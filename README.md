# Kaymak Sigorta teklif ve belge yükleme sistemi

## Özellikler
- Müşteri teklif formu: ad, telefon, sigorta türü, plaka, not ve dosya.
- JPG/JPEG/PNG/WEBP/PDF yükleme, 12 MB varsayılan sınır.
- Talepler SQLite veritabanına kaydedilir.
- Yönetim paneli: `/yonetim/giris`
- Panelden belge görüntüleme, talep durumunu değiştirme, müşteriyi arama ve WhatsApp üzerinden cevap taslağı açma.
- WhatsApp üzerinden fotoğraf otomatik gönderme kullanılmaz; dosya siteye yüklenir.

## Yerel test
Python 3.10+ gerekir.
1. `python -m venv .venv`
2. Windows: `.venv\\Scripts\\activate` / macOS/Linux: `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `.env.example` dosyasındaki değerleri ortam değişkeni olarak ayarlayın. `ADMIN_PASSWORD` için güçlü, benzersiz bir şifre kullanın. `DATA_DIR` kalıcı veri klasörünü göstermelidir.
5. `python app.py`
6. Site: `http://127.0.0.1:5000`; yönetim: `http://127.0.0.1:5000/yonetim/giris`

## İnternete yayınlamadan önce
- HTTPS zorunlu olacak şekilde bir Python/Flask hosting platformuna dağıtın.
- `FLASK_SECRET_KEY`, `ADMIN_USER`, `ADMIN_PASSWORD` ve `WHATSAPP_NUMBER` ortam değişkenlerini hosting panelinde ayarlayın.
- Kalıcı disk/volume bağlayın ve `DATA_DIR` değişkenini bu mount noktasına ayarlayın (ör. `/data`); yüklemeler ve SQLite veritabanı aynı kalıcı yerde tutulmalıdır.
- Veritabanı ve yüklemeler için yedekleme, erişim kontrolü, gizlilik/KVKK aydınlatma metni, saklama-silme süresi ve kötü amaçlı dosya taraması planlayın.
- Üretimde `debug=False` tutun ve Flask development server yerine Gunicorn/uygun WSGI sunucusu kullanın.
- Bu taslak tam bir sigorta satış/teklif entegrasyonu değildir; müşteri taleplerini toplar. Poliçe fiyatı veya bağlayıcı teklif üretmez.
- Gerçek yayına almadan önce güvenlik incelemesi yaptırın. Hassas ruhsat görselleri yalnızca yetkili kullanıcıya açık tutulmalıdır.
