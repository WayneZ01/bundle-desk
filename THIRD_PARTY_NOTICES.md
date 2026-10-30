# 第三方组件

Bundle Desk 自有源码为 MIT；本文件列出的第三方组件保留原许可证。源码仓库与二进制发行包的组件范围不同。

| 组件 | 用途 / 版本 | 来源及许可 |
| --- | --- | --- |
| bundletool | AAB/APKS 转换与安装 · 1.18.3 | [Google bundletool](https://github.com/google/bundletool)，Apache 2.0；JAR 内包含传递依赖许可，提取副本见 docs/legal |
| apksigner | APK 签名校验与签名 · SDK build-tools 34.0.0 | [Android apksig](https://android.googlesource.com/platform/tools/apksig/)，Apache 2.0，Android 工具 NOTICE 见 docs/legal |
| Android SDK aapt / ADB | 包解析与设备通信 | [Android SDK Tools](https://developer.android.com/tools)，对应 NOTICE 随运行时保留，SDK 下载和分发受相应许可约束 |
| Python | 本地服务；Mac 3.12.14 / Windows embeddable 3.12.10 | [Python](https://www.python.org/)、[python-build-standalone](https://github.com/astral-sh/python-build-standalone)，保留各发行版 LICENSE |
| Amazon Corretto | 首次 macOS ARM64 包的 Java 11.0.21 | [Amazon Corretto](https://aws.amazon.com/corretto/)，OpenJDK GPLv2 with Classpath Exception，保留 legal 目录 |
| Azul Zulu | Windows 包的 Java 17.0.21 | [Azul Zulu](https://www.azul.com/downloads/)，OpenJDK GPLv2 with Classpath Exception，保留 legal 目录 |
| Eclipse Temurin | macOS 重新准备脚本的 Java 17 来源 | [Adoptium](https://adoptium.net/)，OpenJDK GPLv2 with Classpath Exception，保留 legal 目录 |

运行时不提交到 Git。首次 Release 的运行时来源及实际版本与构建脚本后续下载版本可能不同，请以具体 Release 说明、发行包内 LICENSE/NOTICE 及 runtime-sources.json 为准。

应用图标和界面由本项目生成，按自有源码许可证提供。README 徽章由 shields.io 提供，显示仓库的实际发布状态。

Windows EXE 版额外使用 Microsoft .NET 8（MIT，保留发行许可）与 Microsoft.Web.WebView2 SDK / Fixed Version Runtime（微软分发许可，保留包内许可及第三方声明）。官方说明：[WebView2 分发](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)。HTML 版不附带此浏览器运行时。
