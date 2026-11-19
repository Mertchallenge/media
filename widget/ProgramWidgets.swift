// "Bugünün programı" ve "Haftalık program" widget'ları. Veri: extra.json
import WidgetKit
import SwiftUI
import AppKit

// MARK: - Bugünün programı

struct ProgramEntry: TimelineEntry {
    let date: Date
    let day: XDay?
    let hasData: Bool
    var tomorrow: Bool = false      // günün son etkinliğinden 30 dk sonra yarının programı gösterilir
}

func programDay(_ x: XData?, _ date: Date) -> XDay? {
    let iso = isoString(date)
    return x?.program.first { $0.date == iso }
}

/// Günün son saatli etkinliğinden 30 dk sonrası; saatli satır yoksa nil.
func programRollover(_ day: XDay?, _ ref: Date) -> Date? {
    guard let day = day else { return nil }
    let stamps = day.items.compactMap { $0.time.isEmpty ? nil : timeToday($0.time, ref) }
    return stamps.max().map { $0.addingTimeInterval(30 * 60) }
}

/// `at` anında gösterilecek gün: bugün; son etkinlikten 30 dk sonra (ve yarın programı varsa) yarın.
func effectiveProgram(_ x: XData?, _ at: Date) -> (day: XDay?, tomorrow: Bool) {
    let today = programDay(x, at)
    if let r = programRollover(today, at), at >= r,
       let next = Calendar.current.date(byAdding: .day, value: 1, to: at),
       let tm = programDay(x, next), !tm.items.isEmpty {
        return (tm, true)
    }
    return (today, false)
}

func programEntry(_ x: XData?, _ at: Date) -> ProgramEntry {
    let e = effectiveProgram(x, at)
    return ProgramEntry(date: at, day: e.day, hasData: x != nil, tomorrow: e.tomorrow)
}

struct ProgramTodayProvider: TimelineProvider {
    func placeholder(in context: Context) -> ProgramEntry { ProgramEntry(date: Date(), day: nil, hasData: false) }

    func getSnapshot(in context: Context, completion: @escaping (ProgramEntry) -> Void) {
        completion(programEntry(Store.read("extra.json", as: XData.self), Date()))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<ProgramEntry>) -> Void) {
        let x = Store.read("extra.json", as: XData.self)
        let now = Date()
        let cal = Calendar.current
        var moments: [Date] = []
        let tomorrowDate = cal.date(byAdding: .day, value: 1, to: now) ?? now
        // bugünün satır saatleri, geçiş anı, gece yarısı ve yarının satır saatleri
        let today = programDay(x, now)
        for it in today?.items ?? [] { if let t = timeToday(it.time, now) { moments.append(t) } }
        if let r = programRollover(today, now) { moments.append(r) }
        let midnight = cal.startOfDay(for: tomorrowDate)
        moments.append(midnight)
        for it in programDay(x, tomorrowDate)?.items ?? [] { if let t = timeToday(it.time, tomorrowDate) { moments.append(t) } }
        var entries = [programEntry(x, now)]
        for t in Set(moments).sorted() where t > now { entries.append(programEntry(x, t)) }
        completion(Timeline(entries: entries, policy: .after(now.addingTimeInterval(30 * 60))))
    }
}

struct ItemRow: View {
    let item: XItem
    let done: Bool
    let isNext: Bool
    @Environment(\.widgetRenderingMode) var mode

    var body: some View {
        let st = kindStyle(item.kind)
        HStack(spacing: 8) {
            Text(item.time.isEmpty ? "Gün boyu" : item.time)
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(done ? kMuted.opacity(0.7) : st.fg)
                .frame(width: 50, alignment: .leading)
            Text(item.title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(done ? kMuted : kText)
                .lineLimit(1)
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 10).padding(.vertical, 5)
        .background(RoundedRectangle(cornerRadius: 9).fill(done ? Color.white.opacity(0.04) : kindFill(st.bg, mode)))
        .overlay(RoundedRectangle(cornerRadius: 9).stroke(isNext ? kGreenHi : Color.clear, lineWidth: 1.5))
    }
}

struct ProgramTodayView: View {
    @Environment(\.widgetFamily) var family
    let entry: ProgramEntry

