// "Sıradaki maç" ve "Doğum günleri" widget'ları. Veri: extra.json
import WidgetKit
import SwiftUI
import AppKit

// MARK: - Sıradaki maç

struct MatchEntry: TimelineEntry {
    let date: Date
    let fixture: XFixture?
    let clubLogo: String
    let hasData: Bool
}

struct NextMatchProvider: TimelineProvider {
    func placeholder(in context: Context) -> MatchEntry { MatchEntry(date: Date(), fixture: nil, clubLogo: "", hasData: false) }

    func make() -> MatchEntry {
        let x = Store.read("extra.json", as: XData.self)
        let today = isoString(Date())
        let fx = x?.fixtures.first { $0.date >= today }
        return MatchEntry(date: Date(), fixture: fx, clubLogo: x?.clubLogo ?? "", hasData: x != nil)
    }

    func getSnapshot(in context: Context, completion: @escaping (MatchEntry) -> Void) { completion(make()) }

    func getTimeline(in context: Context, completion: @escaping (Timeline<MatchEntry>) -> Void) {
        completion(Timeline(entries: [make()], policy: .after(Date().addingTimeInterval(30 * 60))))
    }
}

struct NextMatchView: View {
    @Environment(\.widgetFamily) var family
    let entry: MatchEntry

    var body: some View {
        content.containerBackground(for: .widget) { WidgetBackground() }
    }

    func facts(_ fx: XFixture) -> (days: Int, dateText: String, timeText: String) {
        let d = isoDate(fx.date) ?? Date()
        return (daysUntil(d, from: entry.date), trFormat(d, "d MMMM EEEE"), fx.time.isEmpty ? "Saat belli değil" : fx.time)
    }

