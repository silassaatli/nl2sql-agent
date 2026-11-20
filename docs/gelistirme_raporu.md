# Geliştirme raporu: değerlendirme altyapısı ve ek özellikler

Dal: `feature/eval-and-improvements` · Model: `gemini-3.5-flash-lite` · Tarih: 2026-11-20

Bu çalışmada mevcut NL2SQL ajanına bir ölçüm altyapısı ve birkaç ek özellik eklendi. Kural şuydu: **çalışan hiçbir davranış değişmesin.** Ajanın akışını değiştiren her yeni özellik bir bayrakla açılıyor ve varsayılan olarak kapalı. Bayraklar kapalıyken modele giden istekler, değişiklikten önceki kodla bayt bayt aynı. Bu, 61 soruyla (16 ödev testi + 45 golden set sorusu) karşılaştırılarak doğrulandı. Güvenlik katmanına (`validator.py`, `db.py`) dokunulmadı.

## 1. Eklenenler

| Özellik | Ne yapar | Bayrak | Dosyalar |
|---|---|---|---|
| Golden set + eval | 45 soruluk test seti; ajanı ölçer, rapor üretir | — | `eval/` |
| Self-correction | Hata, boş sonuç veya her zaman doğru JOIN koşulunda modelden en fazla 2 kez düzeltme ister | `SELF_CORRECTION` | `app/pipeline.py`, `app/sql_checks.py` |
| Göreli tarih çözücü | "geçen ay", "bu yıl" gibi ifadeleri referans tarihe (2026-06-30) göre kodla çözer, varsayıma yazar | `RELATIVE_DATES` | `app/semantic.py`, `app/llm.py` |
| Otomatik yorum | Sonuç tablosunun altına 2–3 cümlelik yorum (kural tabanlı) | `INSIGHTS` | `app/insight.py` |
| SQL açıklaması | Çalıştırılan SQL'i maddeler hâlinde Türkçe anlatır (sqlglot) | `SQL_EXPLAIN` | `app/explain.py` |
| Panelde "Değerlendirme" | Son eval raporunu, tekrarlı koşuları ve karşılaştırmayı gösterir | — | `app/eval_view.py` |

**Golden set (`eval/golden_set.json`):** 45 Türkçe iş sorusu. Dağılım:
- 38 SQL sorusu (11 kolay, 16 orta, 11 zor) ve 4 netleştirme gerektiren soru.
- 3 cevaplanamaz veya zararlı soru.
- Zor sorular şu teknikleri gerektiriyor: LAG ile aylık değişim, kümülatif toplam, kategori içinde ROW_NUMBER, yeni müşteri sayısı, churn riski, segment payı, birlikte alınan ürün çiftleri.
- Her zor sorunun gold SQL'i, farklı bir yöntemle (pencere fonksiyonu kullanmadan) yazılmış bağımsız bir kontrol sorgusuyla aynı sonucu verdi. "İlk N" sorularında sınırda eşitlik olmadığı otomatik kontrol edildi (`eval/check_gold.py`).
- 3 soru ödevdeki test ya da few-shot sorularının farklı ifadesi; `paraphrase` etiketiyle işaretli.

**Eval nasıl karşılaştırır (`eval/run_eval.py`):**
- Her soru panelin kullandığı `pipeline.ask()` üzerinden sorulur. Beklenen sonuç her koşuda gold SQL'den salt-okunur bağlantıyla yeniden hesaplanır.
- Karşılaştırma `tests/run_all.py`'deki kuralla yapılır: sütun adlarına bakılmaz, ondalıklar 2 basamağa yuvarlanır. Sıra yalnızca gerektiği yerde kontrol edilir, fazladan sütuna izin verilir.
- Netleştirme sorusunda ajanın soru sorması, ret sorusunda reddetmesi başarı sayılır.
- Kota hatasında bekleyip yeniden dener (exponential backoff). Cevaplar önbelleğe yazılır, kesilen koşu kaldığı yerden devam eder.
- Sonuçlar zorluk ve etikete göre kırılımlarla JSON ve Markdown olarak raporlanır.

## 2. Eval sonuçları

Model aynı soruya her seferinde aynı SQL'i üretmiyor. Bu yüzden her ayar 3 kez koşturuldu.
- **Kapalı:** bugünkü sistem.
- **Açık:** `SELF_CORRECTION` ve `RELATIVE_DATES` birlikte.

| Ayar | Tamamlanan koşuların ortalaması | Bütün koşuların ortalaması | Koşu başına puanlanan soru |
|---|---|---|---|
| Bayraklar kapalı | **%97,8** (2 koşu) | %97,0 (3 koşu) | 45 / 43 / 45 |
| Bayraklar açık | **%98,9** (2 koşu) | %99,3 (3 koşu) | 45 / 45 / 17 |

| Zorluk (bütün koşuların ortalaması) | Kapalı | Açık |
|---|---|---|
| Kolay | %100 | %100 |
| Orta | %98,5 | %100 |
| Zor | %90,2 | %95,5 |

