# Teknik değerlendirme

NL2SQL Agent · ENS-AI-001 · Sıla Saatlı, Taha Yavaş [KONTROL: Kişi A'nın adı]

**Sonuç.** Resmi raporda ([test_report.md](test_report.md), gerçek model, mock yok) iş soruları 7/8 (eşik 6/8), davranış
2/2, güvenlik 6/6. Modele giden 13 testin uçtan uca süresi ortalama 9,3 sn, medyan 7,2 sn. Model `qwen2.5-coder:7b` (Ollama, yerel),
`temperature=0`, prompt ≈ 3446 token, `num_ctx=8192`.

## 1. Sınırlılıklar

- **Model doğruluğu ifadeye bağlı.** Aynı soru farklı ifade edilince sonuç değişiyor: son prompt'la üç ölçüm setinde 7/8,
  8/8, 7/8; önceki bir sürümde "farklı ifadeler 2" seti 2/8 ([olcumler/README.md](olcumler/README.md)). Görünen
  sorulardaki başarı gizli test setinde garanti değil; kurallar ve örnekler görülen hatalara bakılarak eklendi.
- **Test 05 FAIL.** Model doğru 12 müşteriyi buluyor ama yalnızca `CustomerID, Name` döndürüyor; cevap anahtarındaki `City`
  eksik. Ara sıra var olan `Orders` tablosunu "yok" sayıp `unsupported` da döndürüyor. `unsupported` bir hata sayılmadığı için
  yeniden deneme bunu yakalamıyor.
- **Doğal dil güvenlik testlerinde reddi veren model.** Doğrudan SQL girdileri (12, 14, 16) artık modele gitmeden
  validator'da işleniyor, ama doğal dil girdilerinde (11, 13, 15) model SQL üretmeden `unsupported` döndürdü; bu üç testte
  validator'a SQL ulaşmadı. Model kandırılıp SQL üretseydi validator ve authorizer devreye girerdi; bu katmanlar
  `tests/test_security.py` ile ayrıca doğrulanıyor (10/10 PASS).
- **Doğrudan SQL tespiti ilk kelimeye bakıyor.** "Select en çok satan 5 ürün" gibi SQL kelimesiyle başlayan bir Türkçe soru
  modele gitmez, `parse_error` döner. Güvenlik açığı değil (girdi yine validator'dan geçer), kullanılabilirlik sınırı.
- **Varsayım metni doğrulanmıyor.** `assumption` modelin kendi açıklaması; "İzmir'in toplam cirosu"nda SQL tarih filtresi
  içermediği hâlde model "tarih filtresi eklendi" yazdı. Doğruluk için esas olan SQL'dir; arayüz bunu not olarak gösteriyor.
- **Semantik katman kural tabanlı.** "Geçen Kasım", "yılbaşından beri" gibi ifadeler tanınmıyor; yılsız "son çeyrek" bilerek
  çözülmüyor.
- **Donanım.** 6 GB VRAM'e model ve bağlam belleği birlikte sığmıyor (`ollama ps`: %76 GPU / %24 CPU). Tek kullanıcılı bir
  PoC için yeterli; eşzamanlı kullanıcı veya daha büyük model için yetersiz.
- **Kapsam.** Tek tablo seti, tek SELECT; takip sorusu, grafik, çok adımlı planlama yok (bonus, yapılmadı).

## 2. Karşılaşılan sorunlar ve çözümleri

Prompt 21 ölçümle, her değişiklikten sonra yeniden deneme olmadan geliştirildi; iş soruları 4/8'den 7/8'e çıktı.

| Sorun | Çözüm | Etki (ölçüm) |
|---|---|---|
| Model var olan tabloları "yok" saydı, JOIN'leri unuttu | Şemaya FK'lerden üretilen hazır JOIN koşulları | 4/8 → 5/8 |
| Kurallar yazılı olduğu hâlde uygulanmadı | 4 few-shot örneği (2 ok, 1 clarify, 1 unsupported) | 5/8 → 7/8 |
| Yılsız ay adlarında yıl uyduruldu; "geçen çeyrek" için few-shot örneğinin tarih aralığı (2025 Q4) kopyalandı | Tarih çözücü: aralık kodla hesaplanıp soruya "Tarih notu" olarak eklenir | 03 ve 07 sonraki bütün setlerde geçti |
| Tarih içermeyen soruya filtre eklendi (model olmayan bir notu uydurdu) | "Tarih filtresi ekleme" notu + "aktif müşteri" için son 90 gün notu | 06 bütün setlerde düzeldi |
| "En çok satan" adete göre, "ortalama satır tutarı" `AVG(UnitPrice)` olarak okundu | Metrik sözlüğü ve riskli eş anlamlılar için "Metrik notu" | 08 son ölçümlerde ciroya göre |
| "Kategori bazında" sorusuna `LIMIT 1` | 5. few-shot örneği: gruplama, LIMIT yok | 04 düzeldi, ama 05 eksik sütunla bozuldu; üç setin toplamı 20/24 → 22/24 olduğu için örnek tutuldu |
| Prompt büyüdükçe Ollama'nın 4096 token'lık varsayılan penceresi yetmeyebilirdi (aşılırsa sistem prompt'u sessizce kesilir) | `num_ctx = 8192` | Prompt ≈ 3446 token, pay yeterli |
| Doğrudan SQL girdileri (12, 14, 16) de modele gidiyordu; model `unsupported` döndürdüğü için validator'a hiç ulaşmıyorlardı | `SQL_START` regex'i: SQL komutuyla başlayan girdi modele gitmeden validator'a verilir (Kişi A) | 12 ve 16 `multiple_statements` ile reddedildi, 14'te yalnızca temiz SELECT çalıştı |
| Ölçüm aracı yanlış PASS veriyordu: doğru şehir + yanlış ciro, ve eksik sütunun her testte kabulü | Karşılaştırma `run_all.py` ile aynı kurala getirildi, kayıtlı SQL'ler modeli çağırmadan yeniden puanlandı | Bazı eski puanlar düştü (ör. adım 2: 8/8 → 7/8); düzeltilmiş puanlar yayımlandı |

**Ana ders.** Bu 7B model örnekleri kurallardan daha güçlü takip ediyor; örnekteki tarih aralığını ve sütun sayısını da
kopyalıyor. Kodla üretilen notlar (tarih, metrik) kurallardan daha etkili. Bir hatayı düzelten örnek başka bir testi
bozabildiği için her değişiklik bütün setlerde ölçüldü.

## 3. Alternatifler

- **Model.** `qwen2.5-coder:7b` seçildi: ücretsiz, yerel, tek komutla kurulan, SQL'e yönelik ve donanıma sığan bir model.
  Ekip planındaki `qwen3:8b` (Türkçesi daha iyi olarak önerilen) **denenmedi ve ölçülmedi**. Ücretli API modelleri
  değerlendirilmedi: ödev ücretli lisans veya API'yi zorunlu tutmuyor, yerel çözümde de veri makineden çıkmıyor.
- **Çerçeve.** LangChain / LlamaIndex kullanılmadı. Akış dört fonksiyonluk (generate → validate → execute → log) ve doğrudan
  Python ile her satırı açıklanabiliyor; bağımlılıklar `sqlglot`, `streamlit`, `ollama`, `pytest` ile sınırlı.
- **Güvenlik.** Yalnızca prompt kuralı (model kandırılabilir) veya yalnızca parser (kaçırabilir) yerine iki bağımsız katman:
  SQLGlot AST doğrulaması ve salt-okunur bağlantı + SQLite authorizer.
- **Tarih yorumu.** Göreli tarihleri modele hesaplatmak yerine kodla çözmek seçildi; ölçümlerde tarih hatalarını kalıcı olarak
  giderdi.

## 4. İyileştirme önerileri

1. **Doğrudan SQL tespitini daraltmak:** girdi SQL komutuyla başlıyor ama SQLGlot ayrıştıramıyorsa (ör. "Select en çok
   satan 5 ürün") hata vermek yerine doğal dil olarak modele göndermek. Güvenlik değişmez, çünkü modelin SQL'i de aynı
   validator'dan geçer. (Doğrudan SQL'i modele göndermeden validator'a verme önerisi uygulandı; 12 ve 16 artık
   `multiple_statements` ile reddediliyor.)
2. **`unsupported` iddiasını kodla denetlemek:** model şemada var olan bir tabloyu "yok" diyorsa bu bir hata sayılıp tek
   yeniden deneme hakkı kullanılabilir (05'teki ara sıra görülen hata).
3. **Listeleme sorularında tanımlayıcı sütunlar:** "kimler?" gibi sorularda ad ve şehir gibi ayırt edici sütunları göstermeyi
   isteyen bir kural veya örnek (05'teki eksik `City`). Etkisi bütün setlerde ölçülmeli; önceki örnek deneyimi bir düzeltmenin
   başka testi bozabileceğini gösterdi.
4. **Güvenlik birim testlerini genişletmek:** WITH içinde `sqlite_master` ve `--` satır yorumu elle denendi (doğru
   reddediliyor / temizleniyor) ama `tests/test_security.py`'de yok.
5. **Model karşılaştırması:** `qwen3:8b` ve benzerlerini aynı ölçüm aracıyla ([olcumler/olcum.py](olcumler/olcum.py)) üç soru
   setinde ölçmek; doğruluk ile süreyi birlikte raporlamak.
6. **Daha geniş gizli test hazırlığı:** soru setlerini çoğaltmak ve few-shot örneklerini bu setlerden bağımsız tutmak.
7. **Bonus (çekirdekten sonra):** SQL ile `assumption`'ı karşılaştıran öz-denetim turu, netleştirme sonrası takip sorusu,
   sonuç grafiği.
