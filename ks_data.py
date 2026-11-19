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

# Haftalık antrenman programı (kulübün gönderdiği görselden). kind: meal | gym | training | match | meeting | camp | off
def _prog_week() -> dict:
    items = []

    def add(day, time, title, kind):
        items.append({"date": f"2026-11-{day:02d}", "time": time, "title": title, "kind": kind})

    for day in (15, 18, 24):                                       # öğleden sonra düzeni
        add(day, "14:00", "Ara öğün", "meal"); add(day, "15:45", "Fitness / Gym", "gym")
        add(day, "16:00", "Antrenman", "training"); add(day, "18:00", "Akşam yemeği", "meal")
    for day in (16, 17, 19, 22):                                   # sabah düzeni
        add(day, "10:00", "Kahvaltı (zorunlu)", "meal"); add(day, "11:45", "Fitness / Gym", "gym")
        add(day, "12:00", "Antrenman", "training"); add(day, "14:00", "Öğle yemeği (zorunlu)", "meal")
    add(20, "15:00", "Ara öğün", "meal"); add(20, "15:00", "Kamp başlar", "camp")
    add(20, "17:00", "Antrenman", "training"); add(20, "19:00", "Akşam yemeği", "meal"); add(20, "22:00", "Ara öğün", "meal")
    add(21, "11:00", "Kahvaltı (zorunlu)", "meal"); add(21, "15:30", "Maç yemeği", "meal")
    add(21, "16:45", "Toplantı ve hareket", "meeting"); add(21, "19:00", "Kocaelispor - Fenerbahçe", "match")
    add(23, "", "İzin", "off")
    items.sort(key=lambda i: (i["date"], i["time"] or "99:99"))
    return {"id": "2026-11-15", "title": "Antrenman Programı", "subtitle": "12- Fenerbahçe", "coach": "Selçuk İnan",
            "start": "2026-11-15", "end": "2026-11-24", "items": items}


DEFAULT_PROGRAMS = [_prog_week()]


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
        "programs": [dict(p) for p in DEFAULT_PROGRAMS],
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
            # Yeni sürümle gelen haftalık programlar (id'si henüz olmayanlar) kullanıcının verisine eklenir
            progs = data.setdefault("programs", [])
            have = {p.get("id") for p in progs if isinstance(p, dict)}
            new_progs = [json.loads(json.dumps(p)) for p in DEFAULT_PROGRAMS if p["id"] not in have]
            progs.extend(new_progs)
            if missing_press or new_progs:
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
    programs = []
    for pr in raw.get("programs", []):
        if not isinstance(pr, dict) or _parse_date(pr.get("start")) is None:
            continue
        items = [it for it in pr.get("items", []) if isinstance(it, dict) and _parse_date(it.get("date")) is not None]
        end = pr.get("end") if _parse_date(pr.get("end")) is not None else pr["start"]
        programs.append({**pr, "end": end, "items": items})
    programs.sort(key=lambda pr: pr["start"])
    return {"fixtures": fixtures, "players": players, "press": press, "programs": programs}


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


# ==========================================================================================
#  HAFTALIK PROGRAM -> TAKVİM (.ics)  (Mac Takvim / widget'ı ve bildirimleri için)
# ==========================================================================================
import hashlib
from datetime import datetime, timedelta

PROGRAM_KIND_MINUTES = {"meal": 60, "gym": 15, "training": 90, "match": 120, "meeting": 30, "camp": 30}
PROGRAM_ALARM_KINDS = {"training", "match", "meeting", "camp"}   # 15 dk önce hatırlat


