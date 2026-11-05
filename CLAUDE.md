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
    #           ModelOutputError (cevap kullanılamaz: bozuk JSON, bilinmeyen status, ok iken boş sql
    #                             → "invalid_model_output", 1 kez yeniden denenebilir)
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

## Durum
- Hazır: `setup_db.py`, `data/`, `config.py`, `app/validator.py`, `app/db.py`, `tests/test_cases.json`, `tests/expected/` (01–08 cevap anahtarı + `build_expected.py`), `app/schema.py` (şema + az değerli TEXT sütun değerleri + tarih aralığı + FK'lerden JOIN koşulları → `data/schema.json`; `setup_db.py` otomatik çağırır), `app/llm.py` (prompt + varsayılan ölçüt kuralı ("en çok satan" dahil = ciro) + yılsız ay kuralı + 4 few-shot + `generate_sql`)
- Ortam: `.venv` + `requirements.txt` kurulu, Ollama + `qwen2.5-coder:7b` indirildi ve Python'dan çağrıldı
- Prompt ölçümleri (`docs/olcumler/README.md`, retry yok, iş soruları 01–08): test soruları 4/8 → 5/8 → 8/8 → (ay kuralı sonrası) 7/8; farklı ifadeler 1: 6/8 → 7/8; farklı ifadeler 2: **3/8**. 09 ve 10 her ölçümde doğru, 11–16'da SQL hiç çalışmadı. Prompt ≈ 2777 token (Ollama penceresi 4096; aşılırsa sistem prompt'u kesilir).
- Açık sorunlar (prompt): few-shot Örnek 1'in tarih aralığı (2025 Q4) çeyrek sorularına kopyalanıyor (07); "en çok satan" kurala rağmen adete göre (08); karmaşık yılsız ay ifadelerinde yıl yanlış (03); "satır tutarı" eş anlamlısı tanınmıyor (04).
- Yapılacak: `app/pipeline.py`, `app/ui.py`, `app/logger.py`, `tests/run_all.py`, `tests/report.py`, `docs/`, README'deki TODO'lar

## Komutlar
```bash
python setup_db.py          # veritabanını kur + data/schema.json üret
python -m app.schema        # sadece şemayı yeniden üret (proje kökünden, -m ile)
python tests/expected/build_expected.py   # test 01–08 cevap anahtarını üret
streamlit run app/ui.py     # arayüz
python tests/run_all.py     # 16 test + rapor
ollama pull qwen2.5-coder:7b
```
