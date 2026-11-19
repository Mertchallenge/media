#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaStaffKS — Admin Paneli
============================
MediaStaffKS'ten (main.py) TAMAMEN AYRI, kendi penceresinde açılan bir yönetim aracı.
Buradan:
  - Fikstür (maç ekle / düzenle / sil)
  - Kadro (oyuncu ekle / düzenle / sil — forma no, mevki, doğum tarihi)
  - Takım logoları (görsel seç / kaldır)
  - Oyuncu fotoğrafları (görsel seç / kaldır)
yönetilir. Tüm değişiklikler main.py ile AYNI klasördeki "veri.json" dosyasına yazılır;
MediaStaffKS bir sonraki açılışında bu dosyadaki güncel veriyi otomatik okur.

Çalıştırmak için: main.py ile birlikte aynı klasörde olmalı, "python3 admin.py" ile açılır.
"""

import sys
import unicodedata
import re
from pathlib import Path

import ks_data

from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QPixmap, QColor, QPalette, QPainter, QPainterPath, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QLineEdit, QScrollArea, QFrame, QSizePolicy
)

K_BG = "#0E1712"
K_CARD = "#152019"
K_GREEN = "#35784C"
K_GREEN_HI = "#5FD889"
K_TEXT = "#EAF2EC"
K_MUTED = "#8FA398"
K_BORDER = "#223229"

APP_DIR = Path(__file__).resolve().parent


# ==========================================================================================
#  Görsel klasörleri — main.py'deki okuma mantığıyla AYNI kurallar (bağımsız kopya)
# ==========================================================================================

TEAM_LOGOS_DIRNAMES = ("takim_logolari", "logolar", "logos")
PLAYER_PHOTOS_DIRNAMES = ("oyuncu_fotograflari", "oyuncularimiz", "oyuncular", "oyuncu_resimleri",
                           "player_photos", "fotograflar")
_IMG_EXTS = ("png", "jpg", "jpeg", "webp")

_TR_SLUG_MAP = str.maketrans({
    "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
})


def name_slug(text: str) -> str:
    slug = text.strip().lower().translate(_TR_SLUG_MAP)
    slug = "".join(ch if ch.isalnum() else "_" for ch in slug)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def pick_photo_entry(full_slug: str, entries: list):
    """entries: [(dosya_slug, öğe)]. Yalnız TAM kelime eşleşmesi: "onur" dosyası "Onurcan Piri"ye düşmez.
    Öncelik: tam ad > aynı kelime kümesi > dosya adı ismin kelimelerinden biri/birkaçı > dosyada fazladan kelime var."""
    nset = {t for t in full_slug.split("_") if t}
    best, best_score = None, 0
    for slug, item in entries:
        if not slug:
            continue
        if slug == full_slug:
            score = 1000
        else:
            fset = {t for t in slug.split("_") if t}
            if not fset:
                continue
            if fset == nset:
                score = 900
            elif fset <= nset:
                score = 500 + len(fset)
            elif nset and nset <= fset:
                score = 600 - len(fset)
            else:
                continue
        if score > best_score:
            best, best_score = item, score
    return best


def _find_in_dirs(dirnames, extra_detect_word, name: str):
    slug = name_slug(name)
    candidate_dirs = []
    for dirname in dirnames:
        d = APP_DIR / dirname
        if d.is_dir():
            candidate_dirs.append(d)
    try:
        for entry in APP_DIR.iterdir():
            if entry.is_dir() and entry not in candidate_dirs and extra_detect_word in name_slug(entry.name):
                candidate_dirs.append(entry)
    except OSError:
        pass

    for folder in candidate_dirs:
        for ext in _IMG_EXTS:
            cand = folder / f"{slug}.{ext}"
            if cand.is_file():
                return cand
            cand = folder / f"{slug}.{ext.upper()}"
            if cand.is_file():
                return cand

    found = []
    for folder in candidate_dirs:
        try:
            entries = list(folder.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_file() and entry.suffix.lower().lstrip(".") in _IMG_EXTS:
                found.append((name_slug(entry.stem), entry))
    return pick_photo_entry(slug, found)


def _write_dir(dirnames, extra_detect_word):
    for dirname in dirnames:
        d = APP_DIR / dirname
        if d.is_dir():
            return d
    try:
        for entry in APP_DIR.iterdir():
            if entry.is_dir() and extra_detect_word in name_slug(entry.name):
                return entry
    except OSError:
        pass
    d = APP_DIR / dirnames[0]
    d.mkdir(parents=True, exist_ok=True)
    return d


def team_logo_path(name: str):
    return _find_in_dirs(TEAM_LOGOS_DIRNAMES, "takim", name) or _find_in_dirs(TEAM_LOGOS_DIRNAMES, "logo", name)


def player_photo_path(name: str):
    return _find_in_dirs(PLAYER_PHOTOS_DIRNAMES, "oyuncu", name)


def set_image(target_dir: Path, name: str, old_path, source_file: str) -> bool:
    raw = QPixmap()
    if not raw.load(source_file) or raw.isNull():
        return False
    if old_path is not None:
        try:
            old_path.unlink()
        except OSError:
            pass
    target = target_dir / f"{name_slug(name)}.png"
    return raw.save(str(target), "PNG")


def remove_image(path) -> bool:
    if path is None:
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False


def slugify(name: str) -> str:
    folded = unicodedata.normalize("NFKD", name.replace("ı", "i").replace("İ", "I"))
    ascii_text = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


POSITIONS = [
    "Kaleci", "Stoper", "Sol bek", "Sağ bek", "Ön libero", "Merkez orta saha",
    "On numara", "Sol kanat", "Sağ kanat", "Santrafor",
]


# ==========================================================================================
#  Küçük yardımcılar
# ==========================================================================================

def make_btn(text: str, height: int = 32, variant: str = "") -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedHeight(height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if variant:
        btn.setObjectName(variant)
    return btn


def stretch_header(table: QTableWidget):
    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)


def rounded_pixmap(raw: QPixmap, size: int, radius: int) -> QPixmap:
    """Görseli size x size kareye sığdırıp (kırparak) verilen köşe yarıçapıyla yuvarlar."""
    if raw.isNull():
        return raw
    scaled = raw.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                         Qt.TransformationMode.SmoothTransformation)
    x = max(0, (scaled.width() - size) // 2)
    y = max(0, (scaled.height() - size) // 2)
    cropped = scaled.copy(x, y, size, size)
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, cropped)
    painter.end()
    return result


# ==========================================================================================
#  SEKME 1 — FİKSTÜR
# ==========================================================================================

class FixturesTab(QWidget):
    COLUMNS = ["Ev Sahibi", "Deplasman", "Tarih (YYYY-AA-GG)", "Saat (SS:DD)", "Stadyum"]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hint = QLabel("Her satır bir maç. Hücrelere çift tıklayıp düzenleyebilirsin. "
                       "Bitince mutlaka 'Kaydet'e bas.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        stretch_header(self.table)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        add_btn = make_btn("+ Maç ekle")
        add_btn.clicked.connect(self.add_row)
        del_btn = make_btn("Seçili satırı sil", variant="dangerBtn")
        del_btn.clicked.connect(self.delete_row)
        save_btn = make_btn("Kaydet", 36, "primaryBtn")
        save_btn.clicked.connect(self.save)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self.status = QLabel("")
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        self.reload()

    def reload(self):
        raw = ks_data.load_raw()
        self.table.setRowCount(0)
        for fx in raw.get("fixtures", []):
            self._append_row(fx.get("home", ""), fx.get("away", ""), fx.get("date", ""),
                              fx.get("time", ""), fx.get("stadium", ""))
        self.status.setText(f"{self.table.rowCount()} maç yüklendi.")

    def _append_row(self, home, away, date_text, time_text, stadium):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, value in enumerate([home, away, date_text, time_text, stadium]):
            self.table.setItem(row, col, QTableWidgetItem(str(value or "")))

    def add_row(self):
        self._append_row("Kocaelispor", "", "2026-01-01", "19:00", "")

    def delete_row(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def save(self):
        fixtures = []
        for row in range(self.table.rowCount()):
            def cell(c):
                item = self.table.item(row, c)
                return item.text().strip() if item else ""
            home, away, date_text, time_text, stadium = cell(0), cell(1), cell(2), cell(3), cell(4)
            if not home or not away:
                continue
            if ks_data.parse_date(date_text) is None:
                QMessageBox.warning(self, "Geçersiz tarih",
                                     f"{home} - {away} maçının tarihi \"{date_text}\" okunamadı.\n"
                                     "YYYY-AA-GG biçiminde olmalı (ör. 2026-11-21).")
                return
            fixtures.append({"home": home, "away": away, "date": date_text,
                              "time": time_text, "stadium": stadium})
        ks_data.save_fixtures(fixtures)
        self.status.setText(f"Kaydedildi — {len(fixtures)} maç.")


# ==========================================================================================
#  SEKME 2 — KADRO
# ==========================================================================================

class RosterTab(QWidget):
    COLUMNS = ["Ad Soyad", "Doğum Tarihi (YYYY-AA-GG)", "Forma No", "Mevki"]

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hint = QLabel(f"Mevki örnekleri: {', '.join(POSITIONS)}. Forma numarası boş bırakılabilir. "
                      "Bitince 'Kaydet'e bas.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        stretch_header(self.table)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        add_btn = make_btn("+ Oyuncu ekle")
        add_btn.clicked.connect(self.add_row)
        del_btn = make_btn("Seçili satırı sil", variant="dangerBtn")
        del_btn.clicked.connect(self.delete_row)
        save_btn = make_btn("Kaydet", 36, "primaryBtn")
        save_btn.clicked.connect(self.save)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self.status = QLabel("")
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        self.reload()

    def reload(self):
        raw = ks_data.load_raw()
        self.table.setRowCount(0)
        for p in raw.get("players", []):
            self._append_row(p.get("name", ""), p.get("dob", ""), p.get("no"), p.get("pos", ""))
        self.status.setText(f"{self.table.rowCount()} oyuncu yüklendi.")

    def _append_row(self, name, dob, no, pos):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(name or "")))
        self.table.setItem(row, 1, QTableWidgetItem(str(dob or "")))
        self.table.setItem(row, 2, QTableWidgetItem("" if no in (None, "") else str(no)))
        self.table.setItem(row, 3, QTableWidgetItem(str(pos or "")))

    def add_row(self):
        self._append_row("", "", "", "Kaleci")

    def delete_row(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)

    def save(self):
        players = []
        for row in range(self.table.rowCount()):
            def cell(c):
                item = self.table.item(row, c)
                return item.text().strip() if item else ""
            name, dob_text, no_text, pos = cell(0), cell(1), cell(2), cell(3)
            if not name:
                continue
            dob = None
            if dob_text:
                if ks_data.parse_date(dob_text) is None:
                    QMessageBox.warning(self, "Geçersiz tarih",
                                         f"{name} için doğum tarihi \"{dob_text}\" okunamadı.\n"
                                         "YYYY-AA-GG biçiminde olmalı (ör. 2004-12-09) ya da boş bırakılmalı.")
                    return
                dob = dob_text
            no = None
            if no_text:
                try:
                    no = int(no_text)
                except ValueError:
                    QMessageBox.warning(self, "Geçersiz forma no",
                                         f"{name} için forma no \"{no_text}\" sayı değil.")
                    return
            players.append({"name": name, "dob": dob, "no": no, "pos": pos})
        ks_data.save_players(players)
        self.status.setText(f"Kaydedildi — {len(players)} oyuncu.")


# ==========================================================================================
#  SEKME 3 / 4 — GÖRSELLER (takım logoları / oyuncu fotoğrafları) — ortak satır bileşeni
# ==========================================================================================

class ImageListTab(QWidget):
    def __init__(self, title_hint: str, names_fn, path_fn, dirnames, detect_word,
                 parent_window, round_preview: bool = False, noun: str = "kayıt"):
        super().__init__()
        self.names_fn = names_fn
        self.path_fn = path_fn
        self.dirnames = dirnames
        self.detect_word = detect_word
        self.parent_window = parent_window
        self.round_preview = round_preview
        self.noun = noun

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hint = QLabel(title_hint)
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        top_row = QHBoxLayout()
        self.count_label = QLabel("")
        self.count_label.setObjectName("status")
        top_row.addWidget(self.count_label)
        top_row.addStretch(1)
        refresh_btn = make_btn("Listeyi yenile", 30)
        refresh_btn.clicked.connect(self.reload)
        top_row.addWidget(refresh_btn)
        layout.addLayout(top_row)

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(8)
        self.rows_layout.setContentsMargins(0, 2, 0, 2)
        holder = QWidget()
        holder.setLayout(self.rows_layout)

        scroll = QScrollArea()
        scroll.setObjectName("imgScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(holder)
        layout.addWidget(scroll, 1)

        self.reload()

    def reload(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        names = self.names_fn()
        plural = self.noun if self.noun.endswith("ı") or self.noun.endswith("u") else self.noun
        self.count_label.setText(f"{len(names)} {plural}")
        if not names:
            empty = QLabel("Henüz veri yok. Önce ilgili sekmeden ekleyip kaydet.")
            empty.setObjectName("hint")
            self.rows_layout.addWidget(empty)
            self.rows_layout.addStretch(1)
            return

        for name in names:
            self.rows_layout.addWidget(self._row(name))
        self.rows_layout.addStretch(1)

    def _row(self, name: str) -> QFrame:
        row = QFrame()
        row.setObjectName("imgRow")
        h = QHBoxLayout(row)
        h.setContentsMargins(12, 10, 12, 10)
        h.setSpacing(14)

        preview = QLabel()
        preview.setFixedSize(46, 46)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setObjectName("preview")
        path = self.path_fn(name)
        if path is not None:
            raw = QPixmap()
            if raw.load(str(path)) and not raw.isNull():
                radius = 23 if self.round_preview else 10
                preview.setPixmap(rounded_pixmap(raw, 42, radius))
        else:
            preview.setText("—")
        h.addWidget(preview)

        name_lab = QLabel(name)
        name_lab.setObjectName("rowName")
        h.addWidget(name_lab, 1)

        status_lab = QLabel("Görsel eklendi" if path is not None else "Görsel yok")
        status_lab.setObjectName("rowStatusOk" if path is not None else "rowStatusMissing")
        h.addWidget(status_lab)

        pick_btn = make_btn("Değiştir" if path is not None else "Görsel seç", 32)
        pick_btn.clicked.connect(lambda checked=False, n=name: self._pick(n))
        h.addWidget(pick_btn)

        if path is not None:
            remove_btn = make_btn("Kaldır", 32, "dangerBtn")
            remove_btn.clicked.connect(lambda checked=False, n=name: self._remove(n))
            h.addWidget(remove_btn)

        return row

    def _pick(self, name: str):
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"{name} için görsel seç", "", "Görseller (*.png *.jpg *.jpeg *.webp)")
        if not file_path:
            return
        target_dir = _write_dir(self.dirnames, self.detect_word)
        old = self.path_fn(name)
        if set_image(target_dir, name, old, file_path):
            self.reload()
        else:
            QMessageBox.warning(self, "Olmadı", "Bu görsel okunamadı, başka bir dosya seçmeyi dener misin?")

    def _remove(self, name: str):
        remove_image(self.path_fn(name))
        self.reload()


def opponent_names() -> list:
    raw = ks_data.load_raw()
    names, seen = [], set()
    for fx in raw.get("fixtures", []):
        for side in (fx.get("home", ""), fx.get("away", "")):
            if side and side != ks_data.KULUP_ADI and side not in seen:
                seen.add(side)
                names.append(side)
    return names


def roster_names() -> list:
    raw = ks_data.load_raw()
    return [p.get("name", "") for p in raw.get("players", []) if p.get("name")]


# ==========================================================================================
#  ANA PENCERE
# ==========================================================================================

STYLESHEET = f"""
QWidget {{ background-color: {K_BG}; color: {K_TEXT}; font-family: -apple-system, "Segoe UI", sans-serif; font-size: 13px; }}
QMainWindow {{ background-color: {K_BG}; }}
QLabel#hint {{ color: {K_MUTED}; }}
QLabel#status {{ color: {K_MUTED}; font-weight: 600; }}
QLabel#rowName {{ font-weight: 600; font-size: 13.5px; }}
QLabel#rowStatusOk {{ color: {K_GREEN_HI}; font-size: 11.5px; }}
QLabel#rowStatusMissing {{ color: {K_MUTED}; font-size: 11.5px; }}