def _ics_escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _ics_fold(line: str) -> str:
    raw = line.encode("utf-8")
    if len(raw) <= 74:
        return line
    out, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > (74 if not out else 73):
            out.append(cur.decode("utf-8"))
            cur = b
        else:
            cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def programs_to_ics(programs: list, today: "date | None" = None) -> str:
    """Bugünden itibaren olan program satırlarını iCalendar metnine çevirir (satır yoksa boş metin).
    UID sabit olduğundan aynı dosya yeniden içe aktarılınca etkinlikler çoğalmaz, güncellenir."""
    today_iso = (today or date.today()).isoformat()
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    events = []
    for pr in programs:
        for it in pr.get("items", []):
            if it.get("date", "") < today_iso:
                continue
            d = date.fromisoformat(it["date"])
            title = it.get("title", "")
            uid = hashlib.sha1(f"{it['date']}|{it.get('time','')}|{title}".encode("utf-8")).hexdigest()[:20] + "@mediastaffks"
            ev = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}"]
            tm = it.get("time") or ""
            if tm and re.match(r"^\d{2}:\d{2}$", tm):
                start = datetime.combine(d, datetime.strptime(tm, "%H:%M").time())
                end = start + timedelta(minutes=PROGRAM_KIND_MINUTES.get(it.get("kind", ""), 60))
                ev += [f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}", f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}"]
            else:                                   # saatsiz (ör. İzin): tüm gün
                ev += [f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(d + timedelta(days=1)).strftime('%Y%m%d')}"]
            ev.append("SUMMARY:" + _ics_escape(title))
            sub = " · ".join(x for x in (pr.get("title", ""), pr.get("subtitle", "")) if x)
            if sub:
                ev.append("DESCRIPTION:" + _ics_escape(sub))
            if it.get("kind") in PROGRAM_ALARM_KINDS and tm:
                ev += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + _ics_escape(title), "TRIGGER:-PT15M", "END:VALARM"]
            ev.append("END:VEVENT")
            events.append(ev)
    if not events:
        return ""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MediaStaffKS//Program//TR", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", "X-WR-CALNAME:Kocaelispor Program"]
    for ev in events:
        lines += ev
    lines.append("END:VCALENDAR")
    return "\r\n".join(_ics_fold(l) for l in lines) + "\r\n"


