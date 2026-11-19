#!/bin/bash
# PyInstaller bazı sürümlerde QtWebEngineProcess yardımcı uygulamasını .app'e koymuyor
# (Qt "could not find it" deyip çöküyor). Eksikse pip'teki PyQt6'dan tamamlar ve yeniden imzalar.
# Kullanım: bash fix_webengine.sh dist/MediaStaffKS.app [python]
set -euo pipefail
APP="$1"; PY="${2:-python3}"
QT_LIB="$("$PY" -c 'import os, PyQt6; print(os.path.join(os.path.dirname(PyQt6.__file__), "Qt6", "lib"))')"
SRC="$QT_LIB/QtWebEngineCore.framework"
DST="$APP/Contents/Frameworks/PyQt6/Qt6/lib/QtWebEngineCore.framework"

if [ ! -d "$SRC" ]; then
  echo "UYARI: $SRC yok (PyQt6-WebEngine kurulu değil); WebEngine düzeltmesi atlandı." >&2
  exit 0
fi
if find "$APP" -name QtWebEngineProcess -type f | grep -q .; then
  echo "QtWebEngineProcess pakette mevcut."
else
  echo "QtWebEngineProcess pakette YOK — eksik dosyalar PyQt6'dan kopyalanıyor"
  mkdir -p "$DST"
  rsync -a --ignore-existing "$SRC/" "$DST/"
  find "$APP" -name QtWebEngineProcess -type f | grep -q . || { echo "HATA: yardımcı uygulama hâlâ yok" >&2; exit 1; }
  # Dosya eklendi: imza geçersiz kaldı, Apple Silicon'da yeniden imzalamak şart
  codesign --force --deep --sign - "$APP"
  echo "Yeniden imzalandı."
fi
