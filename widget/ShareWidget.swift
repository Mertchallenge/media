// "Paylaşım takibi" widget'ı. Veri: share.json
import WidgetKit
import SwiftUI
import AppKit

struct ShareEntry: TimelineEntry {
    let date: Date
    let data: WData?
}

struct ShareProvider: TimelineProvider {
    func placeholder(in context: Context) -> ShareEntry { ShareEntry(date: Date(), data: nil) }

    func getSnapshot(in context: Context, completion: @escaping (ShareEntry) -> Void) {
        completion(ShareEntry(date: Date(), data: Store.read("share.json", as: WData.self)))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<ShareEntry>) -> Void) {
        let entry = ShareEntry(date: Date(), data: Store.read("share.json", as: WData.self))
        completion(Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(15 * 60))))
    }
}

struct FaceView: View {
    let player: WPlayer
    let size: CGFloat

    var body: some View {
        VStack(spacing: 3) {
            ImageB64(b64: player.face, fallback: player.first, size: size)
            Text(player.first)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(kMuted)
                .lineLimit(1)
        }
        .frame(width: size + 10)
    }
}

struct NeverChip: View {
    let never: Int
    var body: some View {
        if never > 0 {
            Text("Son 7 günde paylaşılmayan: \(never) oyuncu")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(kAmber)
                .padding(.horizontal, 10).padding(.vertical, 4)
                .background(kAmber.opacity(0.15))
                .clipShape(Capsule())
        } else {
            Text("Son 7 günde herkes paylaşıldı")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(kGreenHi)
                .padding(.horizontal, 10).padding(.vertical, 4)
                .background(kGreen.opacity(0.18))
                .clipShape(Capsule())
        }
    }
}

struct HeaderView: View {
    let title: String
    let trailing: String
    var body: some View {
        HStack {
            SectionTitle(text: title)
            Spacer()
            Text(trailing)
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(kText)
        }
    }
}

struct ShareWidgetView: View {
    @Environment(\.widgetFamily) var family
    let entry: ShareEntry

    var body: some View {
        content.containerBackground(for: .widget) { WidgetBackground() }
    }

    @ViewBuilder var content: some View {
        if let data = entry.data, let last = data.last {
            switch family {
            case .systemSmall: small(data, last)
            case .systemLarge: large(data, last)
            default: medium(data, last)
            }
        } else {
            VStack(alignment: .leading, spacing: 6) {
                SectionTitle(text: "PAYLAŞIM TAKİBİ")
                Spacer()
                Text(entry.data == nil ? "MediaStaffKS uygulamasını bir kez aç." : "Henüz paylaşım kaydı yok.")
                    .font(.system(size: 12)).foregroundColor(kMuted)
                Spacer()
            }
        }
    }

    func small(_ d: WData, _ last: WLast) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            SectionTitle(text: "PAYLAŞIM TAKİBİ")
            Text("Son paylaşım").font(.system(size: 11)).foregroundColor(kMuted)
            Text(last.date).font(.system(size: 17, weight: .bold)).foregroundColor(kText)
            Text("\(last.count) oyuncu").font(.system(size: 13)).foregroundColor(kText)
            Spacer(minLength: 0)
            Text(d.never > 0 ? "\(d.never) oyuncu 7 gündür paylaşılmadı" : "Herkes paylaşıldı")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(d.never > 0 ? kAmber : kGreenHi)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    func medium(_ d: WData, _ last: WLast) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HeaderView(title: "PAYLAŞIM TAKİBİ", trailing: "Son paylaşım · \(last.date) · \(last.count) oyuncu")
            HStack(alignment: .top, spacing: 2) {
                ForEach(last.players.prefix(6)) { FaceView(player: $0, size: 38) }
                Spacer(minLength: 0)
            }
            Spacer(minLength: 0)
            NeverChip(never: d.never)
        }
    }

    func large(_ d: WData, _ last: WLast) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HeaderView(title: "PAYLAŞIM TAKİBİ", trailing: "Son paylaşım · \(last.date) · \(last.count) oyuncu")
            HStack(alignment: .top, spacing: 2) {
                ForEach(last.players.prefix(7)) { FaceView(player: $0, size: 38) }
                Spacer(minLength: 0)
            }
            NeverChip(never: d.never)
            Text("SIRASI GELENLER")
                .font(.system(size: 10, weight: .bold)).tracking(0.8).foregroundColor(kMuted)
            ForEach(d.waiting.prefix(6)) { w in
                HStack {
                    Text(w.name).font(.system(size: 13, weight: .medium)).foregroundColor(kText).lineLimit(1)
                    Spacer()
                    Text(w.days == nil ? "hiç paylaşılmadı" : "\(w.days!) gün önce")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(w.days == nil ? kAmber : kMuted)
                }
            }
            Spacer(minLength: 0)
        }
    }
}

struct ShareTrackingWidget: Widget {
    let kind = "ShareTracking"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: ShareProvider()) { entry in
            ShareWidgetView(entry: entry)
        }
        .configurationDisplayName("Paylaşım takibi")
        .description("Son paylaşılan oyuncular ve 7 gündür paylaşılmayanlar.")
        .supportedFamilies([.systemSmall, .systemMedium, .systemLarge])
    }
}
