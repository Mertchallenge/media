// MediaStaffKS widget'ları — ortak veri modelleri, okuyucular, renkler ve yardımcılar.
import SwiftUI
import AppKit

// MARK: - Paylaşım takibi verisi (share.json)

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

// MARK: - Program / maç / doğum günü verisi (extra.json)

struct XItem: Codable, Identifiable {
    let time: String            // "HH:mm" ya da "" (gün boyu)
    let title: String
    let kind: String            // meal | gym | training | match | meeting | camp | off
    var id: String { time + title }
}

struct XDay: Codable, Identifiable {
    let date: String            // yyyy-MM-dd
    let subtitle: String
    let items: [XItem]
    var id: String { date }
}

struct XFixture: Codable, Identifiable {
    let date: String
    let time: String
    let opponent: String
    let home: Bool
    let stadium: String
    let oppLogo: String
    var id: String { date + opponent }
}

struct XBirthday: Codable, Identifiable {
    let name: String
    let first: String
    let next: String            // bir sonraki doğum günü (yyyy-MM-dd)
    let turning: Int
    let face: String
    var id: String { name }
}

struct XData: Codable {
    let updated: String
    let program: [XDay]
    let clubLogo: String
    let fixtures: [XFixture]
    let birthdays: [XBirthday]
}

// MARK: - Dosya okuma

func realHomePath() -> String {
    if let pw = getpwuid(getuid()), let dir = pw.pointee.pw_dir {
        return String(cString: dir)          // sandbox içinde bile gerçek ev klasörü
    }
    return NSHomeDirectory()
}

enum Store {
    static var dir: String { realHomePath() + "/Library/Application Support/MediaStaffKS/widget/" }

    static func read<T: Decodable>(_ file: String, as type: T.Type) -> T? {
        guard let raw = FileManager.default.contents(atPath: dir + file) else { return nil }
        return try? JSONDecoder().decode(T.self, from: raw)
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
let kSoft = Color(hex: 0xC9D6CE)
let kMuted = Color(hex: 0x8CA095)
let kAmber = Color(hex: 0xF2B24A)

func kindStyle(_ kind: String) -> (fg: Color, bg: Color) {
    switch kind {
    case "training": return (Color(hex: 0xFF7B7F), Color(hex: 0x2E1719))
    case "gym": return (kGreenHi, Color(hex: 0x12291F))
    case "match": return (Color(hex: 0x7FB2FF), Color(hex: 0x152238))
    case "meeting", "camp": return (kAmber, Color(hex: 0x2A2113))
    case "off": return (kGreenHi, Color(hex: 0x0E2A1F))
    default: return (kSoft, Color(hex: 0x1B2420))
    }
}

struct WidgetBackground: View {
    var body: some View {
        LinearGradient(colors: [kBg1, kBg2], startPoint: .topLeading, endPoint: .bottomTrailing)
    }
}

// MARK: - Tarih yardımcıları

func isoString(_ d: Date) -> String {
    let f = DateFormatter()
    f.locale = Locale(identifier: "en_US_POSIX")
    f.dateFormat = "yyyy-MM-dd"
    return f.string(from: d)
}

func isoDate(_ s: String) -> Date? {
    let f = DateFormatter()
    f.locale = Locale(identifier: "en_US_POSIX")
    f.dateFormat = "yyyy-MM-dd"
    return f.date(from: s)
}

func hhmm(_ d: Date) -> String {
    let f = DateFormatter()
    f.locale = Locale(identifier: "en_US_POSIX")
    f.dateFormat = "HH:mm"
    return f.string(from: d)
}

func trFormat(_ d: Date, _ format: String) -> String {
    let f = DateFormatter()
    f.locale = Locale(identifier: "tr_TR")
    f.dateFormat = format
    return f.string(from: d)
}

func timeToday(_ time: String, _ now: Date) -> Date? {
    let parts = time.split(separator: ":")
    guard parts.count == 2, let h = Int(parts[0]), let m = Int(parts[1]) else { return nil }
    return Calendar.current.date(bySettingHour: h, minute: m, second: 0, of: now)
}

func daysUntil(_ target: Date, from now: Date) -> Int {
    let c = Calendar.current
    return c.dateComponents([.day], from: c.startOfDay(for: now), to: c.startOfDay(for: target)).day ?? 0
}

func countdownText(_ days: Int) -> String {
    if days <= 0 { return "Bugün" }
    if days == 1 { return "Yarın" }
    return "\(days) gün"
}

// MARK: - Ortak görünümler

/// Masaüstü widget'ları "vurgulu/renksiz" moda geçince fotoğraflar tek renkli silüete dönüşür; tam renkte kalmasını sağlar.
@ViewBuilder func fullColor(_ img: Image) -> some View {
    #if compiler(>=6.0)
    if #available(macOS 15.0, *) {
        img.widgetAccentedRenderingMode(.fullColor)
    } else {
        img
    }
    #else
    img
    #endif
}

struct ImageB64: View {
    let b64: String
    let fallback: String
    let size: CGFloat
    var circle = true

    var body: some View {
        content
            .frame(width: size, height: size)
            .clipShape(RoundedRectangle(cornerRadius: circle ? size / 2 : 6))
    }

    @ViewBuilder var content: some View {
        if !b64.isEmpty, let data = Data(base64Encoded: b64), let img = NSImage(data: data) {
            fullColor(Image(nsImage: img).resizable()).scaledToFill()
        } else {
            ZStack {
                kGreen.opacity(0.35)
                Text(String(fallback.prefix(1)))
                    .font(.system(size: size * 0.45, weight: .bold))
                    .foregroundColor(kText)
            }
        }
    }
}

struct SectionTitle: View {
    let text: String
    var body: some View {
        Text(text)
            .font(.system(size: 10, weight: .bold))
            .tracking(0.8)
            .foregroundColor(kGreenHi)
    }
}
