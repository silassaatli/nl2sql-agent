# NL2SQL Agent: Doğal Dilden SQL'e Kurumsal Analitik Asistanı

Ensight Teknik Staj Ödevi (ENS-AI-001). Türkçe sorulan iş sorularını SQL'e çeviren, sorguyu güvenli şekilde çalıştıran ve sonucu gösteren bir Proof of Concept.
Senaryo: bir bankanın ürün ve hizmet satış verisi (bkz. [data/VERI_SETI.md](data/VERI_SETI.md)).

**Ekip:** _İsim Soyisim_ · _İsim Soyisim_

## Gereksinimler

- Python 3.10+
- [Ollama](https://ollama.com) ve en az 8 GB RAM (model ~4.7 GB)

## Kurulum

```bash
git clone <repo-adresi>
cd nl2sql-agent

python -m venv .venv
# Windows:      .venv\Scripts\activate
# Mac / Linux:  source .venv/bin/activate
pip install -r requirements.txt

ollama pull qwen2.5-coder:7b     # modeli indir (bir kez)
python setup_db.py               # veritabanını sabit CSV'lerden sıfırdan kur + şema bağlamını (data/schema.json) üret
```

## Çalıştırma

```bash
streamlit run app/ui.py          # arayüz
python tests/run_all.py          # 16 testi çalıştır, docs/ altına rapor üret
```

## Proje yapısı

```
config.py            Sabit ayarlar: referans tarih, limitler, model adı
setup_db.py          Veritabanını data/csv/ içindeki sabit veriden kurar, ardından data/schema.json üretir
data/                Veri seti (CSV) ve veri dokümantasyonu
app/schema.py        Şema bağlamı: tablo, sütun, tip, PK/FK → LLM'e verilir
app/llm.py           Prompt + Ollama çağrısı → SQL üretimi
app/semantic.py      Semantik katman: metrik sözlüğü + tarih çözücü (soruya Tarih/Metrik notu ekler)
app/validator.py     SQLGlot ile güvenlik doğrulaması
app/db.py            Salt-okunur bağlantı + authorizer + süre/satır limiti
app/pipeline.py      Uçtan uca akış, hata yönetimi, yeniden deneme, JSON log
app/ui.py            Streamlit arayüzü
tests/               16 test, beklenen sonuçlar, test çalıştırıcı
docs/                Mimari diyagram, test raporu, teknik değerlendirme
logs/                Çalışma logları (queries.jsonl)
```

## Mimari

_TODO: docs/ altındaki diyagramı ekleyin._

soru → LLM (şema + metrikler + tarih kuralları) → doğrulama (SQLGlot) → salt-okunur çalıştırma (authorizer, 500 satır, süre sınırı) → sonuç + JSON log

## Şema bağlamı

_TODO: Şemanın nasıl üretildiği (app/schema.py) ve prompt'a nasıl verildiği._

## Prompt yaklaşımı ve model seçimi

_TODO: Model, parametreler (temperature=0, format=json), prompt içeriği, neden bu model (Türkçe performans, ücretsiz/yerel, donanım)._

## Semantik katman / metrik sözlüğü (bonus)

Ödevin "Şema bağlamı" alanındaki bonus maddesi. Kod: [app/semantic.py](app/semantic.py).
İş dilindeki ifadeler veritabanı karşılıklarına **modelin tahminine bırakılmadan, kodla** çevrilir.

**1. Metrik sözlüğü (`METRICS`).** Her metrik için ad, eş anlamlılar, SQL ifadesi ve not tutulur. Prompt'un metrik bölümü
bu sözlükten üretilir.

| Metrik | Eş anlamlılar | SQL |
|---|---|---|
| Ciro | gelir, en çok satan, en çok satılan | `SUM(oi.Quantity * oi.UnitPrice)` (Products.Price değil) |
| Sipariş adedi | sipariş sayısı | `COUNT(DISTINCT o.OrderID)` |
| Aktif müşteri | — | `COUNT(DISTINCT o.CustomerID)`, 2026-04-02 – 2026-06-30 arasında siparişi olan |
| Ortalama sipariş kalemi tutarı | kategori ortalaması, satır / kalem / satış kalemi tutarı | `AVG(oi.Quantity * oi.UnitPrice)` (AVG(UnitPrice) değil) |

Soruda riskli bir eş anlamlı geçerse (ör. "en çok sat…", "kalem", "satır tutarı") formül ayrıca **Metrik notu** olarak
soruya eklenir. "İşlem tutarı" bilerek eş anlamlı **değildir**: veri setinde işlem = sipariş (Orders), yani "ortalama işlem
tutarı" kalem başına değil sipariş başına ortalamadır.

**2. Tarih çözücü (`resolve_dates`, `date_note`).** Soru modele gitmeden önce tarih ifadeleri bulunur, aralığa çevrilir ve
soruya **Tarih notu** olarak eklenir. Model tarih hesaplamaz, nottaki aralığı kopyalar. Hesap yalnızca
`config.REFERENCE_DATE` (2026-06-30) üzerinden yapılır; sistem saati kullanılmaz.

| İfade | Örnek | Sonuç |
|---|---|---|
| Config ifadeleri (`DATE_RANGES`) | "son 6 ay", "geçen çeyrek", "son 30 gün" | Config'deki aralık |
| Yılsız ay adı | "Haziranda", "Mayıs ayında" | Referans tarihten geriye en yakın o ay (Ocak–Haziran → 2026, Temmuz–Aralık → 2025) |
| Yıllı ay / çeyrek | "2026'nın ilk çeyreği", "2025'in son çeyreği", "I. çeyrek" | İlgili çeyrek; yılsız "son çeyrek" belirsiz sayılır, çözülmez |
| İlk N ay | "Mart sonuna kadarki ilk üç ay" | O yılın Ocak'ından N. ayın sonuna |
| Ay aralığı | "Ocak'tan Haziran'a", "Ocak–Mart" | En erken ayın başından en geç ayın sonuna tek aralık |
| Aktif müşteri | "kaç aktif müşterimiz var" | Son 90 gün (metrik tanımı) |
| Tarih yok | "İzmir'in toplam cirosu" | "Tarih filtresi ekleme" notu |

Sınırlılıklar: kural tabanlıdır (ör. "geçen Kasım", "yılbaşından beri" tanınmaz); "Aralık" gibi ay adları başka anlamda
kullanılırsa yanlış eşleşebilir. Etkisi ölçümlerle belgelendi: [docs/olcumler/README.md](docs/olcumler/README.md)
(tarih hataları 03 ve 07 bu katmandan sonra bütün ölçüm setlerinde düzeldi).

## Güvenlik

_TODO: Ödev Bölüm 05'teki 7 kuralın her biri nasıl sağlanıyor._

## Testler

_TODO: Özet tablo (docs/test_report.md'den)._

## Sınırlılıklar

_TODO: Teknik değerlendirmeyle birlikte tamamlanacak._

### Bilinen model hataları (prompt ölçümleri, [docs/olcumler/README.md](docs/olcumler/README.md))

Son ölçümlerde (yeniden deneme olmadan) iş sorularında test soruları ve iki farklı ifade setinde **7/8**. Kural ve kodla
üretilen notlarla çözülemeyen hatalar:

| Test | Hata | Not |
|---|---|---|
| 04 | "Kategori bazında …" gruplama sorusuna `LIMIT 1` ekleniyor, tek kategori dönüyor | Prompt'ta "gruplama sorularında LIMIT ekleme" kuralı var; model uygulamıyor |
| 08 | "En çok satan / satılan" bazen ciroya, bazen adete (`SUM(Quantity)`) göre sıralanıyor | Metrik sözlüğü ve Metrik notu "ciroya göre" diyor; bir ölçümde model notu okuyup tersini yazdı |
| 05 | Ara sıra var olan `Orders` tablosu "veri modelinde yok" sayılıp `unsupported` dönüyor | `unsupported` bir hata olmadığı için pipeline'ın yeniden denemesi bunu yakalamaz |

Ortak gözlem: `qwen2.5-coder:7b` örnekleri kurallardan daha güçlü takip ediyor ve sonuçlar ifadeden ifadeye dalgalanıyor.
Muhtemel çözüm ilgili kalıbı gösteren bir few-shot örneği ya da daha büyük bir model. Görünen sorulardaki sonuç gizli test
setinde garanti değildir; kurallar ve notlar bu sorulardaki hatalara bakılarak eklendi.

### Çalışma ortamı

- Bağlam penceresi `num_ctx = 8192` (Ollama varsayılanı 4096). Prompt ≈ 3255 token; pencere aşılırsa Ollama prompt'un başını
  (sistem prompt'u) sessizce keser.
- Model ekran kartı belleğine tam sığmıyor (`ollama ps`: %24 CPU / %76 GPU). Yanıtlar genelde 2–10 sn, model belleğe ilk
  yüklenirken ~15 sn.

## Kullanılan yapay zekâ araçları

_TODO: Örn. Claude, GitHub Copilot: hangi kısımda, nasıl kullanıldı._
