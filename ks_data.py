#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaStaffKS (main.py) ile Admin Paneli (admin.py) arasında PAYLAŞILAN veri katmanı.

Fikstür ve kadro bilgisi artık main.py'nin içine gömülü değil; main.py/admin.py ile
AYNI klasördeki "veri.json" dosyasında tutulur:

    - main.py   bu veriyi yalnızca OKUR (uygulama içinde düzenleme ekranı yok).
    - admin.py  hem OKUR hem YAZAR (fikstür, kadro, logo ve fotoğraf yönetimi).

"veri.json" dosyası yoksa (ilk çalıştırma), bu modüldeki DEFAULT_* listeleriyle
otomatik oluşturulur — böylece daha önce main.py içine elle girilmiş fikstür/kadro
hiçbir veri kaybı olmadan buraya taşınmış olur.
"""

import json
import os
import re
import sys
import time as _time
import urllib.request
from datetime import date
from pathlib import Path

APP_FOLDER_NAME = "MediaStaffKS"


def is_frozen() -> bool:
    """PyInstaller ile paketlenmiş (.app) sürümde mi çalışıyoruz?"""
    return bool(getattr(sys, "frozen", False))


def bundle_dir() -> Path:
    """Uygulamayla BİRLİKTE gelen (salt-okunur) dosyalar: logolar, yazı tipleri, paketlenmiş görseller.
    Geliştirme modunda script klasörü; .app'te PyInstaller'ın açtığı kaynak klasörü."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def user_data_dir() -> Path:
    """Kullanıcının kendi dosyaları: veri.json, takım logoları, oyuncu fotoğrafları.
    .app güncellendiğinde silinmesin diye paketin DIŞINDA durur:
    macOS: ~/Library/Application Support/MediaStaffKS (MEDIASTAFF_DATA ile değiştirilebilir).
    Geliştirme modunda (python main.py) eskisi gibi script klasörüdür."""
    override = os.environ.get("MEDIASTAFF_DATA")
    if override:
        return Path(override).expanduser()
    if is_frozen():
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / APP_FOLDER_NAME
        if sys.platform.startswith("win"):
            return Path(os.environ.get("APPDATA", str(Path.home()))) / APP_FOLDER_NAME
        return Path.home() / ".local" / "share" / APP_FOLDER_NAME
    return Path(__file__).resolve().parent


def asset_dirs() -> list:
    """Görsel/yazı tipi aranacak klasörler, öncelik sırasıyla: kullanıcı klasörü, sonra paketin içi."""
    out = []
    for d in (user_data_dir(), bundle_dir()):
        if d not in out:
            out.append(d)
    return out


def find_asset(*names) -> "Path | None":
    """asset_dirs() içinde verilen dosya adlarından ilkini bulur (kullanıcı klasörü önce)."""
    for d in asset_dirs():
        for n in names:
            c = d / n
            if c.is_file():
                return c
    return None


DATA_PATH = user_data_dir() / "veri.json"

KULUP_ADI = "Kocaelispor"
_KOCAELISPOR_STADIUM = "Kocaeli Stadyumu"
DEFAULT_KOCAELISPOR_STADIUM = _KOCAELISPOR_STADIUM

