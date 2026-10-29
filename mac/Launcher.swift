import Cocoa
import WebKit

final class Delegate: NSObject, NSApplicationDelegate, WKUIDelegate, WKNavigationDelegate, WKDownloadDelegate {
    var window: NSWindow!
    var process: Process?
    var browser: WKWebView!
    var buffer = ""
    func applicationDidFinishLaunching(_ notification: Notification) {
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1260, height: 900), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "Bundle Desk"
        window.minSize = NSSize(width: 820, height: 650)
        browser = WKWebView(frame: window.contentView!.bounds)
        browser.autoresizingMask = [.width, .height]
        browser.uiDelegate = self
        browser.navigationDelegate = self
        window.contentView!.addSubview(browser)
        window.center(); window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        let task = Process(); process = task
        #if arch(arm64)
        let architecture = "arm64"
        #else
        let architecture = "x86_64"
        #endif
        task.executableURL = Bundle.main.resourceURL!.appendingPathComponent("runtime/" + architecture + "/python/bin/python3")
        task.arguments = [Bundle.main.resourceURL!.appendingPathComponent("app/server.py").path, "--no-browser"]
        var environment = ProcessInfo.processInfo.environment
        environment["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        task.environment = environment
        let pipe = Pipe(); task.standardOutput = pipe
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.buffer += text
                if let line = self.buffer.split(separator: "\n").first, let url = URL(string: String(line)), url.host == "127.0.0.1" {
                    self.browser.load(URLRequest(url: url)); handle.readabilityHandler = nil
                }
            }
        }
        task.terminationHandler = { _ in DispatchQueue.main.async { if NSApp.isRunning { let alert = NSAlert(); alert.messageText = "本地服务已停止"; alert.informativeText = "内置运行时启动失败，请重新解压完整安装包。"; alert.runModal() } } }
        do { try task.run() } catch { let alert = NSAlert(); alert.messageText = "无法启动本地服务"; alert.informativeText = error.localizedDescription; alert.runModal() }
    }
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        decisionHandler(navigationAction.shouldPerformDownload ? .download : .allow)
    }
    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) { download.delegate = self }
    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) { download.delegate = self }
    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String, completionHandler: @escaping (URL?) -> Void) {
        let panel = NSSavePanel(); panel.nameFieldStringValue = suggestedFilename
        panel.begin { result in completionHandler(result == .OK ? panel.url : nil) }
    }
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        panel.beginSheetModal(for: window) { result in
            completionHandler(result == .OK ? panel.urls : nil)
        }
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationWillTerminate(_ notification: Notification) { process?.terminationHandler = nil; process?.terminate() }
}
let app = NSApplication.shared
app.setActivationPolicy(.regular)
let menu = NSMenu(); let menuItem = NSMenuItem(); menu.addItem(menuItem)
let sub = NSMenu(); sub.addItem(withTitle: "退出 Bundle Desk", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"); menuItem.submenu = sub; app.mainMenu = menu
let delegate = Delegate(); app.delegate = delegate; app.run()
