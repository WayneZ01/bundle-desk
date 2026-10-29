# 更新日志

## v1.0.1 — 2026-10-29

首次开源发布。

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
- Windows x64：已完成打包与静态校验，提供 Windows CI smoke test；等待实机反馈。
- Intel Mac / Windows ARM64：未提供发行包。
