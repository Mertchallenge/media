"""MediaStaffKS — paketlenmiş (.app) uygulamanın giriş noktası.

PyInstaller bu dosyayı başlatıcı olarak paketler; main.py ve ks_data.py paketin içinde yer alır.
Uygulama içi güncelleme yeni main.py/ks_data.py'yi veri klasöründeki "kod" klasörüne indirir
(~/Library/Application Support/MediaStaffKS/kod). Burada, o kod paketlenmiş sürümden DAHA YENİYSE
ve paketle uyumluysa onu yükleriz — böylece .app'i yeniden derlemeden güncelleme çalışır.
Bir sorun çıkarsa (içe aktarma hatası vb.) sessizce paketin kendi sürümüne düşeriz.

BUNDLE_API: Paketin içerdiği kütüphaneler/launcher değişirse artır (main.py'deki REQUIRES_BUNDLE ile karşılaştırılır).
"""
import importlib.util
import os
import re
import sys
import traceback
from pathlib import Path

BUNDLE_API = 1
os.environ["MEDIASTAFF_BUNDLE_API"] = str(BUNDLE_API)


def _vt(v):
    out = []
    for p in str(v).strip().lstrip("vV").split("."):
        d = "".join(ch for ch in p if ch.isdigit())
        out.append(int(d) if d else 0)
    return tuple(out)


def _meta(text):
    ver = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.M)
    req = re.search(r'^REQUIRES_BUNDLE\s*=\s*(\d+)', text, re.M)
    return (ver.group(1) if ver else ""), (int(req.group(1)) if req else 1)


def _bundled_version():
    try:
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        return (base / "bundle_version.txt").read_text(encoding="utf-8").strip()
    except Exception:
        return "0"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _log(user_dir, text):
    try:
        user_dir.mkdir(parents=True, exist_ok=True)
        with open(user_dir / "launcher.log", "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except Exception:
        pass


def _entry():
    import ks_data as bundled_ks_data            # paketteki (yalnızca veri klasörünü bulmak için)
    user_dir = bundled_ks_data.user_data_dir()
    overlay = user_dir / "kod"
    ov_main, ov_ks = overlay / "main.py", overlay / "ks_data.py"

    if ov_main.is_file() and ov_ks.is_file() and "--no-overlay" not in sys.argv:
        try:
            ver, req = _meta(ov_main.read_text(encoding="utf-8"))
            if ver and _vt(ver) > _vt(_bundled_version()) and req <= BUNDLE_API:
                sys.modules.pop("ks_data", None)
                sys.modules.pop("main", None)
                _load("ks_data", ov_ks)
                mod = _load("main", ov_main)
                _log(user_dir, f"güncel kod yüklendi: {ver}")
                return mod.main
            _log(user_dir, f"güncel kod kullanılmadı (kod={ver}, paket={_bundled_version()}, gereken paket={req})")
        except Exception:
            _log(user_dir, "güncel kod yüklenemedi, paketin kendi sürümüne dönülüyor:\n" + traceback.format_exc())
        sys.modules.pop("ks_data", None)
        sys.modules.pop("main", None)

    import ks_data  # noqa: F401  (paketteki)
    import main
    return main.main


if __name__ == "__main__":
    _entry()()