# --- İlk çalıştırmada veri.json'u dolduracak varsayılan değerler -----------------------------
DEFAULT_FIXTURES = [
    {"home": "Beşiktaş", "away": "Kocaelispor", "date": "2026-10-11", "time": "19:00", "stadium": "Tüpraş Stadyumu"},
    {"home": "Kocaelispor", "away": "Göztepe", "date": "2026-10-18", "time": "16:00", "stadium": _KOCAELISPOR_STADIUM},
    {"home": "Alanyaspor", "away": "Kocaelispor", "date": "2026-10-23", "time": "20:00", "stadium": "Bahçeşehir Okulları Stadyumu"},
    {"home": "Kocaelispor", "away": "Rizespor", "date": "2026-10-31", "time": "16:00", "stadium": _KOCAELISPOR_STADIUM},
    {"home": "Eyüpspor", "away": "Kocaelispor", "date": "2026-11-07", "time": "13:30", "stadium": "Pendik Stadyumu"},
    {"home": "Kocaelispor", "away": "Fenerbahçe", "date": "2026-11-21", "time": "19:00", "stadium": _KOCAELISPOR_STADIUM},
    {"home": "Çorum FK", "away": "Kocaelispor", "date": "2026-11-29", "time": "13:30", "stadium": "Çorum Stadyumu"},
    {"home": "Erzurumspor", "away": "Kocaelispor", "date": "2026-12-06", "time": "13:30", "stadium": "Kazım Karabekir Stadyumu"},
    {"home": "Kocaelispor", "away": "Trabzonspor", "date": "2026-12-13", "time": "13:30", "stadium": _KOCAELISPOR_STADIUM},
    {"home": "Gençlerbirliği", "away": "Kocaelispor", "date": "2026-12-21", "time": "20:00", "stadium": "Eryaman Stadyumu"},
]

DEFAULT_PLAYERS = [
    {"name": "Serhat Öztaşdelen", "dob": "2004-12-09", "no": 83, "pos": "Kaleci"},
    {"name": "Aleksandar Jovanović", "dob": "1992-12-06", "no": 1, "pos": "Kaleci"},
    {"name": "Onurcan Piri", "dob": "1994-09-28", "no": 23, "pos": "Kaleci"},
    {"name": "Talha Polat", "dob": "2006-11-17", "no": None, "pos": "Kaleci"},
    {"name": "Tanguy Zoukrou", "dob": "2003-05-07", "no": 4, "pos": "Stoper"},
    {"name": "Matej Maglica", "dob": "1998-09-25", "no": 6, "pos": "Stoper"},
    {"name": "Emir Ortakaya", "dob": "2004-06-22", "no": 5, "pos": "Stoper"},
    {"name": "Onur Öztonga", "dob": "2000-01-06", "no": 41, "pos": "Stoper"},
    {"name": "Massadio Haïdara", "dob": "1992-12-02", "no": 21, "pos": "Sol bek"},
    {"name": "Muharrem Cinan", "dob": "1998-05-13", "no": 3, "pos": "Sol bek"},
    {"name": "Anfernee Dijksteel", "dob": "1996-10-27", "no": 2, "pos": "Sağ bek"},
    {"name": "Uğur Kaan Yıldız", "dob": "2002-08-06", "no": 22, "pos": "Sağ bek"},
    {"name": "Show", "dob": "1999-03-06", "no": 14, "pos": "Ön libero"},
    {"name": "Mahamadou Susoho", "dob": "2005-01-20", "no": 20, "pos": "Ön libero"},
    {"name": "Hulusi Destici", "dob": "2008-08-06", "no": 18, "pos": "Ön libero"},
    {"name": "Berkan Kutlu", "dob": "1998-01-25", "no": 10, "pos": "Merkez orta saha"},
    {"name": "Tayfur Bingöl", "dob": "1993-01-11", "no": 75, "pos": "Merkez orta saha"},
    {"name": "Ege Bilim", "dob": "2006-04-14", "no": 27, "pos": "Merkez orta saha"},
    {"name": "Tobias Gulliksen", "dob": "2003-07-09", "no": 8, "pos": "On numara"},
    {"name": "Rigoberto Rivas", "dob": "1998-07-31", "no": 99, "pos": "Sol kanat"},
    {"name": "Makana Baku", "dob": "1998-04-08", "no": 32, "pos": "Sol kanat"},
    {"name": "Haydar Karataş", "dob": "2007-03-13", "no": 19, "pos": "Sol kanat"},
    {"name": "Gonçalo Sousa", "dob": "2006-06-30", "no": 11, "pos": "Sağ kanat"},
    {"name": "Dan Agyei", "dob": "1997-06-01", "no": 7, "pos": "Sağ kanat"},
    {"name": "Bedirhan Yıldız", "dob": "2005-01-30", "no": 89, "pos": "Sağ kanat"},
    {"name": "Metehan Altunbaş", "dob": "2003-01-07", "no": 26, "pos": "Santrafor"},
    {"name": "Florian Ayé", "dob": "1997-01-19", "no": 97, "pos": "Santrafor"},
    {"name": "Bruno Petkovic", "dob": "1994-09-16", "no": 9, "pos": "Santrafor"},
    {"name": "Arda Özyar", "dob": "2007-04-16", "no": 17, "pos": "Santrafor"},
]


