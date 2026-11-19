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

- `main.py` içindeki `APP_VERSION` sabiti, uygulamanın şu anki sürümünü tutar.
- Uygulama açılışta GitHub'daki **en son release**'i (`v<sürüm>` etiketi) kontrol eder.
- Daha yeni bir sürüm varsa kullanıcıya sorar; onaylarsa paketlenmiş `.app` sürümünde
  yeni `.app`'i indirip kendini değiştirir ve yeniden başlar. `python3 main.py` ile
  çalıştırılan sürümde ise sadece `main.py` dosyasını indirip üzerine yazar.

## Yeni bir sürüm yayınlamak

1. `main.py` içindeki `APP_VERSION` değerini artır (örn. `"1.0.1"`).
2. Değişiklikleri `main` dalına gönder (push).
3. Yeni bir sürüm etiketi oluştur ve gönder:
   ```
   git tag v1.0.1
   git push origin v1.0.1
   ```
4. GitHub Actions (`.github/workflows/release.yml`) otomatik olarak macOS üzerinde
   `MediaStaffKS.app`'i derler, zip'ler ve bir **Release** olarak yayınlar.
5. Kullanıcılar uygulamayı bir sonraki açılışta otomatik olarak bu sürüme güncelleyecek.

## Not — Gatekeeper uyarısı

Uygulama Apple tarafından imzalanmadığı (ücretli geliştirici hesabı gerektirir) için
ilk kurulumda macOS "tanımlanamayan geliştirici" uyarısı gösterebilir. Kullanıcı
uygulamaya sağ tıklayıp **Aç**'ı seçerek bu uyarıyı bir kerelik geçebilir.
