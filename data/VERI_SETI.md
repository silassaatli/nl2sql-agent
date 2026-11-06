# Veri Seti Dokümantasyonu: Bankacılık / Finans Senaryosu

Proje, bir bankanın **ürün ve hizmet satış verisi** üzerinde çalışır. Veri **sentetik (uydurma) ama sabittir**: gerçek müşteri verisi, kişisel veri veya kurumsal sistem bağlantısı içermez.
Veri `data/csv/` klasöründeki 4 CSV dosyasında durur ve değişmez, bu sayede testlerin beklenen sonuçları her zaman aynı kalır.

## Kurulum

```bash
python setup_db.py
```

Komut `data/csv/` içindeki dosyaları okuyup `data/nl2sql.db` dosyasını **sıfırdan** oluşturur (varsa önce siler).
Yüklemeden sonra veri kalitesi kontrolleri çalışır: yabancı anahtar ihlali, tarih aralığı dışında işlem ve kalemsiz işlem olmamalıdır.
Sadece Python standart kütüphanesi kullanılır.

## Senaryo: tablolar finans dünyasında ne anlama geliyor?

Tablo ve sütun adları ödevde tanımlanan şemayla **birebir aynıdır**. Böylece ödevdeki 16 test ve metrik tanımları değişmeden geçerli kalır. Sadece içerik bankacılığa uyarlanmıştır.

| Tablo | Finans karşılığı |
|---|---|
| Customers | Banka müşterileri: bireysel müşteriler, KOBİ'ler ve kurumsal firmalar |
| Products | Bankanın sattığı ürün ve hizmetler: kredi tahsis ücretleri, kart ücretleri, sigorta poliçeleri, yatırım/döviz komisyonları, nakit yönetimi hizmetleri |
| Orders | Müşterinin bankayla yaptığı satış işlemi (bir işlemde birden fazla ürün olabilir) |
| OrderItems | İşlemdeki her ürün satırı: adet (`Quantity`) ve uygulanan fiyat (`UnitPrice`) |

**Ciro = bankanın ürün/hizmet geliri** (ücret, komisyon, prim): `SUM(Quantity * UnitPrice)`.

## Tablolar ve ilişkiler

```
Customers (1) ──< Orders (1) ──< OrderItems >── (1) Products
```

| Tablo | Satır | Sütunlar | Anahtarlar |
|---|---|---|---|
| Customers | 200 | CustomerID INTEGER, Name TEXT, City TEXT, Segment TEXT | PK: CustomerID |
| Products | 32 | ProductID INTEGER, ProductName TEXT, Category TEXT, Price REAL | PK: ProductID |
| Orders | 2500 | OrderID INTEGER, CustomerID INTEGER, OrderDate TEXT | PK: OrderID · FK: CustomerID → Customers |
| OrderItems | 5174 | OrderItemID INTEGER, OrderID INTEGER, ProductID INTEGER, Quantity INTEGER, UnitPrice REAL | PK: OrderItemID · FK: OrderID → Orders, ProductID → Products |

## Ürün kategorileri (6)

| Kategori | Örnek ürünler |
|---|---|
| Kredi Ürünleri | İhtiyaç / Konut / Taşıt / Ticari Kredi Tahsis Ücreti, Teminat Mektubu Komisyonu, Rotatif Kredi Komisyonu |
| Kart ve Ödeme | Kredi Kartı Yıllık Ücreti, Şirket Kredi Kartı, POS Cihazı Yıllık Kirası, Sanal POS Paketi, Fatura Ödeme Talimatı |
| Sigorta | Kasko, Konut Sigortası, DASK, Tamamlayıcı Sağlık, Hayat, İşyeri, Grup Sağlık Sigortası (kişi başı) |
| Yatırım | Hisse Senedi Aracılık Paketi, Yatırım Fonu Yönetim Ücreti, Altın Hesabı, Eurobond Aracılık, Portföy Yönetimi |
| Döviz ve Hazine | Döviz Alım-Satım, Forward, Swap, Akreditif Komisyonu |
| Nakit Yönetimi | Hesap İşletim Paketi, Havale/EFT Paketi, Toplu Maaş Ödeme, Kurumsal Ödeme API, Doğrudan Borçlandırma |

## Veri özellikleri

- **Segment:** Bireysel (121), KOBİ (63), Kurumsal (16). Bireysel müşteriler kişi adı, KOBİ'ler "Ltd. Şti.", Kurumsal müşteriler "A.Ş." ile biten şirket adı taşır.
- **Segmente uygun ürün:** Her müşteri sadece kendi segmentine uygun ürünleri alır. Örneğin bireysel müşteri ticari kredi veya swap almaz, swap ve ödeme API'si yalnızca kurumsal müşterilere satılır.
- **City:** 13 Türkiye şehri (İstanbul, Ankara, İzmir, Bursa, Antalya, Kocaeli, Adana, Konya, Gaziantep, Kayseri, Eskişehir, Trabzon, Samsun).
- **OrderDate:** 2025-07-01 ile 2026-06-30 arası, `YYYY-MM-DD` formatında (saat bilgisi yok). Kasım ve Aralık daha yoğun.
- **Price ve UnitPrice:** `Price` ürünün liste fiyatıdır (tarife ücreti). `UnitPrice` müşteriye uygulanan fiyattır: bireyselde %90–%105, KOBİ'de %85–%100, kurumsalda %75–%98 (büyük müşteriye özel fiyatlama). **Ciro her zaman UnitPrice üzerinden hesaplanır.**
- **Quantity:** Bireyselde genellikle 1, KOBİ'de 1–5, kurumsalda 1–12. "Grup Sağlık Sigortası (kişi başı)" için adet sigortalanan çalışan sayısıdır (3–20).
- **İşlemi olmayan müşteriler:** 12 müşterinin bilerek hiç işlemi yoktur (test 05 için).

## Metrik tanımları (ödevden)

| Metrik | Tanım | Finans yorumu |
|---|---|---|
| Ciro | `SUM(Quantity * UnitPrice)`, OrderItems üzerinden | Ürün/hizmet geliri |
| Sipariş adedi | `COUNT(DISTINCT OrderID)` | İşlem sayısı |
| Aktif müşteri | 2026-04-02 – 2026-06-30 arasında en az bir işlemi olan müşteri | Son 90 günde işlem yapan müşteri |
| Kategori ortalaması | Kategori bazında `AVG(Quantity * UnitPrice)` | Ürün grubu başına ortalama satır geliri |

Referans tarih: **2026-06-30**.

## Veri nasıl üretildi?

Öğretici yalnızca çalışılacak sektörü (bankacılık) belirledi; veri seti ve yükleme betiği (`setup_db.py`) ekip tarafından
hazırlandı. Veri, ödevdeki şemaya ve bankacılık senaryosuna uygun olarak bir Python betiğiyle (Claude yardımıyla yazıldı)
bir kez üretildi ve CSV olarak donduruldu. Üretim betiği repoda değildir.
Teslimde kullanılan veri her zaman bu CSV dosyalarıdır. Veri değiştirilirse test 01–08'in beklenen sonuçları yeniden hesaplanmalıdır.
