#!/bin/bash
# MediaStaffKS — macOS widget'ı ("Paylaşım takibi") oluşturucu.
#
# Kullanım (terminalde, proje klasöründe):   bash build_widget.sh
#
# Gerekli: Xcode Komut Satırı Araçları (yoksa:  xcode-select --install ).  Tam Xcode gerekmez.
# Ne yapar: widget/ShareWidget.swift'i derler, MediaStaffKS-Widget.app paketini oluşturur, imzalar,
# /Applications'a kurar ve bir kez açar. Sonra: masaüstüne sağ tık → Widget'ları Düzenle → MediaStaffKS.
set -euo pipefail

cd "$(dirname "$0")"
say() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mHATA: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = "Darwin" ] || die "Bu betik yalnızca macOS'ta çalışır."
command -v swiftc >/dev/null || die "swiftc bulunamadı. Önce şunu çalıştır:  xcode-select --install"
[ -f widget/ShareWidget.swift ] || die "widget/ShareWidget.swift bulunamadı; betiği proje klasöründen çalıştır."

ARCH="$(uname -m)"
TARGET="${ARCH}-apple-macos14.0"
APP="dist/MediaStaffKS-Widget.app"
APPEX="$APP/Contents/PlugIns/ShareWidget.appex"
BASE_ID="tr.kocaelispor.mediastaffks.widget"

say "Paket klasörleri hazırlanıyor ($TARGET)"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources" "$APPEX/Contents/MacOS" "$APPEX/Contents/Resources"
[ -f icon.icns ] && cp icon.icns "$APP/Contents/Resources/icon.icns"

say "Widget derleniyor"
swiftc -O -parse-as-library -application-extension -target "$TARGET" \
  widget/ShareWidget.swift -o "$APPEX/Contents/MacOS/ShareWidget" \
  -Xlinker -e -Xlinker _NSExtensionMain

say "Ana uygulama derleniyor"
swiftc -O -target "$TARGET" widget/HostApp.swift -o "$APP/Contents/MacOS/MediaStaffKSWidget"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>MediaStaffKSWidget</string>
  <key>CFBundleIdentifier</key><string>${BASE_ID}</string>
  <key>CFBundleName</key><string>MediaStaffKS Widget</string>
  <key>CFBundleDisplayName</key><string>MediaStaffKS Widget</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST

cat > "$APPEX/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>ShareWidget</string>
  <key>CFBundleIdentifier</key><string>${BASE_ID}.sharewidget</string>
  <key>CFBundleName</key><string>Paylaşım takibi</string>
  <key>CFBundleDisplayName</key><string>Paylaşım takibi</string>
  <key>CFBundlePackageType</key><string>XPC!</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSExtension</key><dict>
    <key>NSExtensionPointIdentifier</key><string>com.apple.widgetkit-extension</string>
  </dict>
</dict></plist>
PLIST

# Widget korumalı alanda çalışır; MediaStaffKS'ın veri klasörünü yalnızca OKUYABİLMESİ için istisna verilir.
ENT="$(mktemp -t widget-ent).plist"
cat > "$ENT" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>com.apple.security.app-sandbox</key><true/>
  <key>com.apple.security.temporary-exception.files.home-relative-path.read-only</key>
  <array><string>/Library/Application Support/MediaStaffKS/</string></array>
</dict></plist>
PLIST

say "İmzalanıyor (yerel imza)"
codesign --force --sign - --entitlements "$ENT" "$APPEX"
codesign --force --sign - "$APP"
rm -f "$ENT"

say "Kuruluyor"
TARGET_DIR="/Applications"
[ -w "$TARGET_DIR" ] || { TARGET_DIR="$HOME/Applications"; mkdir -p "$TARGET_DIR"; }
rm -rf "$TARGET_DIR/MediaStaffKS-Widget.app"
ditto "$APP" "$TARGET_DIR/MediaStaffKS-Widget.app"
xattr -cr "$TARGET_DIR/MediaStaffKS-Widget.app" 2>/dev/null || true
pluginkit -a "$TARGET_DIR/MediaStaffKS-Widget.app/Contents/PlugIns/ShareWidget.appex" 2>/dev/null || true
killall chronod 2>/dev/null || true

say "Kayıt denetimi"
if pluginkit -m -p com.apple.widgetkit-extension 2>/dev/null | grep -qi mediastaffks; then
  echo "Widget macOS'a kaydedildi."
else
  echo "UYARI: widget henüz kayıtlı görünmüyor. Uygulamayı bir kez açınca kaydolabilir; olmazsa bu çıktıyı bana gönder."
fi

say "Bitti!"
echo "  Uygulama: $TARGET_DIR/MediaStaffKS-Widget.app (şimdi açılacak, bir uyarı çıkacak → Tamam)"
echo "  Sonra: masaüstüne sağ tık → Widget'ları Düzenle → 'MediaStaffKS' → 'Paylaşım takibi'."
open "$TARGET_DIR/MediaStaffKS-Widget.app"
