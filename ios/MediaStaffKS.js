// MediaStaffKS — iPhone widget'ları (Scriptable uygulaması için).
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
