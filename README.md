# MediaStaffKS

Kocaelispor Medya Departmanı masaüstü uygulaması (PyQt6).

## Dosyalar

- `main.py` — asıl uygulama (bunu çalıştırırsın: `python3 main.py`).
- `admin.py` — **ayrı, bağımsız** bir Admin Paneli (`python3 admin.py` ile kendi
  penceresinde açılır). Fikstür, kadro, takım logoları ve oyuncu fotoğrafları buradan
  eklenir/düzenlenir/silinir.
- `ks_data.py` — ikisinin de okuyup yazdığı paylaşılan veri katmanı; `main.py` sadece
  okur, `admin.py` hem okur hem yazar.
- `veri.json` — fikstür ve kadro verisinin tutulduğu dosya. İlk çalıştırmada otomatik
  oluşur, elle düzenlenmesi gerekmez (Admin Paneli'ni kullan).

Üçü de (main.py, admin.py, ks_data.py) **aynı klasörde** olmalı.

## Medya bölümü — günlük akış

1. **Ayıklama:** referans + medya klasörünü seç, başlat. Bitince oyuncu klasörlerinin yanında `Rapor.csv` oluşur.
2. **İnceleme:** Eşleşmeyen (KARISIK) ve düşük güvenli fotoğrafları tek tek onayla / düzelt. `Enter` öneriyi onaylar, `1/2/3` aday seçer, `→` atlar, `X` hiçbiri, `Z` geri alır. Onayladığın yüz referansa eklenir (sonraki ayıklamalar daha doğru olur).
3. **Sosyal:** *Sosyal medya* sekmesi oyuncu klasörlerindeki (ya da seçtiğin başka bir klasördeki) fotoğraflardan Story (1080×1920), Gönderi (1080×1350), Kare (1080×1080) üretir ve KSmedya logosunu ekler (`SOSYAL` klasörü). *İçerik dengesi* sekmesi kimin az / hiç çıkmadığını, hangi oyuncunun tek referanslı olduğunu gösterir.
4. **Maçlar → Maç günü listesi:** Her maç için işaretlenebilir kontrol listesi.

Ayarlar `~/.kocaelispor_foto_ayiklama/medya_ayarlar.json` dosyasında tutulur (sosyal medya ayarları, maç günü liste işaretleri).

## Admin Paneli nasıl kullanılır?

Terminalde `python3 admin.py` çalıştır (ya da main.py ile aynı klasörde bir kısayol
oluştur). Dört sekme var:

- **Fikstür**: maç ekle/sil, hücrelere çift tıklayıp tarih/saat/stadyum düzenle.
- **Kadro**: oyuncu ekle/sil, forma no / mevki / doğum tarihi düzenle.
- **Takım Logoları**: her rakip takım için bir görsel seç ya da kaldır.
- **Oyuncu Fotoğrafları**: her oyuncu için bir görsel seç ya da kaldır.

Her sekmede **Kaydet**'e basmayı unutma — kaydedilen veri `veri.json`'a yazılır ve
MediaStaffKS'in bir sonraki açılışında otomatik görünür (uygulama açıksa kapatıp
yeniden açman gerekir).

## Masaüstü uygulaması (.app)

Terminal/VS Code olmadan, Dock'tan açılan gerçek bir Mac uygulaması.

**Mac'inde kurmak (tek komut):** proje klasöründe (main.py'nin olduğu yerde)

```
bash build_mac.sh
```

Bu komut kulüp logosundan ikon üretir, `MediaStaffKS.app` ve `MediaStaffKS-Admin.app` dosyalarını
derler, `/Applications`'a (olmazsa `~/Applications`) kurar ve mevcut `veri.json`, takım logoları ve
oyuncu fotoğraflarını veri klasörüne kopyalar (var olan dosyaların üzerine yazmaz).
İlk derleme birkaç dakika sürer; sonra Launchpad/Spotlight/Dock'tan açarsın.

**Veriler nerede?** `.app` güncellenince silinmesin diye paketin dışında:
`~/Library/Application Support/MediaStaffKS/` (veri.json, `oyuncu_fotograflari/`, `takim_logolari/`).
Ayarlar → Hakkında → *Fotoğraf / veri klasörünü aç* ile Finder'da açılır. Ana uygulama ve Admin
uygulaması aynı klasörü kullanır. `python3 main.py` ile (geliştirme) çalıştırırsan eskisi gibi
script klasörü kullanılır.