# ---------------------------------------------------------------------------
# iPhone widget'ları (Scriptable) — iCloud Drive üzerinden eşitleme
# ---------------------------------------------------------------------------
IOS_SCRIPT_NAME = "MediaStaffKS.js"
IOS_DATA_DIRNAME = "MediaStaffKS-data"
SCRIPTABLE_JS = r'''// MediaStaffKS — iPhone widget'ları (Scriptable uygulaması için).
// Widget'a uzun bas → Widget'ı Düzenle → Script: MediaStaffKS → Parameter:
//   program | week | share | match | birthdays     (boşsa: program)
// Veriler Mac'teki MediaStaffKS uygulamasından iCloud ile gelir.

const DATA_DIR = "MediaStaffKS-data";
const BG1 = "#0E1A14", BG2 = "#0A0E0C";
const GREEN = "#00A86B", GREEN_HI = "#2FD69A", TEXT = "#E9F2ED", SOFT = "#C9D6CE", MUTED = "#8CA095", AMBER = "#F2B24A";
const KIND = {
  training: ["#FF7B7F", "#2E1719"], gym: [GREEN_HI, "#12291F"], match: ["#7FB2FF", "#152238"],
  meeting: [AMBER, "#2A2113"], camp: [AMBER, "#2A2113"], off: [GREEN_HI, "#0E2A1F"], meal: [SOFT, "#1B2420"],
};
const DAYS3 = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];
const MONTHS3 = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];

const fm = FileManager.iCloud();
async function load(name) {
  try {
    const path = fm.joinPath(fm.joinPath(fm.documentsDirectory(), DATA_DIR), name);
    if (!fm.fileExists(path)) return null;
    await fm.downloadFileFromiCloud(path);
    return JSON.parse(fm.readString(path));
  } catch (e) { return null; }
}

const pad = n => String(n).padStart(2, "0");
const isoOf = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const parseIso = s => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
const hhmm = d => `${pad(d.getHours())}:${pad(d.getMinutes())}`;
const daysUntil = (target, now) => Math.round((parseIso(isoOf(target)) - parseIso(isoOf(now))) / 86400000);
const countdown = n => (n <= 0 ? "Bugün" : n === 1 ? "Yarın" : `${n} gün`);
const kindStyle = k => KIND[k] || KIND.meal;
const img = b64 => (b64 ? Image.fromData(Data.fromBase64String(b64)) : null);

function newWidget(family) {
  const w = new ListWidget();
  const g = new LinearGradient();
  g.colors = [new Color(BG1), new Color(BG2)];
  g.locations = [0, 1];
  w.backgroundGradient = g;
  w.setPadding(family === "small" ? 12 : 14, 14, 12, 14);
  w.refreshAfterDate = new Date(Date.now() + 15 * 60 * 1000);
  return w;
}

function text(parent, str, size, color, weight, lines) {
  const t = parent.addText(str);
  t.font = weight === "bold" ? Font.boldSystemFont(size) : weight === "semi" ? Font.semiboldSystemFont(size) : Font.systemFont(size);
  t.textColor = new Color(color);
  if (lines) t.lineLimit = lines;
  return t;
}

function title(parent, str, right) {
  const s = parent.addStack();
  s.layoutHorizontally();
  s.centerAlignContent();
  text(s, str, 10, GREEN_HI, "bold");
  if (right) { s.addSpacer(); text(s, right, 11, TEXT, "semi", 1); }
  return s;
}

function message(w, head, msg) {
  title(w, head);
  w.addSpacer();
  text(w, msg, 12, MUTED);
  w.addSpacer();
}

function avatar(parent, b64, fallback, size) {
  const im = img(b64);
  if (im) {
    const wi = parent.addImage(im);
    wi.imageSize = new Size(size, size);
    wi.cornerRadius = size / 2;
    return wi;
  }
  const s = parent.addStack();
  s.size = new Size(size, size);
  s.cornerRadius = size / 2;
  s.backgroundColor = new Color(GREEN, 0.35);
  s.centerAlignContent();
  s.addSpacer();
  text(s, (fallback || "?").slice(0, 1), size * 0.45, TEXT, "bold");
  s.addSpacer();
  return s;
}

// ---------------------------------------------------------------- Bugünün programı
// Günün son saatli etkinliğinden 30 dk sonra yarının programı gösterilir.
function viewDay(x, now) {
  const days = x.program || [];
  const today = days.find(d => d.date === isoOf(now));
  if (today) {
    const stamps = today.items.filter(i => i.time).map(i => {
      const [h, m] = i.time.split(":").map(Number);
      return new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m);
    }).filter(d => !isNaN(d));
    if (stamps.length && now >= new Date(Math.max(...stamps) + 30 * 60 * 1000)) {
      const tm = days.find(d => d.date === isoOf(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1)));
      if (tm && tm.items.length) return { day: tm, tomorrow: true };
    }
  }
  return { day: today, tomorrow: false };
}

function programWidget(x, family) {
  const w = newWidget(family);
  const now = new Date();
  const { day, tomorrow } = viewDay(x, now);
  const head = tomorrow ? "YARININ PROGRAMI" : "BUGÜNÜN PROGRAMI";
  if (!day || !day.items.length) { message(w, head, "Bugün için program yok."); return w; }
  const items = day.items, nowStr = tomorrow ? "00:00" : hhmm(now);
  const nextIdx = items.findIndex(i => i.time && i.time >= nowStr);
  const done = i => items[i].time && items[i].time < nowStr;

  if (family === "small") {
    title(w, tomorrow ? "YARIN" : (nextIdx < 0 ? "BUGÜN" : "SIRADAKİ"));
    const i = nextIdx >= 0 ? nextIdx : items.length - 1;
    const st = kindStyle(items[i].kind);
    w.addSpacer(4);
    text(w, items[i].time || "Gün boyu", 28, st[0], "bold");
    text(w, items[i].title, 14, TEXT, "semi", 2);
    w.addSpacer();
    const after = nextIdx >= 0 ? items[nextIdx + 1] : null;
    text(w, after ? `Sonra: ${after.time} ${after.title}` : "Bugünün programı bitti", 10, MUTED, "", 1);
    return w;
  }
  const cap = family === "large" ? 9 : 4;
  title(w, head, day.subtitle);
  w.addSpacer(6);
  const start = Math.max(0, Math.min(nextIdx < 0 ? items.length : nextIdx, items.length - cap));
  for (let i = start; i < Math.min(items.length, start + cap); i++) {
    const st = kindStyle(items[i].kind);
    const row = w.addStack();
    row.layoutHorizontally();
    row.centerAlignContent();
    row.setPadding(5, 9, 5, 9);
    row.cornerRadius = 9;
    row.backgroundColor = done(i) ? new Color("#FFFFFF", 0.05) : new Color(st[1]);
    const t = text(row, items[i].time || "Gün boyu", 12, done(i) ? MUTED : st[0], "bold");
    t.minimumScaleFactor = 0.8;
    row.addSpacer(8);
    text(row, items[i].title, 12, done(i) ? MUTED : TEXT, "semi", 1);
    row.addSpacer();
    if (i === nextIdx) { row.borderColor = new Color(GREEN_HI); row.borderWidth = 1.5; }
    w.addSpacer(4);
  }
  w.addSpacer();
  return w;
}

// ---------------------------------------------------------------- Haftalık program
function pillText(it) {
  if (it.kind === "off") return "İZİN";
  if (it.kind === "training") return `${it.time} Antrenman`;
  if (it.kind === "meeting") return `${it.time} Toplantı`;
  if (it.kind === "camp") return `${it.time} Kamp`;
  if (it.kind === "match") return `${it.time} ${(it.title.split(" - ").pop() || it.title)}`;
  return `${it.time} ${it.title}`;
}

function weekWidget(x, family) {
  const w = newWidget(family);
  const now = new Date(), today = isoOf(now);
  const days = (x.program || []).filter(d => d.date >= today).slice(0, family === "large" ? 7 : 3);
  if (!days.length) { message(w, "HAFTALIK PROGRAM", "Yaklaşan program yok."); return w; }
  title(w, "HAFTALIK PROGRAM", days[0].subtitle);
  w.addSpacer(6);
  for (const d of days) {
    const dt = parseIso(d.date);
    const row = w.addStack();
    row.layoutHorizontally();
    row.centerAlignContent();
    row.setPadding(6, 8, 6, 8);
    row.cornerRadius = 9;
    row.backgroundColor = new Color("#FFFFFF", 0.05);
    if (d.date === today) { row.borderColor = new Color(GREEN_HI); row.borderWidth = 1.2; }
    const lab = text(row, `${DAYS3[dt.getDay()]} ${dt.getDate()} ${MONTHS3[dt.getMonth()]}`, 11, d.date === today ? GREEN_HI : TEXT, "bold", 1);
    lab.minimumScaleFactor = 0.8;
    row.addSpacer(8);
    for (const it of d.items.filter(i => ["training", "match", "meeting", "camp", "off"].includes(i.kind))) {
      const st = kindStyle(it.kind);
      const pill = row.addStack();
      pill.setPadding(3, 6, 3, 6);
      pill.cornerRadius = 8;
      pill.backgroundColor = new Color(st[1]);
      const t = text(pill, pillText(it), 10, st[0], "semi", 1);
      t.minimumScaleFactor = 0.7;
      row.addSpacer(4);
    }
    row.addSpacer();
    w.addSpacer(4);
  }
  w.addSpacer();
  return w;
}

// ---------------------------------------------------------------- Paylaşım takibi
function shareWidget(s, family) {
  const w = newWidget(family);
  if (!s || !s.last) { message(w, "PAYLAŞIM TAKİBİ", s ? "Henüz paylaşım kaydı yok." : "Veri yok. Mac'te MediaStaffKS'ı aç."); return w; }
  const last = s.last;
  if (family === "small") {
    title(w, "PAYLAŞIM TAKİBİ");
    w.addSpacer(4);
    text(w, "Son paylaşım", 11, MUTED);
    text(w, last.date, 17, TEXT, "bold");
    text(w, `${last.count} oyuncu`, 13, TEXT);
    w.addSpacer();
    text(w, s.never > 0 ? `${s.never} oyuncu 7 gündür paylaşılmadı` : "Herkes paylaşıldı", 11, s.never > 0 ? AMBER : GREEN_HI, "semi", 2);
    return w;
  }
  title(w, "PAYLAŞIM TAKİBİ", `Son paylaşım · ${last.date} · ${last.count} oyuncu`);
  w.addSpacer(8);
  const faces = w.addStack();
  faces.layoutHorizontally();
  for (const p of last.players.slice(0, family === "large" ? 7 : 6)) {
    const col = faces.addStack();
    col.layoutVertically();
    col.centerAlignContent();
    avatar(col, p.face, p.first, 38);
    col.addSpacer(3);
    text(col, p.first, 10, MUTED, "", 1);
    faces.addSpacer(6);
  }
  w.addSpacer(8);
  text(w, s.never > 0 ? `Son 7 günde paylaşılmayan: ${s.never} oyuncu` : "Son 7 günde herkes paylaşıldı", 11, s.never > 0 ? AMBER : GREEN_HI, "semi", 1);
  if (family === "large") {
    w.addSpacer(10);
    text(w, "SIRASI GELENLER", 10, MUTED, "bold");
    w.addSpacer(4);
    for (const q of (s.waiting || []).slice(0, 6)) {
      const row = w.addStack();
      row.layoutHorizontally();
      text(row, q.name, 13, TEXT, "semi", 1);
      row.addSpacer();
      text(row, q.days == null ? "hiç paylaşılmadı" : `${q.days} gün önce`, 11, q.days == null ? AMBER : MUTED, "semi");
      w.addSpacer(3);
    }
  }
  w.addSpacer();
  return w;
}

// ---------------------------------------------------------------- Sıradaki maç
function matchWidget(x, family) {
  const w = newWidget(family);
  const now = new Date();
  const fx = (x.fixtures || []).find(f => f.date >= isoOf(now));
  if (!fx) { message(w, "SIRADAKİ MAÇ", "Yaklaşan maç yok."); return w; }
  const d = parseIso(fx.date), n = daysUntil(d, now);
  const when = `${d.getDate()} ${MONTHS3[d.getMonth()]} · ${fx.time || "Saat belli değil"}`;
  title(w, "SIRADAKİ MAÇ");
  w.addSpacer(6);
  if (family === "small") {
    text(w, countdown(n), 30, GREEN_HI, "bold");
    text(w, fx.opponent, 15, TEXT, "bold", 1);
    text(w, fx.home ? "İç saha" : "Deplasman", 11, MUTED);
    w.addSpacer();
    text(w, when, 10, MUTED, "", 1);
    return w;
  }
  const row = w.addStack();
  row.layoutHorizontally();
  row.centerAlignContent();
  const left = row.addStack();
  left.layoutVertically();
  const logos = left.addStack();
  logos.layoutHorizontally();
  logos.centerAlignContent();
  for (const [b64, fb] of [[x.clubLogo, "K"], [fx.oppLogo, fx.opponent]]) {
    const im = img(b64);
    if (im) { const wi = logos.addImage(im); wi.imageSize = new Size(44, 44); }
    else { text(logos, fb.slice(0, 1), 24, TEXT, "bold"); }
    logos.addSpacer(8);
  }
  left.addSpacer(6);
  text(left, fx.opponent, 15, TEXT, "bold", 1);
  text(left, fx.home ? "İç saha" : "Deplasman", 11, GREEN_HI, "semi");
  row.addSpacer();
  const right = row.addStack();
  right.layoutVertically();
  const c = text(right, countdown(n), 32, GREEN_HI, "bold"); c.rightAlignText();
  const t1 = text(right, when, 12, TEXT, "semi", 1); t1.rightAlignText();
  if (fx.stadium) { const t2 = text(right, fx.stadium, 10, MUTED, "", 1); t2.rightAlignText(); }
  w.addSpacer();
  return w;
}

// ---------------------------------------------------------------- Doğum günleri
function birthdaysWidget(x, family) {
  const w = newWidget(family);
  const now = new Date();
  const list = (x.birthdays || []).map(b => {
    let d = parseIso(b.next);
    while (parseIso(isoOf(d)) < parseIso(isoOf(now))) d = new Date(d.getFullYear() + 1, d.getMonth(), d.getDate());
    return { b, days: daysUntil(d, now) };
  }).sort((a, c) => a.days - c.days);
  if (!list.length) { message(w, "DOĞUM GÜNLERİ", "Doğum günü verisi yok."); return w; }
  const chip = (parent, days) => {
    const s = parent.addStack();
    s.setPadding(3, 8, 3, 8);
    s.cornerRadius = 9;
    s.backgroundColor = days <= 7 ? new Color(GREEN, 0.18) : new Color("#FFFFFF", 0.06);
    text(s, countdown(days), 11, days <= 7 ? GREEN_HI : MUTED, "bold");
  };
  if (family === "small") {
    const f = list[0];
    title(w, "DOĞUM GÜNÜ");
    w.addSpacer(4);
    avatar(w, f.b.face, f.b.first, 46);
    w.addSpacer(4);
    text(w, f.b.name, 13, TEXT, "bold", 2);
    w.addSpacer();
    const r = w.addStack(); r.layoutHorizontally(); r.centerAlignContent();
    chip(r, f.days); r.addSpacer(6); text(r, `${f.b.turning}. yaş`, 10, MUTED);
    return w;
  }
  title(w, "DOĞUM GÜNLERİ");
  w.addSpacer(8);
  if (family === "medium") {
    const row = w.addStack();
    row.layoutHorizontally();
    for (const it of list.slice(0, 3)) {
      const col = row.addStack();
      col.layoutVertically();
      col.centerAlignContent();
      avatar(col, it.b.face, it.b.first, 44);
      col.addSpacer(4);
      text(col, it.b.first, 11, TEXT, "semi", 1);
      col.addSpacer(3);
      chip(col, it.days);
      row.addSpacer();
    }
  } else {
    for (const it of list.slice(0, 6)) {
      const row = w.addStack();
      row.layoutHorizontally();
      row.centerAlignContent();
      avatar(row, it.b.face, it.b.first, 34);
      row.addSpacer(10);
      const col = row.addStack();
      col.layoutVertically();
      text(col, it.b.name, 13, TEXT, "semi", 1);
      text(col, `${it.b.turning}. yaşına giriyor`, 10, MUTED);
      row.addSpacer();
      chip(row, it.days);
      w.addSpacer(6);
    }
  }
  w.addSpacer();
  return w;
}

// ---------------------------------------------------------------- Ana akış
const kind = String(args.widgetParameter || "program").trim().toLowerCase();
const family = config.widgetFamily || "medium";
let widget;
if (kind === "share") {
  widget = shareWidget(await load("share.json"), family);
} else {
  const x = await load("extra.json");
  if (!x) {
    widget = newWidget(family);
    message(widget, "MEDIASTAFFKS", "Veri bulunamadı. Mac'te MediaStaffKS'ı aç; iCloud'un eşitlemesini bekle.");
  } else if (kind === "week") widget = weekWidget(x, family);
  else if (kind === "match") widget = matchWidget(x, family);
  else if (kind === "birthdays") widget = birthdaysWidget(x, family);
  else widget = programWidget(x, family);
}
if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  await widget.presentMedium();
}
Script.complete();
'''