**Bu sonuçları okurken:**
- Kota daraldığı için son koşu (açık, 3. tekrar) 17. sorudan sonra durduruldu. G18–G45 bu koşuda sorulmadı.
- Kapalı ayarın 2. tekrarında G34 ve G35 kotaya takıldı.
- Eksik sorular doğruluk hesabına girmedi; ayrıntılar `eval/reports/repeat_latest.md` dosyasında.
- Adil karşılaştırma için **tamamlanan koşulara** bakılmalı. Aradaki fark yaklaşık **bir soru** (G23). Bu kadar az koşuyla farkın anlamlı olduğu söylenemez.
- Ödevin 16 testi (`tests/run_all.py`, Gemini, bayraklar kapalı) bu çalışma sırasında 5 kez koşturuldu:
  - **4 koşuda kabul eşiği karşılandı** (iş ≥ 6/8, davranış 2/2, güvenlik 6/6). Bunlardan birinde iş 8/8 tam geçti.
  - **1 koşuda karşılanmadı:** 08 ve 11 kota hatası (`model_unavailable`), 05 bir değer uyuşmazlığı.
  - FAIL'lerin geri kalanı kota hatasıydı. 05, 06 ve 08 tek başına tekrar sorulunca cevap anahtarıyla eşleşti.
  - Bayraklar kapalıyken modele giden istekler eski kodla aynı olduğu için bu FAIL'ler koddan değil, kota ve model değişkenliğinden kaynaklanıyor.
  - Teslim öncesinde kota toparlanınca son bir koşu yapılacak.

## 3. Bulgular

**Hataların çoğu sessiz.** Sorgu hatasız çalışıyor ama yanlış sonuç veriyor:
- **G25:** Model JOIN koşulunu `p.ProductID = p.ProductID` yazdı. Bu koşul her satırda doğru olduğu için tablolar kartezyen çarpıma girdi ve oran %92 yerine %1162 çıktı. Aynı hata G30'da da bir kez görüldü.
- **G30** ("Her kategoride en çok ciro getiren ürün"): Model çoğu koşuda kategori başına birinciyi seçmek yerine bütün ürünleri sıralı listeliyor.

**"Geçen ay" düzeltmesi işe yaradı.**
- Eski kod "geçen ay" ifadesini tanımadığı için soruya "tarih filtresi EKLEME" notu ekliyordu. Model bu nota bazen uydu ve bütün yılın cirosunu verdi: bayraklar kapalıyken 3 koşunun 1'inde.
- `RELATIVE_DATES` açıkken aralık kodla çözülüyor (Mayıs 2026) ve varsayıma "geçen ay = 2026-05-01 – 2026-05-31" olarak yazılıyor. Bu ayarla G23 2/2 geçti.

**Self-correction neden fark yaratmadı?**
- Gemini'nin ürettiği SQL'ler bu sette neredeyse hiç hata vermiyor ve boş dönmüyor. Yani self-correction'ı tetikleyecek bir durum nadiren oluştu.
- Düzelen 2 vaka (G15, sütun adı hatası) bayrak kapalıyken de 1 kez yeniden deneniyor; yani kazanç yeni özellikten gelmedi.
- Görülen hatalar sessiz yanlışlardı ve hata/boş sonuç tetikleyicisi bunları yakalayamaz. Bu yüzden her zaman doğru koşul kontrolü eklendi. Ölçümde, bayrak açıkken bu hata hiç oluşmadı; kontrolün doğruluğunu şimdilik yalnızca birim testleri gösteriyor.
- Self-correction ödevdeki "en fazla 1 yeniden deneme" kuralını aştığı için **deneysel** kalıyor.

## 4. Bilinen sınırlamalar

- **G30 çözülmedi.** Kategori içinde birinciyi seçme sorusunu model güvenilir şekilde çözemiyor. Kod tarafında bir kontrol bu hatayı yakalamıyor.
- **Model değişkenliği.** Aynı soru farklı koşularda farklı SQL üretebiliyor. Tek koşuluk sonuçlar yanıltıcı olabilir; bu yüzden tekrarlı ölçüm yapıldı. Daha güvenilir sonuç için daha fazla tekrar gerekir.
- **Kota.** Ücretsiz katmanda yoğun ölçümde 429/503 hataları sık görülüyor. Eval bekleyip yeniden deniyor, ama `tests/run_all.py`'de bu mekanizma yok; kota dolunca rastgele bir test FAIL olabiliyor.
- **Golden set bu model için kolay.** Kolay ve orta sorular neredeyse her zaman geçiyor; farkı zor sorular gösteriyor. Daha zor ve daha belirsiz sorular eklenmeli.
- **Göreli tarih çözücünün kapsamı.** "geçen/bu ay", "bu/geçen yıl", "bu çeyrek", "son N ay/gün", "geçen/bu hafta", "dün". "bugün" bilerek yok, çünkü "bugüne kadar" "tüm zamanlar" anlamına geliyor. "Geçen yıl" 2025 takvim yılı olarak çözülüyor, ama veri 2025-07-01'de başlıyor.
- **Yapılmadı:** Token ve maliyet takibi. Teslim süresine sığmadı; resmi fiyatların doğrulanması gerekiyor.

## 5. Nasıl çalıştırılır

```powershell
python -m pytest -q                                  # 115 birim testi (mock'lu, ağ yok)
python eval/check_gold.py                            # gold SQL kontrolü (model çağrısı yok)
python eval/run_eval.py                              # golden set (gerçek Gemini, GEMINI_API_KEY gerekli)
python eval/run_eval.py --experimental both --repeat 3   # bayraklar kapalı/açık, 3'er tekrar
python eval/run_eval.py --experimental both --repeat 3 --cache-only   # yalnızca önbellekten rapor
```

Demo için ek özellikleri açmak (`config.py` değişmeden, yalnızca o terminal oturumu için):

```powershell
$env:NL2SQL_INSIGHTS = "1"; $env:NL2SQL_SQL_EXPLAIN = "1"; $env:NL2SQL_RELATIVE_DATES = "1"
streamlit run app/ui.py
```

`NL2SQL_SELF_CORRECTION = "1"` deneysel moddur; ödevdeki yeniden deneme sınırını aştığı için demoda kapalı kalması önerilir.
