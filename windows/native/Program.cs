using System.Diagnostics;
using System.Text;
using System.Text.Json;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace Wayne.BundleDesk;

internal static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new DeskWindow(args.Contains("--smoke-test")));
    }
}

internal sealed class DeskWindow : Form
{
    readonly WebView2 view = new() { Dock = DockStyle.Fill };
    readonly bool smoke;
    readonly string root = AppContext.BaseDirectory;
    readonly string data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Bundle Desk");
    readonly Label status = new() { Dock = DockStyle.Fill, TextAlign = ContentAlignment.MiddleCenter, Text = "正在启动本地工作台…" };
    Process? service;
    string? origin;
    bool closing;
    public DeskWindow(bool smoke)
    {
        this.smoke = smoke;
        Text = "Bundle Desk";
        ClientSize = new Size(1260, 900);
        MinimumSize = new Size(840, 660);
        StartPosition = FormStartPosition.CenterScreen;
        Icon = System.Drawing.Icon.ExtractAssociatedIcon(Environment.ProcessPath!);
        Controls.Add(status);
        Controls.Add(view);
        view.Visible = false;
        Shown += async (_, _) => await StartAsync();
        FormClosed += (_, _) => StopService();
    }

    async Task StartAsync()
    {
        try
        {
            Directory.CreateDirectory(data);
            string python = Path.Combine(root, "runtime", "windows-x86_64", "python", "python.exe");
            string browser = Path.Combine(root, "runtime", "webview2");
            if (!File.Exists(python) || !File.Exists(Path.Combine(browser, "msedgewebview2.exe")))
                throw new FileNotFoundException("内置运行时不完整，请完整解压 Windows EXE 版 ZIP 后重试。");
            if (root.StartsWith(@"\\")) throw new IOException("请将 EXE 版解压到本机磁盘后启动。");
            // Microsoft requires read/execute rights on the fixed browser binaries for AppContainer renderers on Windows 10.
            // Scope permissions to the shipped browser directory; never grant access to uploaded packages or signing data.
            if (!OperatingSystem.IsWindowsVersionAtLeast(10, 0, 22000))
            {
                foreach (string sid in new[] { "*S-1-15-2-2:(OI)(CI)(RX)", "*S-1-15-2-1:(OI)(CI)(RX)" })
                {
                    var acl = new ProcessStartInfo("icacls.exe") { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
                    acl.ArgumentList.Add(browser); acl.ArgumentList.Add("/grant"); acl.ArgumentList.Add(sid);
                    using var proc = Process.Start(acl)!;
                    var stdout = proc.StandardOutput.ReadToEndAsync(); var stderr = proc.StandardError.ReadToEndAsync();
                    await proc.WaitForExitAsync(); await stdout;
                    if (proc.ExitCode != 0) throw new IOException("无法准备浏览器运行目录权限：" + await stderr);
                }
            }
            var start = new ProcessStartInfo(python) { UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true, WorkingDirectory = root, StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8 };
            start.ArgumentList.Add(Path.Combine(root, "app", "server.py")); start.ArgumentList.Add("--no-browser");
            start.Environment["PYTHONUTF8"] = "1";
            service = Process.Start(start) ?? throw new IOException("无法启动本地服务");
            service.ErrorDataReceived += (_, e) => { if (!string.IsNullOrEmpty(e.Data)) { try { File.AppendAllText(Path.Combine(data, "desktop.log"), e.Data + Environment.NewLine); } catch { } } };
            service.BeginErrorReadLine();
            var line = await service.StandardOutput.ReadLineAsync().WaitAsync(TimeSpan.FromSeconds(60));
            if (!Uri.TryCreate(line, UriKind.Absolute, out var url) || url.Scheme != "http" || url.Host != "127.0.0.1" || string.IsNullOrEmpty(url.Fragment))
                throw new IOException("本地服务未返回有效启动地址。请查看本地数据目录的 desktop.log。");
            origin = url.GetLeftPart(UriPartial.Authority);
            var env = await CoreWebView2Environment.CreateAsync(browser, Path.Combine(data, "WebView2"));
            await view.EnsureCoreWebView2Async(env);
            view.CoreWebView2.Settings.AreDevToolsEnabled = false;
            view.CoreWebView2.Settings.IsStatusBarEnabled = false;
            view.CoreWebView2.NavigationStarting += (_, e) =>
            {
                if (Uri.TryCreate(e.Uri, UriKind.Absolute, out var target) && target.Scheme is "http" or "https" && target.GetLeftPart(UriPartial.Authority) != origin)
                    e.Cancel = true;
            };
            view.CoreWebView2.DownloadStarting += (_, e) =>
            {
                using var deferral = e.GetDeferral();
                using var dialog = new SaveFileDialog { FileName = Path.GetFileName(e.ResultFilePath), OverwritePrompt = true };
                e.Handled = true;
                if (dialog.ShowDialog(this) == DialogResult.OK) e.ResultFilePath = dialog.FileName;
                else e.Cancel = true;
            };
            view.CoreWebView2.ProcessFailed += (_, e) => Fail(new IOException("内置浏览器进程意外退出：" + e.ProcessFailedKind));
            var loaded = new TaskCompletionSource();
            view.CoreWebView2.NavigationCompleted += (_, e) => { if (e.IsSuccess) loaded.TrySetResult(); else loaded.TrySetException(new IOException("界面加载失败：" + e.WebErrorStatus)); };
            view.CoreWebView2.Navigate(url.AbsoluteUri);
            await loaded.Task.WaitAsync(TimeSpan.FromSeconds(45));
            view.Visible = true; status.Visible = false;
            if (smoke)
            {
                // Validate the actual packaged native window, fixed runtime, backend and authenticated page together.
                using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(30));
                while (true)
                {
                    timeout.Token.ThrowIfCancellationRequested();
                    var result = await view.CoreWebView2.ExecuteScriptAsync("document.title.includes('Bundle Desk') && !!document.getElementById('build') && document.querySelectorAll('#environment .ok').length === 4");
                    if (result == "true") break;
                    await Task.Delay(300, timeout.Token);
                }
                File.WriteAllText(Path.Combine(data, "desktop-smoke.json"), JsonSerializer.Serialize(new { success = true, fixedRuntime = env.BrowserVersionString }));
                using (var preview = File.Create(Path.Combine(data, "desktop-smoke.png")))
                    await view.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, preview);
                Environment.ExitCode = 0; Close();
            }
        }
        catch (Exception e) { if (!closing) Fail(e); }
    }
    void Fail(Exception error)
    {
        if (closing) return;
        try { Directory.CreateDirectory(data); File.AppendAllText(Path.Combine(data, "desktop.log"), error + Environment.NewLine); } catch { }
        Environment.ExitCode = 1;
        if (!smoke) MessageBox.Show(this, error.Message, "Bundle Desk 启动失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
        Close();
    }
    void StopService()
    {
        closing = true;
        view.Dispose();
        try { if (service is { HasExited: false }) service.Kill(entireProcessTree: true); } catch { }
        service?.Dispose();
    }
}
