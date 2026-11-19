#!/bin/bash
# MediaStaffKS — macOS masaüstü uygulaması (.app) oluşturucu.
#
# Kullanım (terminalde, proje klasöründe — main.py'nin olduğu yerde):
#     bash build_mac.sh
#
# Ne yapar:
#   1. Kulüp logosundan uygulama ikonunu (.icns) üretir.
#   2. MediaStaffKS.app ve MediaStaffKS-Admin.app'i PyInstaller ile derler.
#   3. Mevcut veri.json, takım logoları ve oyuncu fotoğraflarını uygulamanın veri klasörüne
#      (~/Library/Application Support/MediaStaffKS) kopyalar — var olan dosyaların ÜZERİNE YAZMAZ.
#   4. Uygulamaları /Applications'a (yazılamazsa ~/Applications'a) kurar.
#
# Bundan sonra uygulamayı Launchpad/Spotlight'tan ya da Dock'tan açarsın; terminal/VS Code gerekmez.
set -euo pipefail

cd "$(dirname "$0")"
SRC="$(pwd)"
PY="${PYTHON:-python3}"
DATA_DIR="$HOME/Library/Application Support/MediaStaffKS"

say() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mHATA: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = "Darwin" ] || die "Bu betik yalnızca macOS'ta çalışır."
[ -f main.py ] || die "main.py bulunamadı; betiği proje klasöründen çalıştır."
command -v "$PY" >/dev/null || die "python3 bulunamadı."

say "Python: $("$PY" --version) ($("$PY" -c 'import platform;print(platform.machine())'))"

# --- Gerekli paketler -----------------------------------------------------------------------
say "Gerekli paketler kontrol ediliyor"
if ! "$PY" -c "import PyInstaller" 2>/dev/null; then
  "$PY" -m pip install --upgrade pyinstaller pyinstaller-hooks-contrib
fi
if ! "$PY" -c "from PyQt6.QtWebEngineWidgets import QWebEngineView" 2>/dev/null; then
  echo "PyQt6-WebEngine yok — Instagram önizlemesi için kuruluyor"
  "$PY" -m pip install "PyQt6-WebEngine" || echo "UYARI: PyQt6-WebEngine kurulamadı; uygulama Instagram önizlemesiz derlenecek."
fi
"$PY" -c "import PyQt6, cv2, numpy, insightface, onnxruntime, certifi, cryptography" \
  || die "Eksik paket var. Önce: $PY -m pip install -r requirements.txt"

# --- İkon -----------------------------------------------------------------------------------
say "Uygulama ikonu hazırlanıyor"
rm -rf build_icon.iconset icon.icns
mkdir build_icon.iconset
for size in 16 32 128 256 512; do
  sips -z $size $size kocaelispor_logo.png --out "build_icon.iconset/icon_${size}x${size}.png" >/dev/null
  d=$((size * 2))
  sips -z $d $d kocaelispor_logo.png --out "build_icon.iconset/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns build_icon.iconset -o icon.icns
rm -rf build_icon.iconset

# --- Ortak PyInstaller ayarları -------------------------------------------------------------
DATA_ARGS=(--add-data "kocaelispor_logo.png:.")
[ -f ksmedya_logo.png ] && DATA_ARGS+=(--add-data "ksmedya_logo.png:.")
[ -d fonts ] && DATA_ARGS+=(--add-data "fonts:fonts")

say "MediaStaffKS.app derleniyor (birkaç dakika sürebilir)"
"$PY" -m PyInstaller --noconfirm --clean --windowed --onedir \
  --name MediaStaffKS --icon icon.icns \
  --osx-bundle-identifier tr.kocaelispor.mediastaffks \
  "${DATA_ARGS[@]}" \
  --collect-data certifi --hidden-import certifi \
  --collect-all insightface \
  --collect-all onnxruntime \
  --hidden-import PyQt6.QtWebEngineWidgets --hidden-import PyQt6.QtWebEngineCore \
  --exclude-module tkinter \
  main.py

say "MediaStaffKS-Admin.app derleniyor"
"$PY" -m PyInstaller --noconfirm --windowed --onedir \
  --name MediaStaffKS-Admin --icon icon.icns \
  --osx-bundle-identifier tr.kocaelispor.mediastaffks.admin \
  "${DATA_ARGS[@]}" \
  --exclude-module tkinter \
  admin.py

# --- Veri klasörünü doldur (mevcut dosyaların üzerine yazmadan) -----------------------------
say "Veri klasörü hazırlanıyor: $DATA_DIR"
mkdir -p "$DATA_DIR"
[ -f veri.json ] && rsync -a --ignore-existing veri.json "$DATA_DIR/"
shopt -s nullglob nocaseglob
for d in takim_logolari logolar logos oyuncu_fotograflari oyuncularimiz oyuncular oyuncu_resimleri \
         player_photos fotograflar *oyuncu* *player*; do
  [ -d "$d" ] && rsync -a --ignore-existing "$d" "$DATA_DIR/"
done
shopt -u nullglob nocaseglob
mkdir -p "$DATA_DIR/oyuncu_fotograflari" "$DATA_DIR/takim_logolari"

# --- Kur ------------------------------------------------------------------------------------
say "Uygulamalar kuruluyor"
TARGET="/Applications"
[ -w "$TARGET" ] || { TARGET="$HOME/Applications"; mkdir -p "$TARGET"; }
for app in MediaStaffKS MediaStaffKS-Admin; do
  rm -rf "$TARGET/$app.app"
  ditto "dist/$app.app" "$TARGET/$app.app"
  xattr -cr "$TARGET/$app.app" 2>/dev/null || true
done

# Güncelleme paketi (GitHub Releases'e yüklemek istersen)
( cd dist && rm -f MediaStaffKS-mac.zip && ditto -c -k --sequesterRsrc --keepParent MediaStaffKS.app MediaStaffKS-mac.zip )

say "Bitti!"
echo "  Uygulama : $TARGET/MediaStaffKS.app"
echo "  Admin    : $TARGET/MediaStaffKS-Admin.app"
echo "  Veriler  : $DATA_DIR"
echo "İlk açılışta yüz tanıma modeli indirilir (internet gerekir, tek sefer)."
open -R "$TARGET/MediaStaffKS.app"
