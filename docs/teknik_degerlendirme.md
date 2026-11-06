# Teknik değerlendirme

NL2SQL Agent · ENS-AI-001 · Sıla Saatlı, Taha Yavaş [KONTROL: Kişi A'nın adı]

**Sonuç.** Resmi raporda ([test_report.md](test_report.md), gerçek model, mock yok) iş 8/8 (eşik 6/8), davranış 2/2,
güvenlik 6/6. Model `qwen2.5-coder:7b` (Ollama, yerel), `temperature=0`, prompt ≈ 3446 token, `num_ctx=8192`. Modele giden
13 testte uçtan uca süre ortalama 4,7 sn, medyan 4,9 sn (ısınmış model; soğuk ilk çağrı yüklemeyle 14,6 sn).

> **Karşılaştırma notu.** İlk cevap anahtarı test 05 için `City` sütununu da şart koşuyordu; ödev bunu istemediği için
> karşılaştırma ödev ölçütüne göre düzeltildi. Model çıktısı değişmedi. Eski kuralla iş 7/8 (05 FAIL), düzeltilmiş kuralla 8/8.

## 1. Sınırlılıklar

- **Doğruluk ifadeye bağlı.** Son prompt'la üç ölçüm setinde 7/8, 8/8, 7/8 (eski kuralla; düzeltilmiş kuralla üçü de 8/8);
  önceki bir sürümde "farklı ifadeler 2" 2/8 ([olcumler/README.md](olcumler/README.md)). Kurallar ve örnekler görülen
  hatalara bakılarak eklendi; gizli test setinde aynı başarı garanti değil.
- **05'te kararsızlık.** Ölçümlerde model bazen var olan `Orders` tablosunu "yok" sayıp `unsupported` döndürdü; bu bir hata
  sayılmadığı için yeniden deneme yakalamıyor.
- **Doğal dil güvenlik testlerinde reddi veren model.** 12, 14, 16 modele gitmeden validator'da işleniyor; 11, 13, 15'te ise
  model SQL üretmeden `unsupported` döndürdü, validator'a SQL ulaşmadı. Validator ve authorizer `tests/test_security.py`
  ile ayrıca doğrulanıyor (10/10).
- **Doğrudan SQL tespiti ilk kelimeye bakıyor.** "Select en çok satan 5 ürün" modele gitmez, `parse_error` döner
  (güvenlik değil, kullanılabilirlik sınırı).
- **Varsayım metni doğrulanmıyor.** "İzmir'in toplam cirosu"nda SQL'de tarih filtresi yokken model "tarih filtresi eklendi"
  yazdı; esas olan SQL'dir, arayüz bunu belirtiyor.
- **Semantik katman kural tabanlı.** "Geçen Kasım", "yılbaşından beri" tanınmıyor.
- **Donanım.** 6 GB VRAM'e model + bağlam belleği sığmıyor (%76 GPU / %24 CPU); tek kullanıcılı PoC için yeterli.
- **Kapsam.** Tek SELECT; takip sorusu, grafik, çok adımlı planlama yok (bonus).

## 2. Karşılaşılan sorunlar ve çözümleri

Prompt 21 ölçümle, her değişiklikten sonra yeniden deneme olmadan geliştirildi (iş soruları 4/8 → 7/8, eski kuralla).

| Sorun | Çözüm | Etki |
|---|---|---|
| Var olan tablolar "yok" sayıldı, JOIN'ler unutuldu | FK'lerden üretilen hazır JOIN koşulları | 4/8 → 5/8 |
| Kurallar yazılı ama uygulanmadı | 4 few-shot örneği | 5/8 → 7/8 |
| Yılsız ayda yıl uyduruldu; "geçen çeyrek"te örneğin tarihi (2025 Q4) kopyalandı | Tarih çözücü: aralık kodla hesaplanıp "Tarih notu" olarak eklenir | 03 ve 07 sonraki bütün setlerde geçti |
| Tarihsiz soruya filtre eklendi | "Tarih filtresi ekleme" notu + aktif müşteri için son 90 gün notu | 06 bütün setlerde düzeldi |
| "En çok satan" adet, "ortalama satır tutarı" `AVG(UnitPrice)` sanıldı | Metrik sözlüğü + "Metrik notu" | 08 son ölçümlerde ciroya göre |
| "Kategori bazında" sorusuna `LIMIT 1` | 5. few-shot örneği (gruplama, LIMIT yok) | 04 düzeldi, 05'te model `City`'yi bıraktı; 3 set toplamı 20/24 → 22/24 |
| 4096 token'lık varsayılan pencere yetmeyebilirdi (aşılırsa sistem prompt'u sessizce kesilir) | `num_ctx = 8192` | Prompt ≈ 3446 token |
| Doğrudan SQL de modele gidiyor, validator'a ulaşmıyordu | `SQL_START`: SQL komutuyla başlayan girdi doğrudan validator'a (Kişi A) | 12, 16 `multiple_statements`; 14'te yalnızca temiz SELECT |
| Ölçüm aracı doğru şehir + yanlış ciroyu PASS sayıyordu | Kayıtlı SQL'ler düzeltilmiş kuralla yeniden puanlandı | Bazı puanlar düştü (adım 2: 8/8 → 7/8) |
| Cevap anahtarı 05'te ödevin istemediği `City`'yi şart koşuyordu | Her cevap anahtarında sorunun istediği sütunlar (`required_columns`); tek kural bütün iş testlerinde, açıklayıcı sütun eksikse modelin her sütunu eşleşmeli | 05 FAIL → PASS; 160 kayıtlı çıktıda başka sonuç değişmedi, kasıtlı yanlış çıktılar yine FAIL |

