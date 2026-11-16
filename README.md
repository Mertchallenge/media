# MediaStaffKS

Kocaelispor Medya Departmanı masaüstü uygulaması (PyQt6).

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
