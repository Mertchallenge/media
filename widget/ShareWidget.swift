// MediaStaffKS — "Paylaşım takibi" macOS widget'ı (WidgetKit).
// Veriyi MediaStaffKS uygulaması şu dosyaya yazar:
//   ~/Library/Application Support/MediaStaffKS/widget/share.json
import WidgetKit
import SwiftUI
import AppKit

// MARK: - Veri

struct WPlayer: Codable, Identifiable {
    let name: String
    let first: String
    let face: String            // base64 PNG ("" = fotoğraf yok)
    var id: String { name }
}

struct WLast: Codable {
    let date: String
    let count: Int
    let players: [WPlayer]
}

struct WWaiting: Codable, Identifiable {
    let name: String
    let days: Int?              // nil = hiç paylaşılmadı
    var id: String { name }
}

struct WData: Codable {
    let updated: String
    let last: WLast?
    let never: Int
    let waiting: [WWaiting]
}

func realHomePath() -> String {
    if let pw = getpwuid(getuid()), let dir = pw.pointee.pw_dir {
        return String(cString: dir)          // sandbox içinde bile gerçek ev klasörü
    }
    return NSHomeDirectory()
}

func loadData() -> WData? {
    let path = realHomePath() + "/Library/Application Support/MediaStaffKS/widget/share.json"
    guard let raw = FileManager.default.contents(atPath: path) else { return nil }
    return try? JSONDecoder().decode(WData.self, from: raw)
}

// MARK: - Zaman çizelgesi

struct ShareEntry: TimelineEntry {
    let date: Date
    let data: WData?
}

struct ShareProvider: TimelineProvider {
    func placeholder(in context: Context) -> ShareEntry { ShareEntry(date: Date(), data: nil) }

    func getSnapshot(in context: Context, completion: @escaping (ShareEntry) -> Void) {
        completion(ShareEntry(date: Date(), data: loadData()))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<ShareEntry>) -> Void) {
        let entry = ShareEntry(date: Date(), data: loadData())
        completion(Timeline(entries: [entry], policy: .after(Date().addingTimeInterval(15 * 60))))
    }
}

// MARK: - Renkler

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255)
    }
}
let kBg1 = Color(hex: 0x0E1A14)
let kBg2 = Color(hex: 0x0A0E0C)
let kGreen = Color(hex: 0x00A86B)
let kGreenHi = Color(hex: 0x2FD69A)
let kText = Color(hex: 0xE9F2ED)
let kMuted = Color(hex: 0x8CA095)
let kAmber = Color(hex: 0xF2B24A)

// MARK: - Parçalar

struct FaceView: View {
    let player: WPlayer
    let size: CGFloat

    var body: some View {
        VStack(spacing: 3) {
            avatar
                .frame(width: size, height: size)
                .clipShape(Circle())
            Text(player.first)
                .font(.system(size: 10, weight: .medium))
                .foregroundColor(kMuted)
                .lineLimit(1)
        }
        .frame(width: size + 10)
    }

    @ViewBuilder var avatar: some View {
        if !player.face.isEmpty, let data = Data(base64Encoded: player.face), let img = NSImage(data: data) {
            Image(nsImage: img).resizable().scaledToFill()
        } else {
            ZStack {
                kGreen.opacity(0.35)
                Text(String(player.first.prefix(1)))
                    .font(.system(size: size * 0.45, weight: .bold))
                    .foregroundColor(kText)
            }
        }
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
            Text(title)
                .font(.system(size: 10, weight: .bold))
                .tracking(0.8)
                .foregroundColor(kGreenHi)
            Spacer()
            Text(trailing)
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(kText)
        }
    }
}

// MARK: - Ana görünüm

struct ShareWidgetView: View {
    @Environment(\.widgetFamily) var family
    let entry: ShareEntry

    var body: some View {
        content
            .containerBackground(for: .widget) {
                LinearGradient(colors: [kBg1, kBg2], startPoint: .topLeading, endPoint: .bottomTrailing)
            }
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
                Text("PAYLAŞIM TAKİBİ")
                    .font(.system(size: 10, weight: .bold)).tracking(0.8).foregroundColor(kGreenHi)
                Spacer()
                Text(entry.data == nil ? "MediaStaffKS uygulamasını bir kez aç." : "Henüz paylaşım kaydı yok.")
                    .font(.system(size: 12)).foregroundColor(kMuted)
                Spacer()
            }
        }
    }

    func small(_ d: WData, _ last: WLast) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("PAYLAŞIM TAKİBİ")
                .font(.system(size: 10, weight: .bold)).tracking(0.8).foregroundColor(kGreenHi)
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

// MARK: - Widget

@main
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
