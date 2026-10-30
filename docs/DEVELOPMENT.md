# 开发与构建

## 项目结构

```
app/                  Python 标准库服务、HTML/CSS/JS 界面与 Java 工具
mac/                  Swift WKWebView 启动器、应用图标
windows/              Windows 启动与快捷方式脚本
scripts/              macOS / Windows 运行时准备与打包脚本
tests/                最小 AAB 示例、回归与 Windows smoke test
docs/                 文档与真实界面截图
.github/workflows/    Windows 构建及实机运行测试配置
```

运行时与产物在 `runtime/`、`dist/`，不纳入 Git；不要把它们当作已经随源码下载的文件。发行包则包含运行所需工具。

## 直接运行源码

需要 Python 3.9+、Java 11+、bundletool、ADB，信息解析额外需要 aapt。仓库包含 bundletool 和 apksigner JAR；这些是第三方组件，遵循各自许可。

```sh
python3 app/server.py
```

默认启动随机本地端口并打开浏览器。可使用 `--no-browser`、`--port 端口号`。`--port` 不改变仅监听 127.0.0.1 的行为。

可覆盖 `JAVA_BIN`、`ADB_BIN`、`AAPT_BIN`、`BUNDLETOOL_JAR`、`ANDROID_HOME` 和 `AAB_WORKBENCH_DATA`。Java 优先选择内置运行时；ADB/aapt 的显式环境变量可覆盖自动发现。

## macOS 发行包

打包机需要 Xcode Command Line Tools 和 Python 3.12+，使用者不需要这些开发工具。

```sh
python3.12 scripts/prepare-runtime.py
scripts/build-mac.sh
```

默认构建校验两种架构的运行时。如果仅准备 Apple Silicon，可执行：

```sh
ARCHS=arm64 scripts/build-mac.sh
```

运行时布局：

```
runtime/
  arm64/python/       arm64/jre/Contents/Home/
  x86_64/python/      x86_64/jre/Contents/Home/
  tools/adb           tools/aapt      tools/lib64/
```

脚本从官方来源准备 Python、Java 和 Android 工具，并保留第三方 NOTICE。当前首次发布的 ARM64 包使用 Python 3.12.14 / Corretto 11.0.21；运行时重新准备脚本使用其源码中固定的 Python 版本及 Temurin Java 17。具体版本可能随重新打包而不同，需在 Release 中记录。

`build-mac.sh` 生成 `dist/Bundle Desk.app`，内含图标并使用 ad-hoc 签名。正式公证签名需要维护者自己的 Apple Developer ID。不要提交开发者证书或签名凭据。

HTML 版应同时复制 `app/`、对应 `runtime/` 和根目录的启动 `.command`，再压缩完整目录。应用与 HTML 版必须使用同一份源码版本。

## Windows 发行包

可在 macOS、Linux 或 Windows 的打包机执行，需 Python 3.9+ 和 curl；打包阶段需要网络，使用者运行无需联网下载工具。

```sh
python3 scripts/build-windows.py
```

产物：`dist/Bundle Desk Windows x64.zip` 和 `dist/Bundle Desk HTML Windows x64.zip`，包含 Python embeddable、Java 17 JRE、ADB、aapt、相关 DLL、界面及 Java 工具。来源和 SHA-256 位于包内 `runtime-sources.json`。

当前 Windows 运行时布局为 `runtime/windows-x86_64/{python,jre,tools}`。Windows HTML 本地版提供 `启动 HTML 版.cmd`，调用同目录的 `Start-BundleDesk.cmd`；两个 ZIP 共用同一套代码和依赖。启动器使用相对目录，不依赖打包机路径。

## 验证

```sh
node --check app/web/app.js
node tests/upload-state.cjs
python3 tests/test_windows_paths.py
python3 tests/integration.py
```

`integration.py` 使用真实 bundletool 构造并转换最小 AAB，覆盖自定义签名、无签名解析、默认签名、未签名 APK 签名、有效签名保留及信息解析。该测试的构造阶段依赖开发机 Android SDK build-tools 34.0.0 与 android-34（macOS 默认 SDK 路径）。

Windows 真实运行测试在 Windows 机器执行：

```powershell
python tests/windows-smoke.py 'dist/Bundle Desk Windows x64'
```

`.github/workflows/windows.yml` 负责 Windows runner 构建、HTTP 上传与真实 Java/ADB/aapt 转换 smoke test。这个测试不连接真机，不等同于完整设备安装验证。

## 发布

1. 更新版本、CHANGELOG 与平台验证状态。
2. 运行回归测试，确认发行包无真实签名库或密码、无打包机私有配置。
3. 构建并完整解压校验各平台 ZIP，Mac 校验代码签名，Windows 在 Windows runner 运行 smoke test。
4. 在 `main` 的对应提交创建版本标签，通过 GitHub Releases 上传安装包、源代码归档和 `SHA256SUMS.txt`。
5. 发布说明只列出真实功能与实际验证情况，不把未提供的平台列为可下载。

### Windows EXE 应用

在 Windows 打包机（或本仓库 Windows Actions runner）运行：

```powershell
python scripts/build-windows-native.py
```

打包机需 .NET 8 SDK；使用者不需要安装 .NET。脚本使用 self-contained 发布 Windows Forms + WebView2 原生窗口，下载微软官方 Fixed Version WebView2 CAB 并随包附带。产物为 `dist/Bundle Desk EXE Windows x64.zip`，通过 `BundleDesk.exe` 启动，和 HTML 版共享本地服务、数据目录及默认测试签名。Fixed WebView2 需要随应用升级，不自动更新。Windows 10 按微软要求，仅给随包浏览器二进制目录授予 AppContainer 读取/执行权限；不修改签名或上传数据目录权限。

CI 额外启动实际打包的 `BundleDesk.exe --smoke-test`，验证固定浏览器运行时、服务地址、页面和四项内置工具就绪，关闭后清理子进程。此检查不替代真实手机安装验证。