QFrame#headerBar {{ background-color: {K_CARD}; border: 1px solid {K_BORDER}; border-radius: 14px; }}
QLabel#appTitle {{ font-size: 19px; font-weight: 800; color: {K_TEXT}; }}
QLabel#appBadge {{ background-color: {K_GREEN}; color: white; font-weight: 700; font-size: 11px;
                    border-radius: 9px; padding: 3px 10px; }}
QLabel#pathHint {{ color: {K_MUTED}; font-size: 11.5px; }}

QTabWidget::pane {{ border: 1px solid {K_BORDER}; border-radius: 12px; top: -1px; background-color: {K_CARD}; }}
QTabBar {{ background: transparent; }}
QTabBar::tab {{ background: transparent; color: {K_MUTED}; padding: 11px 20px; font-weight: 600;
                border-top-left-radius: 10px; border-top-right-radius: 10px; margin-right: 2px; }}
QTabBar::tab:hover {{ color: {K_TEXT}; }}
QTabBar::tab:selected {{ background: {K_GREEN}; color: white; }}

QTableWidget {{ background-color: {K_CARD}; gridline-color: {K_BORDER}; border: 1px solid {K_BORDER};
                border-radius: 10px; alternate-background-color: #192720; selection-background-color: {K_GREEN};
                selection-color: white; padding: 2px; }}