    var body: some View {
        content.containerBackground(for: .widget) { WidgetBackground() }
    }

    var items: [XItem] { entry.day?.items ?? [] }
    var nowStr: String { entry.tomorrow ? "00:00" : hhmm(entry.date) }   // yarın gösteriliyorsa hepsi "gelecek"
    var heading: String { entry.tomorrow ? "YARININ PROGRAMI" : "BUGÜNÜN PROGRAMI" }
    var nextIdx: Int? { items.firstIndex { !$0.time.isEmpty && $0.time >= nowStr } }

    func isDone(_ i: Int) -> Bool {
        let t = items[i].time
        return !t.isEmpty && t < nowStr
    }

    /// Görünecek satırlar: sıradakinden başlar; yeterli satır kalmadıysa geriye doğru doldurur.
    func window(_ cap: Int) -> [Int] {
        guard !items.isEmpty else { return [] }
        let start = max(0, min(nextIdx ?? items.count, items.count - cap))
        return Array(start..<min(items.count, start + cap))
    }

    @ViewBuilder var content: some View {
        if let day = entry.day, !items.isEmpty {
            switch family {
            case .systemSmall: small(day)
            case .systemLarge: list(day, cap: 9)
            default: list(day, cap: 4)
            }
        } else {
            VStack(alignment: .leading, spacing: 6) {
                SectionTitle(text: heading)
                Spacer()
                Text(entry.hasData ? "Bugün için program eklenmedi." : "MediaStaffKS uygulamasını bir kez aç.")
                    .font(.system(size: 12)).foregroundColor(kMuted)
                Spacer()
            }
        }
    }

