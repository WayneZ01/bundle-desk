# 更新日志

## v1.0.1 — 2026-10-30

首次开源发布。

### 首版补充

- 补齐 Windows EXE 应用版（独立窗口、内置 .NET 与 Fixed WebView2）与 HTML 本地版（`启动 HTML 版.cmd`），同步补齐使用说明。
- Windows HTML 保留原通用启动入口；两版共用转换核心，提供不同窗口形式，仍作为 v1.0.1 发布。

### 功能

- AAB 转签名 APKS，支持通用模式与按设备生成。
- 自定义签名库及持久化默认测试签名。
- 导入 APK/APKS、设备选择、安装、应用启动。
- 应用信息解析、原始清单与日志展示、APKS 保存及 JSON 导出。
- macOS 原生窗口、macOS HTML 本地版、Windows x64 浏览器便携版。
- 应用图标及 Windows 桌面快捷方式创建脚本。

### 修复

- 导入失败后明确展示原因，操作前重试已选择但尚未成功导入的文件。
- 页面刷新恢复同一服务会话的令牌。
- Mac 原生文件选择器显式回调。

### 平台状态

- macOS Apple Silicon：已验证可用。
- Windows x64：已通过 GitHub Actions Windows runner 的构建、真实工具转换及 EXE 独立窗口/Fixed WebView2 启动测试；真机安装等待反馈。
- Intel Mac / Windows ARM64：未提供发行包。