QTableWidget::item {{ padding: 6px 4px; border: none; }}
QHeaderView::section {{ background-color: {K_CARD}; color: {K_MUTED}; font-weight: 700; padding: 10px 6px;
                         border: none; border-bottom: 2px solid {K_BORDER}; }}

QPushButton {{ background-color: transparent; color: {K_TEXT}; border: 1px solid {K_BORDER};
               border-radius: 8px; padding: 6px 14px; font-weight: 600; }}
QPushButton:hover {{ border-color: {K_GREEN_HI}; color: {K_GREEN_HI}; }}
QPushButton:pressed {{ background-color: {K_BORDER}; }}
QPushButton#primaryBtn {{ background-color: {K_GREEN}; color: white; border: none; }}
QPushButton#primaryBtn:hover {{ background-color: {K_GREEN_HI}; color: #04140D; }}
QPushButton#dangerBtn {{ border-color: #4A2227; color: #FF9EA3; }}
QPushButton#dangerBtn:hover {{ background-color: #2E1719; border-color: #FF7B7F; color: #FF7B7F; }}

QFrame#imgRow {{ background-color: #192720; border: 1px solid {K_BORDER}; border-radius: 10px; }}
QFrame#imgRow:hover {{ border-color: {K_GREEN}; }}
QLabel#preview {{ background-color: {K_BG}; border-radius: 10px; color: {K_MUTED}; font-weight: 700; }}

