# Bundle Desk v1.0.1

首个开源版本：把 Android AAB 转换、签名、设备安装、启动与包信息查看整合到一个本地工作台。

## 新功能

- **AAB → APKS**：支持通用模式与按当前设备生成。
- **签名可选**：上传项目签名库，或自动生成并持续复用默认测试签名；解析 AAB 不需要签名。
- **APK / APKS 导入**：已有包可直接安装；有效签名保留原样，未签名 APK 自动使用默认测试签名。
- **设备操作**：刷新与选择真机/模拟器，安装后启动应用。
- **应用信息**：包名、版本、名称、图标、SDK、权限、组件、原生库及可用原始数据，支持 JSON 导出。
- **本地处理**：内置运行工具，保留执行日志，可保存 APKS、清理会话文件。
- **应用图标**：Mac Finder/Dock 图标与 Windows 快捷方式图标。

## v1.0.1 补充（2026-10-30）

- 补齐 Windows 独立 EXE 应用（`BundleDesk.exe`，内置 .NET 与 Fixed WebView2）以及 HTML 本地版独立下载包。
- Windows EXE 版在独立窗口中使用，HTML 版通过 `启动 HTML 版.cmd` 或原 `Start-BundleDesk.cmd` 在系统浏览器中使用。
- 本次为首版补充，仍使用 v1.0.1，不新增版本；受影响附件的 SHA-256 已更新。

## 修复与改进

- 显示文件导入状态及具体失败原因，操作前重试已选择但未成功导入的文件。
- 页面刷新保留同一服务会话令牌。
- 补全 Mac 原生文件选择器回调。

## 下载

| 平台 | 文件 | 说明 |
| --- | --- | --- |
| macOS 12+ · Apple Silicon | [Bundle-Desk-v1.0.1-macos-arm64.zip](https://github.com/WayneZ01/bundle-desk/releases/download/v1.0.1/Bundle-Desk-v1.0.1-macos-arm64.zip) | 原生窗口，**已验证可用** |
| macOS 12+ · Apple Silicon | [Bundle-Desk-v1.0.1-html-macos-arm64.zip](https://github.com/WayneZ01/bundle-desk/releases/download/v1.0.1/Bundle-Desk-v1.0.1-html-macos-arm64.zip) | 本地浏览器界面，**已验证可用** |
| Windows 10/11 · x64 | [Bundle-Desk-v1.0.1-windows-x64.zip](https://github.com/WayneZ01/bundle-desk/releases/download/v1.0.1/Bundle-Desk-v1.0.1-windows-x64.zip) | EXE 独立窗口，双击 `BundleDesk.exe`；真机安装待反馈 |
| Windows 10/11 · x64 · HTML 本地版 | [Bundle-Desk-v1.0.1-html-windows-x64.zip](https://github.com/WayneZ01/bundle-desk/releases/download/v1.0.1/Bundle-Desk-v1.0.1-html-windows-x64.zip) | 双击 `启动 HTML 版.cmd`，使用系统浏览器 |

完整解压后使用；Mac HTML 版双击 `启动 HTML 版.command`，Windows EXE 版双击 `BundleDesk.exe`，Windows HTML 版双击 `启动 HTML 版.cmd`。运行时均随包提供，无需安装 Android Studio、Java 或 Python；EXE 版额外内置 .NET 与 Fixed WebView2。`SHA256SUMS.txt` 用于核对附件完整性。

Mac 包采用 ad-hoc 签名，未做 Developer ID 公证。当前不提供 Intel Mac、Windows ARM64、安装器、自动更新或模拟器系统镜像。

## 签名与本地数据

默认测试签名按电脑生成，不同电脑默认签名不同。跨电脑更新安装请上传同一份项目签名库。工具不会自动卸载设备上的旧应用。

Mac 数据：`~/Library/Application Support/AAB Workbench`；Windows 数据：`%LOCALAPPDATA%\Bundle Desk`。包文件只在本机处理。请妥善保管本地签名库和密码文件。

## 验证

- macOS Apple Silicon：已验证可用。
- 已通过真实 bundletool 转换、无自定义签名解析/构建、签名保留及 APK 信息解析回归。
- 已通过文件导入状态恢复、Windows 工具路径和 ZIP 完整性检查。
- Windows 已通过 GitHub Actions runner 的构建、内置工具启动、HTTP 文件上传、AAB 解析与默认签名 APKS 转换测试；真机安装待反馈。
