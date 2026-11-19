#!/bin/bash
# PyInstaller macOS'ta QtWebEngineCore.framework'ü bozuk paketliyor: Helpers/Resources dosyaları
# Versions/A yerine Versions/Resources altına düşüyor, Qt de QtWebEngineProcess'i bulamayıp çöküyor.
# Bu betik dosyaları paketin İÇİNDE doğru yere (Versions/A) taşır, yeniden imzalar.
# Kullanım: bash fix_webengine.sh dist/MediaStaffKS.app [python]
set -euo pipefail
APP="$1"; PY="${2:-python3}"
DST="$APP/Contents/Frameworks/PyQt6/Qt6/lib/QtWebEngineCore.framework"
A="$DST/Versions/A"
BAD="$DST/Versions/Resources"
PROBE="$DST/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess"

if [ ! -d "$DST" ]; then
  echo "UYARI: pakette QtWebEngineCore.framework yok; düzeltme atlandı." >&2
  exit 0
fi
if [ -x "$PROBE" ]; then
  echo "QtWebEngineProcess Qt'nin baktığı yolda mevcut."
  exit 0
fi
echo "QtWebEngineProcess Qt'nin baktığı yolda YOK — çerçeve onarılıyor"

mkdir -p "$A/Resources"
if [ -d "$BAD/Helpers" ] && [ ! -e "$A/Helpers" ]; then
  mv "$BAD/Helpers" "$A/Helpers"
fi
if [ -d "$BAD/Resources" ]; then
  cp -R -n "$BAD/Resources/." "$A/Resources/" 2>/dev/null || true
fi
rm -rf "$BAD"

# Hâlâ yoksa (farklı bir düzen): pip'teki PyQt6'dan yardımcıyı bulup kopyala
if [ ! -d "$A/Helpers/QtWebEngineProcess.app" ]; then
  QT_LIB="$("$PY" -c 'import os, PyQt6; print(os.path.join(os.path.dirname(PyQt6.__file__), "Qt6", "lib"))')"
  H="$(find "$QT_LIB/QtWebEngineCore.framework" -name QtWebEngineProcess.app -type d | head -1)"
  [ -n "$H" ] || { echo "HATA: QtWebEngineProcess.app ne pakette ne PyQt6'da bulundu" >&2; exit 1; }
  mkdir -p "$A/Helpers"
  cp -R "$H" "$A/Helpers/"
fi

ln -sfn A "$DST/Versions/Current"
for l in Helpers Resources QtWebEngineCore; do ln -sfn "Versions/Current/$l" "$DST/$l"; done

[ -x "$PROBE" ] || { echo "HATA: onarım sonrası da yardımcı uygulama yok: $PROBE" >&2; exit 1; }
codesign --force --deep --sign - "$APP"                # dosya taşındı → imza yenilenmeli (Apple Silicon şart)
echo "Onarıldı ve yeniden imzalandı."
