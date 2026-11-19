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
#  TFF (tff.org) FİKSTÜR OKUYUCU
#  Süper Lig sayfasının her haftasını (hafta=1..34) indirir, Kocaelispor maçlarını ayıklar.
#  Sayfa yapısına bağımlılığı en aza indirmek için etiket/sınıf adlarına bakmaz: her tablo satırının
#  METİN parçalarından tarih, saat, skor ve iki takım adını bulur.
# ==========================================================================================

TFF_WEEK_URL = "https://www.tff.org/Default.aspx?pageID=198&hafta={week}"
TFF_WEEKS = 34
CLUB_NAME = KULUP_ADI

_TR_UP = str.maketrans({"i": "İ", "ı": "I"})
_TR_LOW = str.maketrans({"İ": "i", "I": "ı"})


def _tr_upper(t: str) -> str:
    return t.translate(_TR_UP).upper()


def _tr_title(t: str) -> str:
    out = []
    for w in t.translate(_TR_LOW).lower().split():
        out.append(w[:1].translate(_TR_UP).upper() + w[1:] if w else w)
    return " ".join(out)


# TFF'deki (büyük harfli, uzun) kulüp adı içinde geçen parça -> uygulamadaki kısa ad
_TEAM_KEYWORDS = [
    ("KOCAELİSPOR", "Kocaelispor"), ("GENÇLERBİRLİĞİ", "Gençlerbirliği"), ("ERZURUM", "Erzurumspor"),
    ("KONYASPOR", "Konyaspor"), ("GAZİANTEP", "Gaziantep FK"), ("RİZESPOR", "Rizespor"),
    ("GALATASARAY", "Galatasaray"), ("GÖZTEPE", "Göztepe"), ("EYÜPSPOR", "Eyüpspor"),
    ("ALANYASPOR", "Alanyaspor"), ("BAŞAKŞEHİR", "Başakşehir"), ("KASIMPAŞA", "Kasımpaşa"),
    ("SAMSUNSPOR", "Samsunspor"), ("FENERBAHÇE", "Fenerbahçe"), ("AMED", "Amedspor"),
    ("TRABZONSPOR", "Trabzonspor"), ("BEŞİKTAŞ", "Beşiktaş"), ("ÇORUM", "Çorum FK"),
]
_TEAM_STRIP = ("A.Ş.", "A.S.", "FUTBOL KULÜBÜ", "SPORTİF FAALİYETLER", "SPOR KULÜBÜ", "KULÜBÜ", "CORENDON", "ÇAYKUR",
               "TÜMOSAN", "TRENDYOL", "ARCA", "PAPARA", "RAMS", "BAHÇEŞEHİR", "LTD.", "ŞTİ.")

# Ev sahibi takımın bilinen stadyumu (TFF liste sayfası stadyum vermiyor). Bilinmeyen boş kalır.
TEAM_STADIUMS = {
    "Kocaelispor": "Kocaeli Stadyumu", "Beşiktaş": "Tüpraş Stadyumu", "Alanyaspor": "Bahçeşehir Okulları Stadyumu",
    "Eyüpspor": "Pendik Stadyumu", "Çorum FK": "Çorum Stadyumu", "Erzurumspor": "Kazım Karabekir Stadyumu",
    "Gençlerbirliği": "Eryaman Stadyumu", "Fenerbahçe": "Ülker Stadyumu", "Galatasaray": "RAMS Park",
    "Trabzonspor": "Papara Park", "Başakşehir": "Başakşehir Fatih Terim Stadyumu",
    "Samsunspor": "Samsun Yeni 19 Mayıs Stadyumu", "Göztepe": "Gürsel Aksel Stadyumu",
    "Rizespor": "Çaykur Didi Stadyumu", "Konyaspor": "Konya Büyükşehir Stadyumu",
    "Gaziantep FK": "Gaziantep Stadyumu", "Kasımpaşa": "Recep Tayyip Erdoğan Stadyumu",
    "Amedspor": "Diyarbakır Stadyumu",
}


def tff_team_name(raw: str) -> str:
    up = _tr_upper(raw.strip())
    for key, name in _TEAM_KEYWORDS:
        if key in up:
            return name
    for junk in _TEAM_STRIP:
        up = up.replace(junk, " ")
    return _tr_title(" ".join(up.split())) or raw.strip()


_DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_TIME_RE = re.compile(r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)")
_SCORE_RE = re.compile(r"^\d{1,2}\s*[-–]\s*\d{1,2}$")
_PLACEHOLDERS = {"-", "–", "—", "v", "vs", "?", "- -"}
_STOPWORDS = {"DETAYLAR", "DETAY", "MAÇ DETAYI", "MAÇ", "İSTATİSTİK", "HAFTA", "TARİH", "SAAT", "SKOR", "STAT", "STADYUM",
              "EV SAHİBİ", "DEPLASMAN", "TAKIM", "O", "G", "B", "M", "A", "Y", "AV", "P", "GENEL", "İÇ SAHA", "DIŞ SAHA",
              "DEVRE", "FİKSTÜR", "PUAN CETVELİ", "HAKEM", "TARAFSIZ", "TEKNİK DİREKTÖR", "SEZON"}


_TAG_RE = re.compile(r"<!--.*?-->|<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>|([^<]+)", re.S)
_SKIP_RE = re.compile(r"<(script|style)\b.*?</\1\s*>", re.S | re.I)
_ENTITIES = {"nbsp": " ", "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'", "#39": "'"}


def _unescape(text: str) -> str:
    def rep(m):
        name = m.group(1)
        if name in _ENTITIES:
            return _ENTITIES[name]
        try:
            if name[:2] in ("#x", "#X"):
                return chr(int(name[2:], 16))
            if name[:1] == "#":
                return chr(int(name[1:]))
        except (ValueError, OverflowError):
            pass
        return m.group(0)
    return re.sub(r"&(#?[a-zA-Z0-9]+);", rep, text)


def _collect_rows(html: str) -> list:
    """Tablo satırlarının (en içteki <tr>) metin parçalarını sırayla toplar.
    Standart kütüphanenin html.parser'ına bağımlı değil (paketli uygulamada garanti olmayabilir)."""
    html = _SKIP_RE.sub(" ", html)
    rows, stack = [], []
    for m in _TAG_RE.finditer(html):
        closing, tag, text = m.group(1), m.group(2), m.group(3)
        if tag:
            tag = tag.lower()
            if tag == "tr":
                if closing:
                    if stack:
                        rows.append(stack.pop())
                else:
                    stack.append([])
            elif tag == "br" and stack:
                stack[-1].append("")
        elif text is not None and stack:
            t = " ".join(_unescape(text).split())
            if t:
                stack[-1].append(t)
    rows.extend(r for r in reversed(stack))      # kapatılmamış <tr>'ler
    return rows


def _is_team_token(tok: str) -> bool:
    if _DATE_RE.search(tok) or _TIME_RE.fullmatch(tok) or _SCORE_RE.match(tok) or tok.lower() in _PLACEHOLDERS:
        return False
    if _tr_upper(tok) in _STOPWORDS or len(tok) > 70:
        return False
    letters = sum(c.isalpha() for c in tok)
    return letters >= 3 and letters >= 0.6 * len(tok.replace(" ", ""))


def _tok_date(tok):
    m = _DATE_RE.search(tok)
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def _tok_time(tok):
    m = _TIME_RE.search(tok)
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else None


def tff_parse_week(html: str) -> list:
    """Bir hafta sayfasından maçları çıkarır: [{"home","away","date" (ISO),"time","score"}].
    Bir satırda tek maç (tarih/saat sırası fark etmez) ya da birden çok maç (sırayla) olabilir."""
    try:
        rows = _collect_rows(html)
    except Exception:
        rows = []
    out = []
    carry_date = None

    def emit(home, away, d, t, score):
        if d is None:
            return
        out.append({"home": tff_team_name(home), "away": tff_team_name(away), "date": d.isoformat(),
                    "time": t or "", "score": score if _SCORE_RE.match(score or "") else ""})

    for tokens in rows:
        row_d = next((d for d in map(_tok_date, tokens) if d), None)
        row_t = next((t for t in map(_tok_time, tokens) if t), None)
        pairs = [i for i, tok in enumerate(tokens)
                 if (_SCORE_RE.match(tok) or tok.lower() in _PLACEHOLDERS)
                 and 0 < i < len(tokens) - 1
                 and _is_team_token(tokens[i - 1]) and _is_team_token(tokens[i + 1])]
        if len(pairs) == 1:
            i = pairs[0]
            emit(tokens[i - 1], tokens[i + 1], row_d or carry_date, row_t, tokens[i])
        elif len(pairs) > 1:
            cur_d, cur_t = carry_date, None
            for i, tok in enumerate(tokens):
                d = _tok_date(tok)
                if d:
                    cur_d = d
                t = _tok_time(tok)
                if t:
                    cur_t = t
                if i in pairs:
                    emit(tokens[i - 1], tokens[i + 1], cur_d, cur_t, tok)
                    cur_t = None
        else:
            teams = [tok for tok in tokens if _is_team_token(tok)]
            if len(teams) == 2 and (row_d or carry_date) and row_t:
                emit(teams[0], teams[1], row_d or carry_date, row_t, "")
        if row_d is not None:
            carry_date = row_d
    return out