**GitHub'dan hazır paket:** `main` dalına push edilince Actions (macOS 14, Apple Silicon)
uygulamayı derler, paketli uygulamayı `--selftest` ile denetler ve geçerse Release yayınlar.
İndirdiğin uygulama imzasız olduğu için ilk açılışta: sağ tık → *Aç* (ya da
`xattr -cr /Applications/MediaStaffKS.app`).

Notlar: yüz tanıma modeli ilk çalıştırmada `~/.insightface` altına indirilir (internet gerekir).
Paket büyüktür (yüzlerce MB; insightface + onnxruntime + Qt WebEngine).

## Otomatik güncelleme nasıl çalışır?

- Paketlenmiş uygulama `launcher.py` ile başlar. `main.py` ve `ks_data.py` paketin içinde durur;
  güncelleme bu iki dosyanın yenisini `~/Library/Application Support/MediaStaffKS/kod/` altına
  indirir ve launcher, paketten **daha yeniyse** onu yükler. Yani `.app` yeniden derlenmez.
- Uygulama açılışta GitHub `main` dalındaki `main.py` içindeki `APP_VERSION`'a bakar. Yerel sürümden
  yüksekse "Yeni sürüm var" penceresi çıkar (`UPDATE_NOTES` metniyle); onaylanırsa indirir, doğrular
  (sözdizimi denetimi), yerine koyar ve yeniden başlar. Ayarlar → Hakkında → *Güncellemeyi denetle*
  elle de kontrol eder.
- Yeni kod açılamazsa launcher paketin kendi sürümüne döner (`.../kod/` silinirse de aynı).
- Yeni bir kütüphane/paketleme değişikliği gerekirse `main.py`'de `REQUIRES_BUNDLE` artırılır;
  eski paket bunu uygulamaz ve "bash build_mac.sh ile yeniden kur" der.
- `python3 main.py` ile çalıştırılan geliştirme sürümü aynı kontrolü yapar ve dosyaların üzerine yazar.

## Yeni bir sürüm yayınlamak

1. `main.py` içinde `APP_VERSION`'ı artır ve `UPDATE_NOTES`'a kısa bir not yaz.
2. `main`'e push et. Uygulamalar bir sonraki açılışta güncellemeyi sunar.
   (Yalnızca `main.py`/`ks_data.py` değişiklikleri için; yeni kütüphane gerekiyorsa `build_mac.sh`.)


## macOS widget'ları

Masaüstüne eklenen gerçek widget'lar (WidgetKit): **Paylaşım takibi**, **Bugünün programı**,
**Haftalık program**, **Sıradaki maç**, **Doğum günleri**. Uygulama verileri
`~/Library/Application Support/MediaStaffKS/widget/` altına (share.json, extra.json) yazar, widget'lar okur.

    bash build_widget.sh      # Xcode Komut Satırı Araçları gerekir (xcode-select --install)

Sonra masaüstüne sağ tık → *Widget'ları Düzenle* → **MediaStaffKS** → istediğin widget.
Widget'lar kendi başlarına tazelenir (program satırı tam saatinde, diğerleri 15–60 dakikada bir);
yeni veri için MediaStaffKS'ı açman yeterli.
`build_widget.sh`'i v1.5.1 sonrası bir kez çalıştırdıysan, uygulamada bir paylaşım kaydettiğinde widget'lar hemen yenilenir
(widget uygulaması arka planda `--reload` ile çalışır).


## iPhone widget'ları (Scriptable)

Aynı beş widget iPhone'da da çalışır. Xcode / geliştirici hesabı gerekmez; ücretsiz **Scriptable**
uygulaması ve iCloud Drive kullanılır.

1. iPhone'a App Store'dan **Scriptable**'ı kur ve bir kez aç (iCloud açık olsun).
2. Mac'te MediaStaffKS'ı aç. Uygulama, `MediaStaffKS.js` betiğini ve verileri
   `iCloud Drive → Scriptable` klasörüne kendiliğinden yazar (`MediaStaffKS-data/share.json`, `extra.json`).
   Betiğin kaynağı `ios/MediaStaffKS.js`; `ks_data.py` içine gömülüdür, güncelleme ile birlikte gelir.
3. iPhone ana ekranına **Scriptable** widget'ı ekle → widget'a dokun (Widget'ı Düzenle):
   *Script* = **MediaStaffKS**, *Parameter* = `program` · `week` · `share` · `match` · `birthdays`.

Veri, Mac'teki uygulama her açılıp yenilendiğinde güncellenir; iPhone widget'ı iOS'un belirlediği
aralıklarla (genelde 15+ dk) tazelenir.
