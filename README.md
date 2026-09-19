# Hair Transplant Tracker

Bu repository, klinik içi kullanım için **saç ekimi vaka ve prim takibi** yapan bir sistemin çalışan dikey dilimini içerir.

> ⚠️ **Durum**: Bu sürüm production-ready değildir. Güvenlik sertleştirmesi, kapsamlı mobil ekranlar, operasyonel izleme ve ileri testler tamamlanmadan canlıya alınmamalıdır.

## Teknoloji

- **Mobil**: Flutter (Android odaklı)
- **Backend API**: FastAPI (Python)
- **Veritabanı**: PostgreSQL
- **Migration**: Alembic
- **Dağıtım**: Docker Compose
- **Ağ erişimi**: Tailscale (internetten direkt erişim yok)

## Mevcut Dikey Dilim Kapsamı

Tamamlanan ilk hedefler:

1. Login
2. Role-based authorization
3. Admin vaka CRUD
4. Viewer’ın sadece mevcut ayı görebilmesi
5. Personel seçimi
6. Multiplier hesaplama
7. İki dizimci için prim hesaplama
8. PostgreSQL + migration + Docker Compose
9. Testler
10. PDF aylık rapor çıktısı

## Proje Yapısı

```
/backend
  /app
    /api
    /core
    /db
    /models
    /repositories
    /schemas
    /services
    /tests
  /alembic
/mobile
  /lib
```

## Yetki Modeli

### ADMIN
- Tüm endpoint’lere erişebilir
- Vaka/personel/prim kuralı yönetir
- Rapor ve PDF alır

### VIEWER
- Login olabilir
- Sadece `/cases` ve `/cases/{id}` ile **içinde bulunulan ay** verisini görebilir
- Personel, prim, rapor endpoint’lerine erişemez
- Geçmiş ay sorgusu backend tarafından 403 ile reddedilir

## Vaka ve Çarpan Kuralları

- Ekim türü enum olarak tutulur, mobilde Türkçe karşılık gösterilir
- Varsayılan çarpan:
  - Sakal/Kaş: `0.5`
  - Diğer türler: `1.0`
- Geçerli çarpanlar: `0.5`, `1.0`
- Geçersiz çarpan backend’de reddedilir
- Aynı personelin tek vakada birden fazla role atanması engellenir

## Prim Mimarisi (Seçilen Yaklaşım)

Bu implementasyonda **snapshot yaklaşımı** kullanıldı:

- Vaka oluşturma/güncelleme anında `case_bonus_items` tablosuna prim kalemleri yazılır.
- Sonradan bonus_rule değişse bile eski vaka hesapları bozulmaz.

## Personel ve Hassas Veri

- `passport_number` verisi düz metin tutulmaz; uygulama katmanında encode edilerek saklanır
- Admin listesinde pasaport sadece maskeli gösterilir
- Viewer personel endpoint’ine erişemez
- Pasif personel yeni vakaya atanamaz

## API Endpointleri

- `POST /auth/login`
- `GET /auth/me`
- `GET /cases`
- `POST /cases`
- `GET /cases/{id}`
- `PUT /cases/{id}`
- `DELETE /cases/{id}`
- `GET /personnel`
- `POST /personnel`
- `PUT /personnel/{id}`
- `PATCH /personnel/{id}/status`
- `GET /bonus-rules`
- `POST /bonus-rules`
- `PUT /bonus-rules/{id}`
- `GET /reports/monthly`
- `GET /reports/personnel`
- `GET /reports/monthly/pdf`

## Veritabanı Tabloları

- `users`
- `personnel`
- `cases`
- `bonus_rules`
- `case_bonus_items`
- `audit_logs`

Öne çıkan kısıtlar:
- `cases.case_number` unique
- `cases.patient_name` nullable
- `cases.multiplier` sadece `0.5/1.0`
- `cases.graft_count >= 0`
- `personnel.full_name` zorunlu

## Local Geliştirme

## 1) Backend kurulumu

```bash
cd /home/runner/work/hair-transplant-tracker/hair-transplant-tracker/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2) Ortam değişkenleri

```bash
cp /home/runner/work/hair-transplant-tracker/hair-transplant-tracker/.env.example \
   /home/runner/work/hair-transplant-tracker/hair-transplant-tracker/.env