    @ViewBuilder var content: some View {
        if let fx = entry.fixture {
            let f = facts(fx)
            if family == .systemSmall {
                VStack(alignment: .leading, spacing: 5) {
                    SectionTitle(text: "SIRADAKİ MAÇ")
                    Text(countdownText(f.days)).font(.system(size: 30, weight: .bold)).foregroundColor(kGreenHi)
                    Text(fx.opponent).font(.system(size: 15, weight: .bold)).foregroundColor(kText).lineLimit(1)
                    Text(fx.home ? "İç saha" : "Deplasman").font(.system(size: 11)).foregroundColor(kMuted)
                    Spacer(minLength: 0)
                    Text("\(f.dateText) · \(f.timeText)").font(.system(size: 10)).foregroundColor(kMuted).lineLimit(2)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            } else {
                HStack(spacing: 14) {
                    VStack(alignment: .leading, spacing: 6) {
                        SectionTitle(text: "SIRADAKİ MAÇ")
                        HStack(spacing: 8) {
                            ImageB64(b64: entry.clubLogo, fallback: "K", size: 46, circle: false)
                            Text("vs").font(.system(size: 11)).foregroundColor(kMuted)
                            ImageB64(b64: fx.oppLogo, fallback: fx.opponent, size: 46, circle: false)
                        }
                        Text(fx.opponent).font(.system(size: 15, weight: .bold)).foregroundColor(kText).lineLimit(1)
                        Text(fx.home ? "İç saha" : "Deplasman")
                            .font(.system(size: 11, weight: .semibold)).foregroundColor(kGreenHi)
                    }
                    Spacer(minLength: 0)
                    VStack(alignment: .trailing, spacing: 4) {
                        Text(countdownText(f.days)).font(.system(size: 34, weight: .bold)).foregroundColor(kGreenHi)
                        Text(f.dateText).font(.system(size: 12, weight: .semibold)).foregroundColor(kText)
                        Text(f.timeText).font(.system(size: 12)).foregroundColor(kSoft)
                        if !fx.stadium.isEmpty {
                            Text(fx.stadium).font(.system(size: 10)).foregroundColor(kMuted).lineLimit(1)
                        }
                    }
                }
            }
        } else {
            VStack(alignment: .leading, spacing: 6) {
                SectionTitle(text: "SIRADAKİ MAÇ")
                Spacer()
                Text(entry.hasData ? "Yaklaşan maç yok." : "MediaStaffKS uygulamasını bir kez aç.")
                    .font(.system(size: 12)).foregroundColor(kMuted)
                Spacer()
            }
        }
    }
}

struct NextMatchWidget: Widget {
    let kind = "NextMatch"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: NextMatchProvider()) { entry in
            NextMatchView(entry: entry)
        }
        .configurationDisplayName("Sıradaki maç")
        .description("Rakip, tarih, saat ve kalan gün.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

// MARK: - Doğum günleri

struct BDay: Identifiable {
    let b: XBirthday
    let days: Int                       // kalan gün
    var id: String { b.id }
}

struct BirthdayEntry: TimelineEntry {
    let date: Date
    let items: [BDay]
    let hasData: Bool
}

struct BirthdaysProvider: TimelineProvider {
    func placeholder(in context: Context) -> BirthdayEntry { BirthdayEntry(date: Date(), items: [], hasData: false) }

    func make() -> BirthdayEntry {
        let x = Store.read("extra.json", as: XData.self)
        let now = Date()
        let cal = Calendar.current
        var list: [BDay] = []
        for b in x?.birthdays ?? [] {
            guard var d = isoDate(b.next) else { continue }
            while cal.startOfDay(for: d) < cal.startOfDay(for: now) {       // uygulama açılmadıysa bir sonraki yıla kaydır
                d = cal.date(byAdding: .year, value: 1, to: d) ?? d.addingTimeInterval(365 * 86400)
            }
            list.append(BDay(b: b, days: daysUntil(d, from: now)))
        }
        list.sort { $0.days < $1.days }
        return BirthdayEntry(date: now, items: list, hasData: x != nil)
    }

    func getSnapshot(in context: Context, completion: @escaping (BirthdayEntry) -> Void) { completion(make()) }

    func getTimeline(in context: Context, completion: @escaping (Timeline<BirthdayEntry>) -> Void) {
        completion(Timeline(entries: [make()], policy: .after(Date().addingTimeInterval(60 * 60))))
    }
}

struct BirthdaysView: View {
    @Environment(\.widgetFamily) var family
    let entry: BirthdayEntry

    var body: some View {
        content.containerBackground(for: .widget) { WidgetBackground() }
    }

    func dayChip(_ days: Int) -> some View {
        Text(countdownText(days))
            .font(.system(size: 11, weight: .bold))
            .foregroundColor(days <= 7 ? kGreenHi : kMuted)
            .padding(.horizontal, 8).padding(.vertical, 3)
            .background((days <= 7 ? kGreen.opacity(0.18) : Color.white.opacity(0.06)))
            .clipShape(Capsule())
    }

    @ViewBuilder var content: some View {
        if entry.items.isEmpty {
            VStack(alignment: .leading, spacing: 6) {
                SectionTitle(text: "DOĞUM GÜNLERİ")
                Spacer()
                Text(entry.hasData ? "Doğum günü verisi yok." : "MediaStaffKS uygulamasını bir kez aç.")
                    .font(.system(size: 12)).foregroundColor(kMuted)
                Spacer()
            }
        } else if family == .systemSmall {
            let first = entry.items[0]
            VStack(alignment: .leading, spacing: 5) {
                SectionTitle(text: "DOĞUM GÜNÜ")
                ImageB64(b64: first.b.face, fallback: first.b.first, size: 46)
                Text(first.b.name).font(.system(size: 13, weight: .bold)).foregroundColor(kText).lineLimit(2)
                Spacer(minLength: 0)
                HStack {
                    dayChip(first.days)
                    Text("\(first.b.turning). yaş").font(.system(size: 10)).foregroundColor(kMuted)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        } else if family == .systemMedium {
            VStack(alignment: .leading, spacing: 8) {
                SectionTitle(text: "DOĞUM GÜNLERİ")
                HStack(alignment: .top, spacing: 6) {
                    ForEach(Array(entry.items.prefix(3))) { pair in
                        VStack(spacing: 4) {
                            ImageB64(b64: pair.b.face, fallback: pair.b.first, size: 44)
                            Text(pair.b.first).font(.system(size: 11, weight: .semibold)).foregroundColor(kText).lineLimit(1)
                            dayChip(pair.days)
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
                Spacer(minLength: 0)
            }
        } else {
            VStack(alignment: .leading, spacing: 8) {
                SectionTitle(text: "DOĞUM GÜNLERİ")
                ForEach(Array(entry.items.prefix(6))) { pair in
                    HStack(spacing: 10) {
                        ImageB64(b64: pair.b.face, fallback: pair.b.first, size: 34)
                        VStack(alignment: .leading, spacing: 1) {
                            Text(pair.b.name).font(.system(size: 13, weight: .semibold)).foregroundColor(kText).lineLimit(1)
                            Text("\(pair.b.turning). yaşına giriyor").font(.system(size: 10)).foregroundColor(kMuted)
                        }
                        Spacer()
                        dayChip(pair.days)
                    }
                }
                Spacer(minLength: 0)
            }
        }
    }
}

struct BirthdaysWidget: Widget {
    let kind = "Birthdays"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: BirthdaysProvider()) { entry in
            BirthdaysView(entry: entry)
        }
        .configurationDisplayName("Doğum günleri")
        .description("Kadronun yaklaşan doğum günleri.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}