**Ana ders.** Bu 7B model örnekleri kurallardan güçlü takip ediyor (tarih aralığını, sütun sayısını da kopyalıyor). Kodla
üretilen notlar kurallardan etkili. Bir düzeltme başka testi bozabildiği için her değişiklik bütün setlerde ölçüldü.

## 3. Alternatifler

- **Model.** `qwen2.5-coder:7b`: ücretsiz, yerel, tek komutla kurulan, SQL'e yönelik, donanıma sığan. Ekip planındaki
  `qwen3:8b` **denenmedi ve ölçülmedi**. Ücretli API'ler değerlendirilmedi (ödev zorunlu tutmuyor, yerelde veri dışarı çıkmıyor).
- **Çerçeve.** LangChain / LlamaIndex yok; dört fonksiyonluk akış (generate → validate → execute → log) doğrudan Python ile.
- **Güvenlik.** Yalnızca prompt (kandırılabilir) veya yalnızca parser (kaçırabilir) yerine iki bağımsız katman: SQLGlot AST
  doğrulaması ve salt-okunur bağlantı + SQLite authorizer.
- **Tarih yorumu.** Modele hesaplatmak yerine kodla çözmek; tarih hatalarını kalıcı olarak giderdi.

## 4. İyileştirme önerileri

1. SQL komutuyla başlayıp ayrıştırılamayan girdiyi ("Select en çok satan…") doğal dil olarak modele göndermek.
2. Model şemada var olan bir tabloyu "yok" diyorsa bunu hata sayıp tek yeniden deneme hakkını kullanmak (05).
3. Ölçüm aracını (`docs/olcumler/karsilastir.py`) `run_all.py`'deki `columns_match`'e bağlayıp ölçümleri yeniden puanlamak.
4. WITH içinde `sqlite_master` ve `--` yorumu (elle denendi) `tests/test_security.py`'ye eklemek.
5. `qwen3:8b` vb. modelleri aynı ölçüm aracıyla üç sette ölçüp doğruluk ve süreyi birlikte raporlamak.
6. Soru setlerini çoğaltmak; few-shot örneklerini bunlardan bağımsız tutmak.
7. Bonus: SQL ile `assumption`'ı karşılaştıran öz-denetim turu, takip sorusu, grafik.
