// "Bugünün programı" ve "Haftalık program" widget'ları. Veri: extra.json
import WidgetKit
import SwiftUI
import AppKit

// MARK: - Bugünün programı

struct ProgramEntry: TimelineEntry {
    let date: Date
    let day: XDay?
    let hasData: Bool
}

func programDay(_ x: XData?, _ date: Date) -> XDay? {
    let iso = isoString(date)
    return x?.program.first { $0.date == iso }
}

struct ProgramTodayProvider: TimelineProvider {
    func placeholder(in context: Context) -> ProgramEntry { ProgramEntry(date: Date(), day: nil, hasData: false) }

    func getSnapshot(in context: Context, completion: @escaping (ProgramEntry) -> Void) {
        let x = Store.read("extra.json", as: XData.self)
        completion(ProgramEntry(date: Date(), day: programDay(x, Date()), hasData: x != nil))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<ProgramEntry>) -> Void) {
        let x = Store.read("extra.json", as: XData.self)
        let now = Date()
        let day = programDay(x, now)
        var entries = [ProgramEntry(date: now, day: day, hasData: x != nil)]
        if let day = day {
            for item in day.items {
                if let t = timeToday(item.time, now), t > now {
                    entries.append(ProgramEntry(date: t, day: day, hasData: true))   // sıradaki satır tam saatinde güncellenir
                }
            }
        }
        completion(Timeline(entries: entries, policy: .after(now.addingTimeInterval(30 * 60))))
    }
}

struct ItemRow: View {
    let item: XItem
    let done: Bool
    let isNext: Bool

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
        .background(RoundedRectangle(cornerRadius: 9).fill(done ? Color.white.opacity(0.04) : st.bg))
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
    var nowStr: String { hhmm(entry.date) }
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
                SectionTitle(text: "BUGÜNÜN PROGRAMI")
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
                SectionTitle(text: "BUGÜNÜN PROGRAMI")
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
            SectionTitle(text: nextIdx == nil ? "BUGÜN" : "SIRADAKİ")
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
    var body: some View {
        let st = kindStyle(kind)
        Text(text)
            .font(.system(size: 10, weight: .semibold))
            .foregroundColor(st.fg)
            .lineLimit(1)
            .padding(.horizontal, 7).padding(.vertical, 3)
            .background(st.bg)
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
