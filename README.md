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
| Ortalama sipariş kalemi tutarı | kategori ortalaması, satır / kalem / satış kalemi / işlem tutarı | `AVG(oi.Quantity * oi.UnitPrice)` (AVG(UnitPrice) değil) |

Soruda riskli bir eş anlamlı geçerse (ör. "en çok sat…", "kalem", "satır tutarı") formül ayrıca **Metrik notu** olarak
soruya eklenir. Not: veri setinde "işlem" = sipariş (Orders) olarak tanımlı; "ortalama işlem tutarı" sipariş başına ortalama
olarak da okunabilir. Ekip kararıyla kalem ortalamasına eşlendi.

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

_TODO_

## Kullanılan yapay zekâ araçları

_TODO: Örn. Claude, GitHub Copilot: hangi kısımda, nasıl kullanıldı._
