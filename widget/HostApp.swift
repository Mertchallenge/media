// Widget'ı taşıyan küçük ana uygulama: bir kez açılınca macOS widget'ı tanır.
import AppKit

final class HostDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.activate(ignoringOtherApps: true)
        let alert = NSAlert()
        alert.messageText = "MediaStaffKS widget'ı kuruldu"
        alert.informativeText = "Masaüstüne sağ tıkla → \"Widget'ları Düzenle\" → \"MediaStaffKS\" → istediğin widget'ı "
            + "(Paylaşım takibi, Bugünün programı, Haftalık program, Sıradaki maç, Doğum günleri) masaüstüne sürükle."
        alert.addButton(withTitle: "Tamam")
        alert.runModal()
        NSApp.terminate(nil)
    }
}

let app = NSApplication.shared
let delegate = HostDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