    func list(_ day: XDay, cap: Int) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                SectionTitle(text: heading)
                Spacer()
                Text(day.subtitle).font(.system(size: 11, weight: .semibold)).foregroundColor(kText).lineLimit(1)
            }
            ForEach(window(cap), id: \.self) { i in
                ItemRow(item: items[i], done: isDone(i), isNext: nextIdx == i)
            }
            Spacer(minLength: 0)
        }
    }

    func small(_ day: XDay) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            SectionTitle(text: entry.tomorrow ? "YARIN" : (nextIdx == nil ? "BUGÜN" : "SIRADAKİ"))
            if let i = nextIdx ?? items.indices.last {
                let it = items[i]
                let st = kindStyle(it.kind)
                Text(it.time.isEmpty ? "Gün boyu" : it.time)
                    .font(.system(size: 26, weight: .bold)).foregroundColor(st.fg)
                Text(it.title).font(.system(size: 14, weight: .semibold)).foregroundColor(kText).lineLimit(2)
                Spacer(minLength: 0)
                if let n = nextIdx, n + 1 < items.count {
                    Text("Sonra: \(items[n + 1].time) \(items[n + 1].title)")
                        .font(.system(size: 10)).foregroundColor(kMuted).lineLimit(1)
                } else {
                    Text("Bugünün programı bitti").font(.system(size: 10)).foregroundColor(kMuted)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct ProgramTodayWidget: Widget {
    let kind = "ProgramToday"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: ProgramTodayProvider()) { entry in
            ProgramTodayView(entry: entry)
        }
        .configurationDisplayName("Bugünün programı")
        .description("Bugünün antrenman, yemek ve maç programı; sıradaki satır vurgulanır.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}

// MARK: - Haftalık program

struct WeekEntry: TimelineEntry {
    let date: Date
    let days: [XDay]
    let hasData: Bool
}

struct ProgramWeekProvider: TimelineProvider {
    func placeholder(in context: Context) -> WeekEntry { WeekEntry(date: Date(), days: [], hasData: false) }

    func make() -> WeekEntry {
        let x = Store.read("extra.json", as: XData.self)
        let today = isoString(Date())
        let days = (x?.program ?? []).filter { $0.date >= today }
        return WeekEntry(date: Date(), days: days, hasData: x != nil)
    }

    func getSnapshot(in context: Context, completion: @escaping (WeekEntry) -> Void) { completion(make()) }

    func getTimeline(in context: Context, completion: @escaping (Timeline<WeekEntry>) -> Void) {
        completion(Timeline(entries: [make()], policy: .after(Date().addingTimeInterval(30 * 60))))
    }
}

struct Pill: View {
    let text: String
    let kind: String
    @Environment(\.widgetRenderingMode) var mode
    var body: some View {
        let st = kindStyle(kind)
        Text(text)
            .font(.system(size: 10, weight: .semibold))
            .foregroundColor(st.fg)
            .lineLimit(1)
            .padding(.horizontal, 7).padding(.vertical, 3)
            .background(kindFill(st.bg, mode))
            .clipShape(Capsule())
    }
}

func pillText(_ it: XItem) -> String {
    switch it.kind {
    case "off": return "İZİN"
    case "training": return "\(it.time) Antrenman"
    case "meeting": return "\(it.time) Toplantı"
    case "camp": return "\(it.time) Kamp"
    case "match":
        let opp = it.title.components(separatedBy: " - ").last ?? it.title
        return "\(it.time) \(opp)"
    default: return "\(it.time) \(it.title)"
    }
}

struct ProgramWeekView: View {
    @Environment(\.widgetFamily) var family
    let entry: WeekEntry

    var body: some View {
        content.containerBackground(for: .widget) { WidgetBackground() }
    }

    @ViewBuilder var content: some View {
        let cap = family == .systemLarge ? 7 : 3
        if entry.days.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                SectionTitle(text: "HAFTALIK PROGRAM")
                Spacer()
                Text(entry.hasData ? "Yaklaşan program yok." : "MediaStaffKS uygulamasını bir kez aç.")
                    .font(.system(size: 12)).foregroundColor(kMuted)
                Spacer()
            }
        } else {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    SectionTitle(text: "HAFTALIK PROGRAM")
                    Spacer()
                    Text(entry.days.first?.subtitle ?? "").font(.system(size: 11, weight: .semibold))
                        .foregroundColor(kText).lineLimit(1)
                }
                ForEach(Array(entry.days.prefix(cap))) { day in
                    row(day)
                }
                Spacer(minLength: 0)
            }
        }
    }

    func row(_ day: XDay) -> some View {
        let d = isoDate(day.date) ?? Date()
        let isToday = day.date == isoString(entry.date)
        let key = day.items.filter { ["training", "match", "meeting", "camp", "off"].contains($0.kind) }
        return HStack(spacing: 8) {
            Text(trFormat(d, "EEE d MMM"))
                .font(.system(size: 11, weight: .bold))
                .foregroundColor(isToday ? kGreenHi : kText)
                .frame(width: 68, alignment: .leading)
            ForEach(key) { Pill(text: pillText($0), kind: $0.kind) }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 8).padding(.vertical, 6)
        .background(RoundedRectangle(cornerRadius: 9).fill(Color.white.opacity(0.04)))
        .overlay(RoundedRectangle(cornerRadius: 9).stroke(isToday ? kGreenHi : Color.clear, lineWidth: 1.2))
    }
}

struct ProgramWeekWidget: Widget {
    let kind = "ProgramWeek"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: ProgramWeekProvider()) { entry in
            ProgramWeekView(entry: entry)
        }
        .configurationDisplayName("Haftalık program")
        .description("Önümüzdeki günlerin antrenman, toplantı ve maç saatleri.")
        .supportedFamilies([.systemMedium, .systemLarge])
    }
}
