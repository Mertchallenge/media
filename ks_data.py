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
from datetime import date
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "veri.json"

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


def _default_data() -> dict:
    return {
        "fixtures": [dict(f) for f in DEFAULT_FIXTURES],
        "players": [dict(p) for p in DEFAULT_PLAYERS],
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
    """data: {"fixtures": [...], "players": [...]} — tüm tarihler ISO metin ("YYYY-AA-GG")."""
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
            data.setdefault("fixtures", [])
            data.setdefault("players", [])
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
    return {"fixtures": fixtures, "players": players}


def save_fixtures(fixtures: list) -> None:
    """fixtures: [{"home","away","date" (ISO metin),"time","stadium"}, ...]"""
    raw = load_raw()
    raw["fixtures"] = fixtures
    save_raw(raw)


def save_players(players: list) -> None:
    """players: [{"name","dob" (ISO metin ya da None),"no","pos"}, ...]"""
    raw = load_raw()
    raw["players"] = players
    save_raw(raw)
