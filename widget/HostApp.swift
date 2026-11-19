// Widget'ı taşıyan küçük ana uygulama.
//  - Widget'a tıklanınca macOS bu uygulamayı açar → burada MediaStaffKS.app'i açıp kendini kapatır.
//  - "--reload" ile açılırsa widget'ları hemen yeniletip kapanır (ana uygulama veriyi yazınca çağırır).
//  - Kurulum sırasında "--setup" ile açılırsa yalnızca kısa bir bilgi penceresi gösterir.
import AppKit
import WidgetKit

final class HostDelegate: NSObject, NSApplicationDelegate {
    let setupMode = CommandLine.arguments.contains("--setup")
    let reloadMode = CommandLine.arguments.contains("--reload")

    func applicationDidFinishLaunching(_ notification: Notification) {
        if setupMode {
            NSApp.activate(ignoringOtherApps: true)
            let alert = NSAlert()
            alert.messageText = "MediaStaffKS widget'ı kuruldu"
            alert.informativeText = "Masaüstüne sağ tıkla → \"Widget'ları Düzenle\" → \"MediaStaffKS\" → istediğin widget'ı "
                + "(Paylaşım takibi, Bugünün programı, Haftalık program, Sıradaki maç, Doğum günleri) masaüstüne sürükle. "
                + "Widget'a tıklayınca MediaStaffKS uygulaması açılır."
            alert.addButton(withTitle: "Tamam")
            alert.runModal()
            NSApp.terminate(nil)
            return
        }
        if reloadMode {
            WidgetCenter.shared.reloadAllTimelines()
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { NSApp.terminate(nil) }
            return
        }
        openMainApp()
        DispatchQueue.main.asyncAfter(deadline: .now() + 6) { NSApp.terminate(nil) }   // güvenlik: takılırsa kapan
    }

    func openMainApp() {
        let ws = NSWorkspace.shared
        var url = ws.urlForApplication(withBundleIdentifier: "tr.kocaelispor.mediastaffks")
        if url == nil {
            for path in ["/Applications/MediaStaffKS.app", NSHomeDirectory() + "/Applications/MediaStaffKS.app"]
            where FileManager.default.fileExists(atPath: path) {
                url = URL(fileURLWithPath: path)
                break
            }
        }
        guard let appURL = url else {
            NSApp.terminate(nil)
            return
        }
        let config = NSWorkspace.OpenConfiguration()
        config.activates = true
        ws.openApplication(at: appURL, configuration: config) { _, _ in
            DispatchQueue.main.async { NSApp.terminate(nil) }
        }
    }
}

let app = NSApplication.shared
let delegate = HostDelegate()
app.delegate = delegate
app.setActivationPolicy(delegate.setupMode ? .regular : .accessory)   // widget tıklamasında Dock'ta zıplamasın
app.run()
