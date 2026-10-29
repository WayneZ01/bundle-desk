Bundle Desk for Windows 10/11 x64
================================
1. Extract the COMPLETE ZIP into a normal folder (do not run inside ZIP preview).
2. Double-click Start-BundleDesk.cmd. Your default browser opens the local tool.
3. Keep the command window open. Close it or press Ctrl+C when finished.

Python, Java, bundletool, apksigner, ADB, aapt and required tool DLLs are included.
No Python / Java / Android Studio / SDK installation or PATH configuration needed.
All package files and signing data are processed locally; no cloud upload.

AAB: inspect without signing; convert with an optional keystore, otherwise a
persistent local test key is generated automatically.
APK / APKS: import, inspect and install. Valid signatures are preserved.
Unsigned APKs receive the local test signature before installation.
A broken existing signature is reported instead of silently replaced.

Default application data: %LOCALAPPDATA%\Bundle Desk
Default signing key: default-signing\test.jks under the above directory.
The "clear session" button preserves the default key. Each computer has a
separate default key. Use the same supplied keystore for cross-PC updates.

A real phone needs USB debugging and authorization. Some phone vendors require
their Windows USB driver. Android emulator software / OS images are not bundled.
Unauthorized or offline devices must be authorized or reconnected first.

This is a portable browser UI edition, not a native Windows window or installer.
The service listens only on 127.0.0.1 with a per-session access token.
Windows ARM64 and 32-bit Windows are not validated/supported by this x64 package.

Runtime sources and archive SHA-256 values: runtime-sources.json.
Vendor license / NOTICE files are preserved with the runtimes.
Built on macOS: Windows process startup, browser launch and device installation
still require verification on a real Windows PC.
