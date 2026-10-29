#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
for ARCH in ${ARCHS:-arm64 x86_64}; do
  test -x "runtime/$ARCH/python/bin/python3" || { echo "缺少 $ARCH Python 运行时，禁止生成不完整发行包"; exit 1; }
  test -x "runtime/$ARCH/jre/Contents/Home/bin/java" || { echo "缺少 $ARCH Java 运行时，禁止生成不完整发行包"; exit 1; }
done
APP="$PWD/dist/Bundle Desk.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/app"
swiftc -target arm64-apple-macosx12.0 mac/Launcher.swift -o "$APP/Contents/MacOS/BundleDesk" -framework Cocoa -framework WebKit
swiftc -target x86_64-apple-macosx12.0 mac/Launcher.swift -o /tmp/bundledesk-intel -framework Cocoa -framework WebKit
lipo -create "$APP/Contents/MacOS/BundleDesk" /tmp/bundledesk-intel -output "$APP/Contents/MacOS/BundleDesk"
cp -R runtime "$APP/Contents/Resources/"
cp app/server.py app/bundletool.jar app/apksigner.jar "$APP/Contents/Resources/app/"
swift scripts/make-icon.swift
iconutil -c icns mac/assets/BundleDesk.iconset -o mac/assets/BundleDesk.icns
cp mac/assets/BundleDesk.icns "$APP/Contents/Resources/"
cp -R app/web "$APP/Contents/Resources/app/"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>CFBundleExecutable</key><string>BundleDesk</string><key>CFBundleIdentifier</key><string>local.bundledesk.app</string><key>CFBundleIconFile</key><string>BundleDesk</string><key>CFBundleName</key><string>Bundle Desk</string><key>CFBundleVersion</key><string>2</string><key>CFBundleShortVersionString</key><string>1.0.1</string><key>LSMinimumSystemVersion</key><string>12.0</string><key>NSHighResolutionCapable</key><true/><key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict></dict></plist>
PLIST
codesign --force --deep --sign - "$APP"
printf '已生成：%s\n' "$APP"
