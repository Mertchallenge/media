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

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QFileDialog, QMessageBox,
    QHeaderView, QAbstractItemView, QLineEdit
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

    tokens = [name_slug(t) for t in name.split() if len(t) >= 3]
    best, best_len = None, -1
    for folder in candidate_dirs:
        try:
            entries = list(folder.iterdir())
        except OSError:
            continue
        for entry in entries:
            if not entry.is_file() or entry.suffix.lower().lstrip(".") not in _IMG_EXTS:
                continue
            file_slug = name_slug(entry.stem)
            if not file_slug:
                continue
            matched = (file_slug == slug or file_slug in slug or slug in file_slug
                       or file_slug in tokens or any(len(tok) >= 4 and tok in file_slug for tok in tokens))
            if matched and len(file_slug) > best_len:
                best, best_len = entry, len(file_slug)
    return best


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

def make_btn(text: str, height: int = 34) -> QPushButton:
    btn = QPushButton(text)
    btn.setFixedHeight(height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def stretch_header(table: QTableWidget):
    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


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
        del_btn = make_btn("Seçili satırı sil")
        del_btn.clicked.connect(self.delete_row)
        save_btn = make_btn("Kaydet")
        save_btn.setObjectName("primaryBtn")
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
        self.status.setText("")

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
        del_btn = make_btn("Seçili satırı sil")
        del_btn.clicked.connect(self.delete_row)
        save_btn = make_btn("Kaydet")
        save_btn.setObjectName("primaryBtn")
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
        self.status.setText("")

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
    def __init__(self, title_hint: str, names_fn, path_fn, dirnames, detect_word, parent_window):
        super().__init__()
        self.names_fn = names_fn
        self.path_fn = path_fn
        self.dirnames = dirnames
        self.detect_word = detect_word
        self.parent_window = parent_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hint = QLabel(title_hint)
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        top_row = QHBoxLayout()
        refresh_btn = make_btn("Listeyi yenile", 30)
        refresh_btn.clicked.connect(self.reload)
        top_row.addWidget(refresh_btn)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(0)
        holder = QWidget()
        holder.setLayout(self.rows_layout)
        layout.addWidget(holder)
        layout.addStretch(1)

        self.reload()

    def reload(self):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        names = self.names_fn()
        if not names:
            empty = QLabel("Henüz veri yok. Önce ilgili sekmeden ekleyip kaydet.")
            empty.setObjectName("hint")
            self.rows_layout.addWidget(empty)
            return

        for name in names:
            self.rows_layout.addWidget(self._row(name))

    def _row(self, name: str) -> QWidget:
        row = QWidget()
        row.setObjectName("imgRow")
        h = QHBoxLayout(row)
        h.setContentsMargins(8, 8, 8, 8)
        h.setSpacing(12)

        preview = QLabel()
        preview.setFixedSize(44, 44)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setObjectName("preview")
        path = self.path_fn(name)
        if path is not None:
            raw = QPixmap()
            if raw.load(str(path)) and not raw.isNull():
                preview.setPixmap(raw.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation))
        else:
            preview.setText("—")
        h.addWidget(preview)

        name_lab = QLabel(name)
        h.addWidget(name_lab, 1)

        pick_btn = make_btn("Değiştir" if path is not None else "Görsel seç", 30)
        pick_btn.clicked.connect(lambda checked=False, n=name: self._pick(n))
        h.addWidget(pick_btn)

        if path is not None:
            remove_btn = make_btn("Kaldır", 30)
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
QLabel#hint {{ color: {K_MUTED}; }}
QLabel#status {{ color: {K_GREEN_HI}; font-weight: 600; }}
QTabWidget::pane {{ border: 1px solid {K_BORDER}; border-radius: 10px; top: -1px; }}
QTabBar::tab {{ background: {K_CARD}; color: {K_MUTED}; padding: 10px 18px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; }}
QTabBar::tab:selected {{ background: {K_GREEN}; color: white; font-weight: 600; }}
QTableWidget {{ background-color: {K_CARD}; gridline-color: {K_BORDER}; border: 1px solid {K_BORDER}; border-radius: 8px; }}
QHeaderView::section {{ background-color: {K_BG}; color: {K_MUTED}; padding: 6px; border: none; border-bottom: 1px solid {K_BORDER}; }}
QPushButton {{ background-color: {K_CARD}; color: {K_TEXT}; border: 1px solid {K_BORDER}; border-radius: 8px; padding: 6px 14px; }}
QPushButton:hover {{ border-color: {K_GREEN_HI}; }}
QPushButton#primaryBtn {{ background-color: {K_GREEN}; color: white; font-weight: 700; border: none; }}
QPushButton#primaryBtn:hover {{ background-color: {K_GREEN_HI}; color: #04140D; }}
QWidget#imgRow {{ background-color: {K_CARD}; border-bottom: 1px solid {K_BORDER}; }}
QLabel#preview {{ background-color: {K_BG}; border-radius: 8px; color: {K_MUTED}; }}
QLineEdit {{ background-color: {K_CARD}; border: 1px solid {K_BORDER}; border-radius: 6px; padding: 4px 8px; }}
"""


class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaStaffKS — Admin Paneli")
        self.resize(980, 680)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Admin Paneli")
        title.setStyleSheet("font-size: 20px; font-weight: 800;")
        layout.addWidget(title)
        sub = QLabel(f"Veriler \"{ks_data.DATA_PATH.name}\" dosyasına kaydedilir · {ks_data.DATA_PATH.parent}")
        sub.setObjectName("hint")
        layout.addWidget(sub)

        self.tabs = QTabWidget()
        self.fixtures_tab = FixturesTab()
        self.roster_tab = RosterTab()
        self.logos_tab = ImageListTab(
            "Fikstürdeki her rakip takım için bir logo seç. Önce 'Fikstür' sekmesinde maçları "
            "ekleyip kaydetmelisin ki takım burada listelensin.",
            opponent_names, team_logo_path, TEAM_LOGOS_DIRNAMES, "logo", self,
        )
        self.photos_tab = ImageListTab(
            "Kadrodaki her oyuncu için bir fotoğraf seç. Önce 'Kadro' sekmesinde oyuncuları "
            "ekleyip kaydetmelisin ki burada listelensin.",
            roster_names, player_photo_path, PLAYER_PHOTOS_DIRNAMES, "oyuncu", self,
        )
        self.tabs.addTab(self.fixtures_tab, "Fikstür")
        self.tabs.addTab(self.roster_tab, "Kadro")
        self.tabs.addTab(self.logos_tab, "Takım Logoları")
        self.tabs.addTab(self.photos_tab, "Oyuncu Fotoğrafları")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs, 1)

        note = QLabel("Değişiklikler MediaStaffKS'e bir sonraki açılışında yansır "
                       "(uygulama açıksa kapatıp yeniden açman gerekir).")
        note.setObjectName("hint")
        note.setWordWrap(True)
        layout.addWidget(note)

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