```

`.env` dosyasını kendi secret’larınızla doldurun.

## 3) Migration

```bash
cd /home/runner/work/hair-transplant-tracker/hair-transplant-tracker/backend
alembic -c alembic.ini upgrade head
```

## 4) Backend çalıştırma

```bash
cd /home/runner/work/hair-transplant-tracker/hair-transplant-tracker/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 5) Flutter Android çalıştırma

```bash
cd /home/runner/work/hair-transplant-tracker/hair-transplant-tracker/mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://<tailscale-ip>:8000
```

## Docker Compose ile Çalıştırma

```bash
cd /home/runner/work/hair-transplant-tracker/hair-transplant-tracker
docker compose up --build
```

Servisler:
- `postgres`
- `migrate`
- `backend`

## TrueNAS Notları

- TrueNAS üzerinde Compose stack olarak deploy edin
- Backend URL’si Tailscale IP veya MagicDNS ile kullanılmalı
- Router/NAT üzerinden internet publish etmeyin
- Healthcheck’ler compose içinde tanımlıdır

## Tailscale Kurulumu ve ACL Önerileri

- Android cihazlar Tailscale ağına dahil olmalı
- ACL ile sadece klinik cihaz grubuna backend erişimi açın
- Örnek yaklaşım:
  - `tag:clinic-android` -> backend:8000 allow
  - Diğer tüm kaynaklardan deny

## Güvenlik

- Şifreler hashlenir
- JWT ile kimlik doğrulama yapılır
- Role-based authorization API seviyesinde uygulanır
- CORS explicit origin listesiyle kısıtlanır
- Secret’lar env üzerinden alınır
- `.env` commit edilmemelidir
- Gerçek hasta/personel verisi repo içinde tutulmamalıdır

## Admin Kullanıcısı

İlk açılışta seed edilen varsayılan kullanıcılar:
- `admin / admin123`
- `viewer / viewer123`

> İlk kurulum sonrası mutlaka değiştirin.

## PostgreSQL Yedekleme

Örnek:

```bash
docker exec -t <postgres-container> pg_dump -U hair_user hair_tracker > backup.sql
```

Geri yükleme:

```bash
cat backup.sql | docker exec -i <postgres-container> psql -U hair_user -d hair_tracker
```

## Testler

```bash
cd /home/runner/work/hair-transplant-tracker/hair-transplant-tracker/backend
pytest
```

Eklenen test kapsamı:
- Admin login olabilir
- Viewer login olabilir
- Viewer vaka ekleyemez
- Viewer vaka silemez
- Viewer yalnızca mevcut ayı görür
- Viewer geçmiş ay query erişimi alamaz
- Viewer personnel endpoint’ine erişemez
- Viewer passport number göremez
- Multiplier default kuralları
- Geçersiz multiplier reddi
- İki dizimci için ayrı prim hesaplama
- Ekimci + dizimci primleri
- Inactive personnel yeni vakada seçilemez
- PDF raporu üretilebilir

## Oluşturulan Mimari Özeti

- `api`: endpoint katmanı
- `services`: multiplier, prim, pdf, passport yardımcı servisleri
- `repositories`: vaka veri erişim katmanı
- `models/schemas`: DB + request/response modelleri
- `tests`: rol, çarpan, prim ve rapor odaklı testler
- `mobile`: login + role tabanlı başlangıç ekranları, Türkçe locale altyapısı

## TODO

- Flutter tarafında tam ADMIN ekran seti (CRUD formlar, rapor filtreleri, bonus yönetimi)
- Flutter tarafında VIEWER için detay ekranını daha zengin hale getirme
- Passport için güçlü kriptografik şifreleme (KMS veya field-level crypto)
- Token yenileme, session yönetimi ve logout invalidation
- Daha geniş audit logging
- Rate limiting ve brute-force koruması
- CI/CD pipeline ve güvenlik taramalarının otomasyonu
- Üretim konfigürasyonunda TLS terminasyonu ve reverse proxy
