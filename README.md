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
python setup_db.py               # veritabanını sabit CSV'lerden sıfırdan kur
```

## Çalıştırma

```bash
streamlit run app/ui.py          # arayüz
python tests/run_all.py          # 16 testi çalıştır, docs/ altına rapor üret
```

## Proje yapısı

```
config.py            Sabit ayarlar: referans tarih, limitler, model adı
setup_db.py          Veritabanını data/csv/ içindeki sabit veriden kurar
data/                Veri seti (CSV) ve veri dokümantasyonu
app/schema.py        Şema bağlamı: tablo, sütun, tip, PK/FK → LLM'e verilir
app/llm.py           Prompt + Ollama çağrısı → SQL üretimi
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

## Güvenlik

_TODO: Ödev Bölüm 05'teki 7 kuralın her biri nasıl sağlanıyor._

## Testler

_TODO: Özet tablo (docs/test_report.md'den)._

## Sınırlılıklar

_TODO_

## Kullanılan yapay zekâ araçları

_TODO: Örn. Claude, GitHub Copilot: hangi kısımda, nasıl kullanıldı._