def scriptable_dir():
    """Scriptable'ın iCloud klasörü (iPhone'da Scriptable bir kez açılınca Mac'te de görünür). Yoksa None."""
    p = Path.home() / "Library" / "Mobile Documents" / "iCloud~dk~simonbs~Scriptable" / "Documents"
    try:
        return p if p.is_dir() else None
    except OSError:
        return None


def ios_sync(widget_dir):
    """widget/share.json + extra.json'u ve widget betiğini Scriptable'ın iCloud klasörüne kopyalar.
    Dönüş: ("ok"|"no_icloud"|"error", ayrıntı). Hata fırlatmaz."""
    try:
        base = scriptable_dir()
        if base is None:
            return "no_icloud", "Scriptable iCloud klasörü bulunamadı"
        script = base / IOS_SCRIPT_NAME
        want = SCRIPTABLE_JS.encode("utf-8")
        if not script.exists() or script.read_bytes() != want:
            script.write_bytes(want)
        dst = base / IOS_DATA_DIRNAME
        dst.mkdir(exist_ok=True)
        n = 0
        for name in ("share.json", "extra.json"):
            src = Path(widget_dir) / name
            if not src.is_file():
                continue
            data = src.read_bytes()
            out = dst / name
            if out.exists() and out.read_bytes() == data:
                continue
            out.write_bytes(data)
            n += 1
        return "ok", f"{n} dosya güncellendi"
    except Exception as exc:  # noqa: BLE001
        return "error", str(exc)
