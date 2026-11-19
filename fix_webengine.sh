#!/bin/bash
# PyInstaller macOS'ta QtWebEngineCore.framework'ü bozuk paketliyor: Helpers/Resources dosyaları
# Versions/A yerine Versions/Resources altına düşüyor, Qt de QtWebEngineProcess'i bulamayıp çöküyor.
# Bu betik doğru dosyaları pip'teki PyQt6'dan Versions/A'ya koyar, yanlış klasörü siler, yeniden imzalar.
# Kullanım: bash fix_webengine.sh dist/MediaStaffKS.app [python]
set -euo pipefail
APP="$1"; PY="${2:-python3}"
QT_LIB="$("$PY" -c 'import os, PyQt6; print(os.path.join(os.path.dirname(PyQt6.__file__), "Qt6", "lib"))')"
SRC="$QT_LIB/QtWebEngineCore.framework"
DST="$APP/Contents/Frameworks/PyQt6/Qt6/lib/QtWebEngineCore.framework"
PROBE="$DST/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess"

if [ ! -d "$SRC" ]; then
  echo "UYARI: $SRC yok (PyQt6-WebEngine kurulu değil); WebEngine düzeltmesi atlandı." >&2
  exit 0
fi
if [ -x "$PROBE" ]; then
  echo "QtWebEngineProcess Qt'nin baktığı yolda mevcut."
  exit 0
fi

SRCA="$(cd -P "$SRC/Versions/Current" && pwd)"   # genelde .../Versions/A
[ -d "$SRCA/Helpers" ] || { echo "HATA: $SRCA/Helpers yok" >&2; exit 1; }
echo "QtWebEngineProcess Qt'nin baktığı yolda YOK — çerçeve onarılıyor"

mkdir -p "$DST/Versions/A"
rsync -a --ignore-existing "$SRCA/Helpers/" "$DST/Versions/A/Helpers/"
rsync -a --ignore-existing "$SRCA/Resources/" "$DST/Versions/A/Resources/"
rm -rf "$DST/Versions/Resources"                       # PyInstaller'ın yanlış yerleştirdiği kopya
[ -e "$DST/Versions/A/QtWebEngineCore" ] || rsync -a "$SRCA/QtWebEngineCore" "$DST/Versions/A/"
ln -sfn A "$DST/Versions/Current"
for l in Helpers Resources QtWebEngineCore; do ln -sfn "Versions/Current/$l" "$DST/$l"; done

[ -x "$PROBE" ] || { echo "HATA: onarım sonrası da yardımcı uygulama yok: $PROBE" >&2; exit 1; }
codesign --force --deep --sign - "$APP"                # dosya eklendi → imza yenilenmeli (Apple Silicon şart)
echo "Onarıldı ve yeniden imzalandı."
