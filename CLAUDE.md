# CLAUDE.md: NL2SQL Agent projesi için çalışma notları

## Proje
Ensight teknik staj ödevi (ENS-AI-001): Türkçe sorulan iş sorularını SQL'e çeviren, sorguyu güvenli şekilde çalıştıran ve sonucu gösteren bir **Proof of Concept**.
- Ödev metni: `data/kaynak/NL2SQL_Stajyer_Odevi_ENS-AI-001.pdf` (**tek gerçek kaynak**; kurallar, 16 test, puanlama burada)
- Ekip planı: `data/kaynak/NL2SQL_3_Gunluk_Ekip_Plani.pdf`
- Bu iki PDF repoda yok (`.gitignore`), her üyenin yerel kopyasında durur.
- Veri seti: `data/VERI_SETI.md` (bankacılık senaryosu, sabit CSV'ler, şema ödevdekiyle birebir aynı)
- Süre: 3 gün. 2 kişilik ekip. Teslimden sonra her üye 10 dakikalık bireysel sözlü savunmaya girecek.

## Ben kimim, nasıl çalışmalısın
- Ben Sıla, ekipte **Kişi B**'yim: `app/schema.py`, `app/llm.py` (prompt + Ollama/Qwen), `app/ui.py` (Streamlit), test 01–10 için referans SQL'ler ve beklenen sonuçlar, `setup_db.py`, JSON log (`app/logger.py`) ve test raporu (`tests/report.py`).
- Arkadaşım **Kişi A**: `app/validator.py`, `app/db.py`, `app/pipeline.py`, `tests/run_all.py`, hata yönetimi. Log ve raporu kendisi yazmaz, sadece çağırır (`pipeline.py` → `write_log`, `run_all.py` → `tests/report.py`).
- Bilgisayar mühendisliği öğrencisiyim. Temel SQL ve Python biliyorum, LLM/RAG deneyimim var. Bu projede yeni olan şeyleri öğrenmek istiyorum.
- **Sözlü savunmada yazılan her satırı açıklamam gerekecek.** Bu yüzden:
  - Kod yazmadan önce ne yapacağını ve nedenini kısaca anlat.
  - Kodu küçük parçalarla yaz, her parçadan sonra ne yaptığını açıkla.
  - Yeni bir kavram (SQLGlot AST, authorizer, few-shot vb.) geçtiğinde bir iki cümleyle açıkla.
  - Bir SQL'i ben yazabilecekken direkt yazma; önce ipucu ver, ben deneyeyim.
- Türkçe cevap ver.

## Değişmez kurallar (ödevden)
- Referans tarih **2026-06-30** (`config.py`). `date('now')` veya sistem saati sorgu sonuçlarında ASLA kullanılmaz.
- Ciro = `SUM(Quantity * UnitPrice)` (OrderItems). `Products.Price` ciro için kullanılmaz.
- Sadece tek ifadeli SELECT; sadece Customers, Products, Orders, OrderItems; salt-okunur bağlantı; 500 satır limiti; süre sınırı.
- Güvenlik prompt'a değil koda bırakılır. Her SQL çalışmadan önce `validate_sql` + `execute_sql` (authorizer) kurallarından geçer.
- Yeniden deneme en fazla 1 kez.
- Mock veya elle yazılmış çıktı, canlı model başarısı gibi raporlanamaz.
- Gereksiz bağımlılık ekleme (LangChain vb. yok). Sade Python + sqlglot + streamlit + ollama + pytest.
- Bonus özelliklere çekirdek bitmeden girme.

## Fonksiyon sözleşmesi (iki kişi buna göre paralel çalışıyor, imzaları değiştirme)
```python
generate_sql(question: str, previous_error: str | None = None) -> dict
    # {"status": "ok"|"clarify"|"unsupported", "sql": str, "assumption": str, "message": str}
    # Fırlatır: ModelUnavailableError (Ollama kapalı/model yok/zaman aşımı → "model_unavailable", yeniden deneme yok)
    #           ModelOutputError(ValueError) (cevap kullanılamaz: bozuk JSON, bilinmeyen status, ok iken boş sql
    #                             → pipeline "except ValueError" ile yakalar → "error" / "invalid_model_response", yeniden deneme yok)
    # İkisi de app.llm'den import edilir. status != "ok" iken sql her zaman "" döner.
validate_sql(sql: str) -> tuple[bool, str, str]     # (geçti_mi, temiz_sql, hata_türü)
execute_sql(sql: str) -> tuple[list[dict], bool]    # (satırlar, kesildi_mi)
ask(question: str) -> dict                           # pipeline: generate → validate → execute + log
write_log(record: dict) -> None                      # app/logger.py (Kişi B), pipeline.py çağırır
```

## Ekip kararları
1. **Log ve rapor Kişi B'de.** `write_log` → `app/logger.py`, test raporu (JSON + Markdown) → `tests/report.py`. Kişi A bunları yalnızca çağırır.
2. **Durum çevirisi `pipeline.py`'de yapılır** (`generate_sql` durumu → `ask()` durumu):

   | Kaynak | `ask()` status |
   |---|---|
   | `generate_sql` → `ok` (ve SQL başarıyla çalıştı) | `success` |
   | `generate_sql` → `clarify` | `clarify` |
   | `generate_sql` → `unsupported` | `rejected` |
   | Güvenlik reddi (validator veya authorizer) | `rejected` |
   | Diğer hatalar (parse, unknown_field, timeout, model_unavailable vb.) | `error` |
3. **Beklenen sonuç formatı** (`tests/expected/<id>.json`): `id`, `question`, `reference_sql`, `columns`, `rows` (liste listesi), `row_count`. Dosyalar elle yazılmaz: 8 referans SQL `tests/expected/build_expected.py` içinde durur, betik bunları kendi salt-okunur bağlantısıyla (bilerek `app/db.py` değil) çalıştırıp dosyaları üretir. Soru metni `test_cases.json`'dan okunur. Veri değişirse betik yeniden çalıştırılır.
4. **Kişi A için (`run_all.py` karşılaştırması):** sütun adlarına değil, satır sırasına ve değerlere bakılır. Float değerler karşılaştırmadan önce **2 ondalığa yuvarlanır**, çünkü aynı hesap farklı sırayla yazılınca son basamakta küçük farklar çıkabilir (ör. `SUM(UnitPrice * Quantity)`).
5. **Sıra kontrolü teste göre değişir:**
   - **Sıkı sıra (01, 03, 08):** soru sıralama içeriyor ("ilk 5", "aylık trend", "ilk 3"). Satırlar beklenen sırayla birebir eşleşmeli.
   - **Sırasız (04, 05, 06):** soru sıralama istemiyor. Karşılaştırmadan önce hem beklenen hem gerçek satırlar sıralanır. Cevap anahtarındaki `ORDER BY` yalnızca dosyanın deterministik olması içindir.
   - **02, 07:** tek satır döndüğü için sıra fark etmez.
   - Gerekçe: sıranın anlam taşımadığı yerde sırayı kontrol etmek doğruluğu değil şansı ölçer. Ödevdeki "sıra ve değer" şartı, sıranın sorunun parçası olduğu testlerde aynen uygulanır.
6. **Eksik sütun riski (01, 07, 08: "hangi ürün/şehir?") iki katmanda çözülür:**
   - **Prompt (Kişi B, `llm.py`):** "Sıralama veya seçim ölçütü olan metriği (ör. ciro) her zaman sonuç sütunu olarak göster" kuralı eklenir.
   - **Karşılaştırma (Kişi A, `run_all.py`):** modelin döndürdüğü sütun sayısı beklenenden azsa, gelen sütunlar beklenen sütunlarla değerlerine göre eşleştirilir ve sadece onlar karşılaştırılır (ör. yalnızca şehir adı döndüyse yalnızca şehir adı). Satır sayısı ve sıra kuralı (madde 5) yine geçerlidir.
   - **Kısıt (ölçümde bulunan hata):** esnek eşleştirme YALNIZCA model daha az sütun döndürdüğünde ve döndürdüğü her sütun eşleştiğinde uygulanır. Model en az beklenen kadar sütun döndürdüyse beklenen sütunların **hepsi** eşleşmeli. Aksi halde doğru şehir + yanlış ciro PASS sayılır (gerçek örnek: test 07'de model Q4 2025 tarihlerini kullandı, İstanbul yine birinci çıktığı için yanlışlıkla PASS sayılmıştı). Uygulama örneği: `docs/olcumler/karsilastir.py`.
   - **Fazla sütun (kabul edildi, 2026-11-05):** model beklenenden fazla sütun döndürürse, beklenen sütunların **hepsi** modelin farklı sütunlarında doğru değerlerle bulunuyorsa PASS; fazla sütunlar yok sayılır. Bütün iş testlerinde geçerli. Gerekçe: fazladan bilgi beklenen sonucu bozmuyor (gerçek örnek: test 05'te model doğru 12 müşteriyi ek `Segment` sütunuyla döndürdü). Uygulama: `tests/run_all.py` (Kişi A, PR #6).

## Durum
- Hazır: `setup_db.py`, `data/`, `config.py`, `app/validator.py`, `app/db.py`, `tests/test_cases.json`, `tests/expected/` (01–08 cevap anahtarı + `build_expected.py`), `app/schema.py` (şema + az değerli TEXT sütun değerleri + tarih aralığı + FK'lerden JOIN koşulları → `data/schema.json`; `setup_db.py` otomatik çağırır), `app/llm.py` (prompt + varsayılan ölçüt kuralı + yılsız ay kuralı + 5 few-shot + `generate_sql`), `app/semantic.py` (bonus semantik katman: metrik sözlüğü + tarih çözücü; soruya Tarih notu ve Metrik notu ekler, README'de belgeli), `app/pipeline.py` (Kişi A), `tests/run_all.py` (Kişi A), `tests/test_security.py` (Kişi A), `app/logger.py` (`logs/queries.jsonl`), `tests/report.py` (`docs/test_report.json` + `.md`)
- **Resmi test raporu (`python tests/run_all.py`, 5 few-shot, yeni pipeline, ısınmış model, 2026-11-06 12:52): iş 7/8, davranış 2/2, güvenlik 6/6 → kabul eşiği karşılandı.** 12 ve 16 modele gitmeden validator'da `multiple_statements`; 14'te yalnızca temiz `SELECT * FROM Customers` çalıştı. Süre: modele giden 13 test ort. 5,2 sn / medyan 5,3 sn. Soğuk modelde ilk çağrı yükleme süresini içerir (ölçüm: 14,6 sn, hemen ardından 3,8 sn; soğuk koşuda ilk test 41,2 sn) → demodan önce ısınma sorusu. Tek FAIL: 05 (doğru 12 müşteri, ama yalnızca `CustomerID, Name`; `City` eksik, eksik sütun sadece 01/07/08'de kabul). Rapor: `docs/test_report.md` + `.json`.
- Rapor geçmişi: main `3644acc` iş 6/8 (04, 05 FAIL; fazla sütun kuralı yoktu) → main `ec599d4` iş 7/8 (04 FAIL) → 5. few-shot ("Şehir bazında sipariş adetlerini göster.") iş 7/8 (04 düzeldi, 05 eksik sütunla bozuldu). Örnek, üç ölçüm setinin toplamı 20/24 → 22/24 çıktığı için tutuldu (Sıla'nın kararı).
- Ortam: `.venv` + `requirements.txt` kurulu, Ollama + `qwen2.5-coder:7b` indirildi ve Python'dan çağrıldı
- Prompt ölçümleri (`docs/olcumler/README.md`, 21 ölçüm, retry yok, iş soruları 01–08; karşılaştırma `run_all.py` ile aynı kural). **Güncel (adım 18–20, 5 few-shot): test soruları 7/8, farklı ifadeler 1: 8/8, farklı ifadeler 2 (düzeltilmiş): 7/8.** 09 ve 10 her ölçümde doğru, 11–16'da SQL hiç çalışmadı. Prompt ≈ 3446 token; `num_ctx = 8192` (`llm.LLM_NUM_CTX`, Ollama varsayılanı 4096'ydı). "İşlem tutarı" eş anlamlı değil (işlem = sipariş).
- Ölçüm aracı düzeltmeleri: `karsilastir.py` eksik sütunu bütün testlerde kabul ediyordu (madde 6'ya aykırı) ve `yeniden_puanla.py` yalnızca `0*.json` okuyordu; düzeltilip bütün ölçümler yeniden puanlandı (bazı eski puanlar düştü, README'de açıklandı).
- Açık sorunlar: 05'te eksik sütun (5. örnekten sonra); 08 ve 04 son ölçümlerde düzeldi ama dalgalanıyordu; ara sıra var olan `Orders` tablosunu "yok" sayıp `unsupported` (05). Bilinen hatalar README "Sınırlılıklar"da. 8/8 denemesi burada bitti.
- `app/ui.py` (dal `sila/ui`): Streamlit; soru formu + 4 demo örneği, durum kutusu (success yeşil / clarify mavi / rejected sarı / error kırmızı) + hata türünün Türkçe açıklaması, mesaj, varsayım, üretilen SQL + duruma göre not, sonuç tablosu, 500 satır uyarısı, süre ve yeniden deneme. Güvenlik kontrolü yapmaz, sadece `ask()`'ı çağırır. AppTest ile gerçek modelle ve `streamlit run` ile denendi.
- **Doğrudan SQL yolu (Kişi A, main'de):** `pipeline.py` `SQL_START` regex'i baştaki boşluk/yorumları atlayıp ilk kelime SQL komutuysa girdiyi modele göndermeden validator'a verir; hatalı kullanıcı SQL'i yeniden denenmez, logda `model: null`. Regex güvenlik kararı değil, yalnızca yol seçer. Bilinen sınır: "Select en çok satan…" gibi Türkçe soru SQL sayılıp `parse_error` döner. Demo: "SELECT * FROM Customers; DELETE FROM Customers" artık canlı olarak `multiple_statements` gösteriyor.
- **Dokümantasyon (dal `sila/dokumanlar`):** README TODO'ları dolduruldu; `docs/mimari.md` (Mermaid, dosya:satır), `docs/log_ornekleri.md` (5 gerçek log satırı), `docs/teknik_degerlendirme.md` (≤ 2 sayfa). Model lisansı Apache 2.0 (`ollama show --license`). `ui.py` doğrudan SQL'de "Girilen SQL" başlığı gösteriyor (`SQL_START` pipeline'dan import). Sıfırdan kurulum 2026-11-06'da denendi, sonuç README'de; tek takılma: uzun klasör yolunda (>~115 karakter) Windows 260 karakter sınırı yüzünden `pip install` (streamlit 1.67) kırılıyor, README'de uyarı var. Açık `[KONTROL: …]` notları: Kişi A'nın adı ve YZ araçları, Claude Code kullanım kapsamı, veri üretimi.
- Yapılacak: kalan `[KONTROL]` notlarını kapat; demo provası (önce ısınma sorusu).

## Komutlar
```bash
python setup_db.py          # veritabanını kur + data/schema.json üret
python -m app.schema        # sadece şemayı yeniden üret (proje kökünden, -m ile)
python tests/expected/build_expected.py   # test 01–08 cevap anahtarını üret
streamlit run app/ui.py     # arayüz
python tests/run_all.py     # 16 test + rapor
ollama pull qwen2.5-coder:7b
```