QLineEdit {{ background-color: {K_CARD}; border: 1px solid {K_BORDER}; border-radius: 6px; padding: 4px 8px; }}

QScrollArea#imgScroll {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {K_BORDER}; border-radius: 5px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {K_GREEN}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
"""


class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaStaffKS — Admin Paneli")
        self.resize(1080, 760)
        self.setMinimumSize(880, 560)

        logo_path = APP_DIR / "kocaelispor_logo.png"
        if logo_path.is_file():
            self.setWindowIcon(QIcon(str(logo_path)))

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        header = QFrame()
        header.setObjectName("headerBar")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 16, 20, 16)
        h_layout.setSpacing(14)
        if logo_path.is_file():
            logo_lab = QLabel()
            raw = QPixmap(str(logo_path))
            if not raw.isNull():
                logo_lab.setPixmap(raw.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation))
            h_layout.addWidget(logo_lab)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Admin Paneli")
        title.setObjectName("appTitle")
        title_col.addWidget(title)
        sub = QLabel(f"Kayıt dosyası: {ks_data.DATA_PATH}")
        sub.setObjectName("pathHint")
        title_col.addWidget(sub)
        h_layout.addLayout(title_col, 1)
        badge = QLabel("MediaStaffKS'ten ayrı")
        badge.setObjectName("appBadge")
        h_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
        outer.addWidget(header)

        self.tabs = QTabWidget()
        self.fixtures_tab = FixturesTab()
        self.roster_tab = RosterTab()
        self.logos_tab = ImageListTab(
            "Fikstürdeki her rakip takım için bir logo seç. Önce 'Fikstür' sekmesinde maçları "
            "ekleyip kaydetmelisin ki takım burada listelensin.",
            opponent_names, team_logo_path, TEAM_LOGOS_DIRNAMES, "logo", self,
            round_preview=False, noun="takım",
        )
        self.photos_tab = ImageListTab(
            "Kadrodaki her oyuncu için bir fotoğraf seç. Önce 'Kadro' sekmesinde oyuncuları "
            "ekleyip kaydetmelisin ki burada listelensin.",
            roster_names, player_photo_path, PLAYER_PHOTOS_DIRNAMES, "oyuncu", self,
            round_preview=True, noun="oyuncu",
        )
        self.tabs.addTab(self.fixtures_tab, "Fikstür")
        self.tabs.addTab(self.roster_tab, "Kadro")
        self.tabs.addTab(self.logos_tab, "Takım Logoları")
        self.tabs.addTab(self.photos_tab, "Oyuncu Fotoğrafları")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        outer.addWidget(self.tabs, 1)

        note = QLabel("Değişiklikler MediaStaffKS'e bir sonraki açılışında yansır "
                       "(uygulama açıksa kapatıp yeniden açman gerekir).")
        note.setObjectName("hint")
        note.setWordWrap(True)
        outer.addWidget(note)

    def _on_tab_changed(self, index: int):
        widget = self.tabs.widget(index)
        if isinstance(widget, ImageListTab):
            widget.reload()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    win = AdminWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