# --- Basın günleri / röportaj takvimi (Kocaelispor beIN Sports röportaj takviminden) --------
DEFAULT_PRESS = [
    {"hafta": "1. Başakşehir", "beinsports": "Metehan Altunbaş - Uğur Yıldız", "antrenman": ""},
    {"hafta": "2. Amed Maç Haftası", "beinsports": "Maglica - Berkan", "antrenman": "Zoukrou ve Emir Ortakaya"},
    {"hafta": "3. Konya Maç Haftası", "beinsports": "Uğur Kaan - Metehan Altunbaş - Massadio Haidara",
     "antrenman": "Emir Ortakaya - Serhat Öztaşdelen"},
    {"hafta": "4. Samsun Maç Haftası", "beinsports": "", "antrenman": "Gulliksen - Ayé"},
    {"hafta": "Beşiktaş haftası", "beinsports": "Emir - Susoho", "antrenman": "Emir"},
    {"hafta": "Göztepe haftası", "beinsports": "", "antrenman": "Susoho"},
]


def _default_data() -> dict:
    return {
        "fixtures": [dict(f) for f in DEFAULT_FIXTURES],
        "players": [dict(p) for p in DEFAULT_PLAYERS],
        "press": [dict(p) for p in DEFAULT_PRESS],
    }


def _parse_date(text):
    try:
        return date.fromisoformat(text) if text else None
    except (TypeError, ValueError):
        return None


def parse_date(text):
    """ISO metni ("YYYY-AA-GG") bir date nesnesine çevirir; okunamazsa None döner.
    admin.py form doğrulaması için kullanılır."""
    return _parse_date(text)