def _decode(data: bytes) -> str:
    for enc in ("utf-8", "windows-1254"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def tff_fetch_week(week: int, ssl_context=None, timeout: int = 20) -> str:
    req = urllib.request.Request(
        TFF_WEEK_URL.format(week=week),
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                 "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as r:
        return _decode(r.read())


def tff_sync(ssl_context=None, progress=None, debug_dir=None, fetch=None) -> dict:
    """Tüm haftaları indirip Kocaelispor maçlarını döndürür.
    {"all": [...tüm maçlar], "kocaeli": [...], "errors": n, "weeks_ok": n, "first_error": str}"""
    fetch = fetch or (lambda w: tff_fetch_week(w, ssl_context))
    seen, allm, errors, weeks_ok, first_error = set(), [], 0, 0, ""
    saved_debug = False
    for w in range(1, TFF_WEEKS + 1):
        if progress:
            progress(w)
        html = None
        for attempt in (1, 2):
            try:
                html = fetch(w)
                break
            except Exception as e:  # noqa: BLE001
                first_error = first_error or str(e)
                _time.sleep(0.5)
        if html is None:
            errors += 1
            if errors >= 3 and weeks_ok == 0:
                break            # ağ yok / engelli: boşuna 34 hafta deneme
            continue
        ms = tff_parse_week(html)
        if ms:
            weeks_ok += 1
        elif debug_dir is not None and not saved_debug:
            try:                 # okunamayan ilk sayfayı sorun giderme için sakla
                Path(debug_dir).mkdir(parents=True, exist_ok=True)
                (Path(debug_dir) / "tff_debug.html").write_text(html, encoding="utf-8")
                saved_debug = True
            except OSError:
                pass
        for m in ms:
            key = (m["date"], m["home"], m["away"])
            if key not in seen:
                seen.add(key)
                allm.append(m)
        _time.sleep(0.25)
    kocaeli = [m for m in allm if CLUB_NAME in (m["home"], m["away"])]
    return {"all": allm, "kocaeli": kocaeli, "errors": errors, "weeks_ok": weeks_ok, "first_error": first_error}


def tff_merge(raw_fixtures: list, kocaeli_matches: list):
    """Mevcut fikstür listesini TFF maçlarıyla birleştirir (ev sahibi+deplasman çifti anahtar).
    TFF'de olan maçın tarih/saati güncellenir, stadyum varsa korunur / yoksa tablodan doldurulur.
    TFF'de olmayan (elle eklenmiş, ör. kupa) kayıtlara dokunulmaz.
    Döner: (yeni_liste, {"added","updated","unchanged"})"""
    by_key = {(f.get("home", ""), f.get("away", "")): dict(f) for f in raw_fixtures}
    stats = {"added": 0, "updated": 0, "unchanged": 0}
    for m in kocaeli_matches:
        key = (m["home"], m["away"])
        old = by_key.get(key)
        stadium = (old or {}).get("stadium") or TEAM_STADIUMS.get(m["home"], "")
        new = {"home": m["home"], "away": m["away"], "date": m["date"],
               "time": m["time"] or (old or {}).get("time", ""), "stadium": stadium}
        if old is None:
            stats["added"] += 1
        elif (old.get("date"), old.get("time"), old.get("stadium", "")) != (new["date"], new["time"], new["stadium"]):
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1
        by_key[key] = new
    merged = sorted(by_key.values(), key=lambda f: (f.get("date", ""), f.get("time", "")))
    return merged, stats