def save_raw(data: dict) -> None:
    """data: {"fixtures": [...], "players": [...], "press": [...]} — tarihler ISO metin ("YYYY-AA-GG")."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    tmp.replace(DATA_PATH)


def load_raw() -> dict:
    """Ham JSON hâliyle (tarihler ISO metin) döndürür — admin.py formlar için bunu kullanır.
    Dosya yoksa varsayılan verilerle oluşturup onu döndürür."""
    if DATA_PATH.is_file():
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # "press" bu özellikten ÖNCE oluşturulmuş eski bir veri.json'da hiç yoktur.
            # O durumda boş liste değil, Excel'den aktarılan varsayılan takvimle doldur ve
            # dosyaya geri yaz — böylece eski bir veri.json'u olan kullanıcı veriyi kaybetmez.
            missing_press = "press" not in data
            data.setdefault("fixtures", [])
            data.setdefault("players", [])
            if missing_press:
                data["press"] = [dict(p) for p in DEFAULT_PRESS]
                save_raw(data)
            return data
        except (OSError, json.JSONDecodeError):
            pass
    data = _default_data()
    save_raw(data)
    return data


def load_data() -> dict:
    """Tarih alanlarını gerçek `date` nesnesine çevirip döndürür — main.py'nin beklediği biçim.
    Geçersiz/okunamayan bir fikstür ya da doğum tarihi varsa o kayıt sessizce atlanır."""
    raw = load_raw()
    fixtures = []
    for f in raw.get("fixtures", []):
        d = _parse_date(f.get("date"))
        if d is None:
            continue
        fixtures.append({
            "home": f.get("home", ""), "away": f.get("away", ""),
            "date": d, "time": f.get("time", ""), "stadium": f.get("stadium", ""),
        })
    players = []
    for p in raw.get("players", []):
        name = (p.get("name") or "").strip()
        if not name:
            continue
        players.append({
            "name": name, "dob": _parse_date(p.get("dob")),
            "no": p.get("no"), "pos": p.get("pos", ""),
        })
    press = []
    for p in raw.get("press", []):
        hafta = (p.get("hafta") or "").strip()
        if not hafta:
            continue
        press.append({
            "hafta": hafta, "beinsports": p.get("beinsports", ""), "antrenman": p.get("antrenman", ""),
        })
    return {"fixtures": fixtures, "players": players, "press": press}


def save_fixtures(fixtures: list) -> None:
    """fixtures: [{"home","away","date" (ISO metin),"time","stadium"}, ...]"""
    raw = load_raw()
    raw["fixtures"] = fixtures
    save_raw(raw)


def save_press(press: list) -> None:
    """press: [{"hafta","beinsports","antrenman"}, ...]"""
    raw = load_raw()
    raw["press"] = press
    save_raw(raw)


def save_players(players: list) -> None:
    """players: [{"name","dob" (ISO metin ya da None),"no","pos"}, ...]"""
    raw = load_raw()
    raw["players"] = players
    save_raw(raw)


# ==========================================================================================
#  TRANSFERMARKT FİKSTÜR OKUYUCU
#  transfermarkt.com.tr/kocaelispor/spielplan/verein/120/saison_id/<yıl> sayfası sunucu tarafında
#  hazır gelir (Süper Lig + Türkiye Kupası satırları). Her satırdan tarih, saat, E/D (ev/deplasman),
#  rakip ve skor okunur. Yalnızca standart kütüphane kullanılır (html.parser DEĞİL — paketlenmiş
#  uygulamada olmayabilir), böylece uygulama içi güncellemeyle yeniden derleme gerekmez.
# ==========================================================================================

CLUB_NAME = KULUP_ADI
TM_CLUB_ID = 120
TM_URL = "https://www.transfermarkt.com.tr/kocaelispor/spielplan/verein/120/saison_id/{season}"
TM_USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                 "Version/17.5 Safari/605.1.15")
TM_BACKUPS_KEPT = 8

_TM_MONTHS = {"oca": 1, "şub": 2, "mar": 3, "nis": 4, "may": 5, "haz": 6,
              "tem": 7, "ağu": 8, "eyl": 9, "eki": 10, "kas": 11, "ara": 12}
_TM_DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\s+([A-Za-zÇĞİÖŞÜçğıöşü]{3})\.?\s+(\d{4})(?!\d)")
_TM_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
_TM_SCORE_RE = re.compile(r"^(\d{1,2}):(\d{1,2})$")
_TM_ROW_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr\s*>", re.S | re.I)
_TM_CELL_RE = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]\s*>", re.S | re.I)
_TM_TAG_RE = re.compile(r"<[^>]+>")
_TM_TITLE_RE = re.compile(r'<a\b[^>]*\btitle="([^"]*)"[^>]*href="/[^"]*/startseite/verein/\d+', re.I)
_ENT = {"nbsp": " ", "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'", "#39": "'"}

# Transfermarkt'taki ad -> uygulamadaki ad (logo dosyası / kısaltma bu adlarla eşleşir)
TM_TEAM_ALIASES = {
    "ç. rizespor": "Rizespor", "çaykur rizespor": "Rizespor", "rizespor": "Rizespor",
    "erzurumspor fk": "Erzurumspor", "erzurum bb": "Erzurumspor",
    "amed sk": "Amedspor", "amed": "Amedspor",
    "istanbul başakşehir fk": "Başakşehir", "i̇stanbul başakşehir fk": "Başakşehir",
    "fenerbahçe sk": "Fenerbahçe", "galatasaray sk": "Galatasaray", "beşiktaş jk": "Beşiktaş",
    "göztepe sk": "Göztepe", "samsunspor": "Samsunspor", "konyaspor": "Konyaspor",
}

# Yalnız kullanıcının kendi girdiği (doğrulanmış) deplasman stadyumları; bilinmeyen BOŞ kalır, tahmin edilmez.
TM_KNOWN_STADIUMS = {
    "Beşiktaş": "Tüpraş Stadyumu", "Alanyaspor": "Bahçeşehir Okulları Stadyumu", "Eyüpspor": "Pendik Stadyumu",
    "Çorum FK": "Çorum Stadyumu", "Erzurumspor": "Kazım Karabekir Stadyumu", "Gençlerbirliği": "Eryaman Stadyumu",
}


def _tm_text(fragment: str) -> str:
    t = _TM_TAG_RE.sub(" ", fragment)
    t = re.sub(r"&(#?\w+);", lambda m: _ENT.get(m.group(1), " "), t)
    return " ".join(t.split())


def tm_team_name(raw: str) -> str:
    name = " ".join((raw or "").split())
    return TM_TEAM_ALIASES.get(name.lower(), name)


def tm_season_for(today: "date | None" = None) -> int:
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


def tm_parse(html: str) -> list:
    """Sayfadaki maç satırlarını okur. Döner: [{"home","away","date" (ISO),"time" ("" = belli değil),
    "played" (bool), "round" (hafta no / tur adı)}]. Maç satırı: tarih + saat + E/D hücreleri olan satır."""
    out = []
    for rm in _TM_ROW_RE.finditer(html or ""):
        cells = [c.group(1) for c in _TM_CELL_RE.finditer(rm.group(1))]
        if len(cells) < 8:
            continue
        texts = [_tm_text(c) for c in cells]
        di = next((i for i, t in enumerate(texts) if _TM_DATE_RE.search(t)), None)
        if di is None or di + 2 >= len(texts):
            continue
        dm = _TM_DATE_RE.search(texts[di])
        month = _TM_MONTHS.get(dm.group(2).lower().replace("i̇", "i")[:3])
        if not month:
            continue
        try:
            d = date(int(dm.group(3)), month, int(dm.group(1)))
        except ValueError:
            continue
        venue = texts[di + 2].upper()
        if venue not in ("E", "D"):
            continue
        tmatch = _TM_TIME_RE.match(texts[di + 1])
        time_txt = f"{int(tmatch.group(1)):02d}:{tmatch.group(2)}" if tmatch else ""
        # rakip: kulüp bağlantısı (title="…") olan ilk hücre
        opp = ""
        for c in cells[di + 3:]:
            tm_ = _TM_TITLE_RE.search(c)
            txt = _tm_text(c)
            if tm_ and txt:
                opp = txt if len(txt) <= len(tm_.group(1)) + 8 else tm_.group(1)
                opp = re.sub(r"\s*\(\d+\.\)\s*$", "", opp).strip()
                break
        if not opp:
            continue
        opp = tm_team_name(opp)
        score = _TM_SCORE_RE.match(texts[-1].replace(" ", ""))
        home, away = (CLUB_NAME, opp) if venue == "E" else (opp, CLUB_NAME)
        out.append({"home": home, "away": away, "date": d.isoformat(), "time": time_txt,
                    "played": bool(score), "round": texts[0]})
    return out


def tm_validate(matches: list, season: int) -> str:
    """Okunan satırlar makul mu? Sorun yoksa "" döner, varsa nedenini metin olarak."""
    league = [m for m in matches if m["round"].isdigit()]
    if len(league) < 30:
        return f"yalnız {len(league)} lig maçı okunabildi (34 bekleniyor)"
    lo, hi = f"{season}-06-01", f"{season + 1}-07-31"
    bad = [m for m in matches if not (lo <= m["date"] <= hi)]
    if bad:
        return f"sezon dışı tarihli maç var ({bad[0]['date']})"
    if len({m["away"] if m["home"] == CLUB_NAME else m["home"] for m in league}) < 17:
        return "rakip sayısı beklenenden az"
    return ""


def tm_fetch(season: int, ssl_context=None, timeout: int = 25) -> str:
    req = urllib.request.Request(TM_URL.format(season=season), headers={
        "User-Agent": TM_USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as resp:
        data = resp.read()
    return data.decode("utf-8", errors="replace")


def backup_data_file(keep: int = TM_BACKUPS_KEPT) -> "Path | None":
    """veri.json'ın zaman damgalı yedeğini alır (en yeni `keep` yedek tutulur)."""
    if not DATA_PATH.is_file():
        return None
    stamp = _time.strftime("%Y%m%d-%H%M%S")
    dest = DATA_PATH.with_name(f"veri.yedek-{stamp}.json")
    try:
        dest.write_bytes(DATA_PATH.read_bytes())
        for old in sorted(DATA_PATH.parent.glob("veri.yedek-*.json"))[:-keep]:
            try:
                old.unlink()
            except OSError:
                pass
        return dest
    except OSError:
        return None


def tm_merge(existing: list, matches: list, today: "date | None" = None):
    """Transfermarkt otoriter kabul edilir: bugün ve sonrasındaki mevcut fikstür kayıtları tamamen
    Transfermarkt'taki gelecek maçlarla DEĞİŞTİRİLİR (önceki hatalı kayıtlar böylece temizlenir).
    Geçmiş kayıtlara dokunulmaz. Stadyum: aynı eşleşmenin eski kaydındaki > Kocaelispor iç saha > bilinen tablo.
    Döner: (yeni_liste, {"added","removed","kept_past"})"""
    today_iso = (today or date.today()).isoformat()
    old_future = {(f.get("home", ""), f.get("away", "")): f for f in existing if f.get("date", "") >= today_iso}
    kept_past = [dict(f) for f in existing if f.get("date", "") < today_iso]
    future = [m for m in matches if m["date"] >= today_iso]
    new_future = []
    for m in future:
        old = old_future.get((m["home"], m["away"])) or {}
        if m["home"] == CLUB_NAME:
            stadium = old.get("stadium") or DEFAULT_KOCAELISPOR_STADIUM
        else:
            stadium = old.get("stadium") or TM_KNOWN_STADIUMS.get(m["home"], "")
        new_future.append({"home": m["home"], "away": m["away"], "date": m["date"],
                           "time": m["time"] or old.get("time", ""), "stadium": stadium})
    merged = sorted(kept_past + new_future, key=lambda f: (f.get("date", ""), f.get("time", "")))
    old_keys = set(old_future)
    new_keys = {(f["home"], f["away"]) for f in new_future}
    return merged, {"added": len(new_keys - old_keys), "removed": len(old_keys - new_keys),
                    "kept_past": len(kept_past), "future": len(new_future)}


def tm_sync(ssl_context=None, today: "date | None" = None, html: "str | None" = None, fetch=None) -> dict:
    """Sayfayı indirir (ya da verilen `html`i kullanır), okur ve doğrular. Dosyaya YAZMAZ.
    Döner: {"matches": [...], "error": "" | neden, "html": ham sayfa (sorun giderme için)}"""
    season = tm_season_for(today)
    try:
        if html is None:
            html = (fetch or (lambda s: tm_fetch(s, ssl_context)))(season)
    except Exception as e:  # noqa: BLE001
        return {"matches": [], "error": str(e) or e.__class__.__name__, "html": "", "season": season}
    matches = tm_parse(html)
    return {"matches": matches, "error": tm_validate(matches, season), "html": html, "season": season}
