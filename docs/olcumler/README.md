# Prompt geliştirme ölçümleri

Prompt'taki her değişikliğin etkisini ayrı ayrı görmek için test soruları her adımdan sonra modele soruldu.
Sonuçlar **gerçek model çıktısıdır** (`qwen2.5-coder:7b`, `temperature=0`, `format=json`); elle yazılmış veya mock sonuç yoktur.

Bu ölçümler resmi test raporu değildir (o: `tests/run_all.py`). Farklar: **yeniden deneme yok** (pipeline'dan daha katı) ve
karşılaştırma ([karsilastir.py](karsilastir.py)), CLAUDE.md ekip kararları 4–6'nın basit bir uygulamasıdır
(2 ondalık yuvarlama, 04/05/06 sırasız, model daha az sütun döndürdüyse esnek sütun eşleştirmesi).

| Dosya | Ne işe yarar |
|---|---|
| [olcum.py](olcum.py) | Ölçümü çalıştırır: `python docs/olcumler/olcum.py <etiket> [soru_dosyası]` |
| [karsilastir.py](karsilastir.py) | Model sonucunu cevap anahtarıyla karşılaştırır |
| [yeniden_puanla.py](yeniden_puanla.py) | Kayıtlı SQL'leri modeli çağırmadan yeniden çalıştırıp güncel karşılaştırmayla puanlar |
| [farkli_ifadeler.json](farkli_ifadeler.json), [farkli_ifadeler_2.json](farkli_ifadeler_2.json) | Gizli test hazırlığı: test 01–10'un farklı ifadeleri |

## Sonuçlar

| # | Dosya | Soru seti | Prompt | İş (01–08) | 09 | 10 | 11–16 |
|---|---|---|---|---|---|---|---|
| 0 | [00_baslangic.json](00_baslangic.json) | Test soruları | İlk sürüm; few-shot yok | **4/8** | clarify ✓ | unsupported ✓ | SQL çalışmadı ✓ |
| 1 | [01_kural_iliskiler.json](01_kural_iliskiler.json) | Test soruları | + varsayılan ölçüt kuralı + otomatik İlişkiler (JOIN) | **5/8** | ✓ | ✓ | ✓ |
| 2 | [02_fewshot.json](02_fewshot.json) | Test soruları | + 4 few-shot (2 ok, 1 clarify, 1 unsupported) | **8/8** | ✓ | ✓ | ✓ |
| 3 | [03_farkli_ifadeler.json](03_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 2 | **6/8** | ✓ | ✓ | — |
| 4 | [04_ay_kurali_test_sorulari.json](04_ay_kurali_test_sorulari.json) | Test soruları | + yılsız ay kuralı (REFERENCE_DATE'ten) + "en çok satan" = ciro | **7/8** | ✓ | ✓ | ✓ |
| 5 | [05_ay_kurali_farkli_ifadeler.json](05_ay_kurali_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 4 | **7/8** | ✓ | ✓ | — |
| 6 | [06_yeni_ifadeler.json](06_yeni_ifadeler.json) | Farklı ifadeler 2 | = adım 4 | **3/8** | ✓ | ✓ | — |
| 7 | [07_ifadeler2_duzeltilmis_eski_prompt.json](07_ifadeler2_duzeltilmis_eski_prompt.json) | Farklı ifadeler 2 **düzeltilmiş** (04, 06, 07) | = adım 4 | **6/8** | ✓ | ✓ | — |
| 8 | [08_semantik_test_sorulari.json](08_semantik_test_sorulari.json) | Test soruları | + semantik katman: tarih çözücü (Tarih notu) + metrik sözlüğü (eş anlamlılar) + Örnek 1'de somut tarih yerine "Mayıs ayında" | **7/8** | ✓ | ✓ | ✓ |
| 9 | [09_semantik_farkli_ifadeler.json](09_semantik_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 8 | **5/8** | ✓ | ✓ | — |
| 10 | [10_semantik_ifadeler2_duzeltilmis.json](10_semantik_ifadeler2_duzeltilmis.json) | Farklı ifadeler 2 düzeltilmiş | = adım 8 | **5/8** | ✓ | ✓ | — |
| 11 | [11_notlar_test_sorulari.json](11_notlar_test_sorulari.json) | Test soruları | + tarih yoksa "filtre ekleme" notu + metrik notu (riskli eş anlamlılar) + gruplamada LIMIT yok kuralı | **6/8** | ✓ | ✓ | ✓ |
| 12 | [12_notlar_farkli_ifadeler.json](12_notlar_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 11 | **6/8** | ✓ | ✓ | — |
| 13 | [13_notlar_ifadeler2_duzeltilmis.json](13_notlar_ifadeler2_duzeltilmis.json) | Farklı ifadeler 2 düzeltilmiş | = adım 11 | **5/8** | ✓ | ✓ | — |
| 14 | [14_aktif_test_sorulari.json](14_aktif_test_sorulari.json) | Test soruları | + "aktif müşteri" → son 90 gün tarih notu (Örnek 2'deki çelişki giderildi) | **7/8** | ✓ | ✓ | ✓ |
| 15 | [15_aktif_farkli_ifadeler.json](15_aktif_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 14 (**güncel**) | **7/8** | ✓ | ✓ | — |
| 16 | [16_aktif_ifadeler2_duzeltilmis.json](16_aktif_ifadeler2_duzeltilmis.json) | Farklı ifadeler 2 düzeltilmiş | = adım 14 (**güncel**) | **7/8** | ✓ | ✓ | — |

| 17 | [17_numctx8192_test_sorulari.json](17_numctx8192_test_sorulari.json) | Test soruları | + `num_ctx = 8192` (önceki ölçümler Ollama varsayılanı 4096); "işlem tutarı" eş anlamlılardan çıkarıldı | **7/8** (yalnız 04 FAIL, adım 14 ile aynı) | ✓ | ✓ | ✓ |

**Güncel durum (adım 14–17):** üç sette de 7/8; `num_ctx = 8192` sonucu değiştirmedi. Kalan hatalar her sette farklı: test soruları 04 (`LIMIT 1`),
farklı ifadeler 1 05 (`unsupported`), farklı ifadeler 2 08 (adet).

**Soru düzeltmesi (adım 7):** Farklı ifadeler 2'deki üç soru ödevdeki beklenen davranışla uyuşmuyordu ("Hangi segment
daha çok…" tek cevap istiyor; "ortalama satır tutarı" ve "Mart sonuna kadarki ilk üç ay" belirsiz). Eski SQL'ler eski sorulara
verilmiş cevaplar olduğundan yeniden puanlamak yerine düzeltilmiş sorular **aynı prompt'la (adım 4) yeniden soruldu**: 3/8 → 6/8.
Yani 3/8 düşüşünün yarısı soruların kendisinden kaynaklanıyordu. Orijinal dosya ([farkli_ifadeler_2.json](farkli_ifadeler_2.json))
değiştirilmedi; düzeltilmiş hali: [farkli_ifadeler_2_duzeltilmis.json](farkli_ifadeler_2_duzeltilmis.json).

Her ölçümde Customers satır sayısı 200 → 200 (hiçbir veri değişmedi). Davranış testleri (09, 10) her ölçümde doğru.

**Yeniden puanlama:** İlk karşılaştırmada esnek sütun eşleştirmesi hatalıydı: model 2 sütun döndürüp biri yanlış olduğunda
(doğru şehir + yanlış ciro) PASS sayılıyordu. Düzeltildikten sonra bütün dosyalar `yeniden_puanla.py` ile yeniden puanlandı
(model çağrılmadı, kayıtlı SQL'ler yeniden çalıştırıldı). Değişen tek sonuç: adım 4, test 07 PASS → FAIL (8/8 → 7/8).
Değişen dosyada `meta.rescored` alanı bunu açıklar.

## Gözlemler

- **0 → 1:** Model kuralları okuyor ama uygulamıyordu (02, 05'te var olan tabloları "yok" saydı; 06'da `Customers` JOIN'ini
  unuttu; 08'de birim fiyata göre sıraladı). İlişkiler bölümü 02'yi düzeltti.
- **1 → 2:** Few-shot örnekleri kalan üç hatayı düzeltti. Kuralı anlatmak yerine uygulanmış halini göstermek belirgin şekilde etkili.
- **Farklı ifadeler 1 (adım 3):** Yılı yazılmamış aylarda model yılı uydurdu (03: "Ocak'tan Haziran'a" → 2023; 08: "Haziranda"
  filtresi tamamen atlandı). "En çok satan" adete göre yorumlandı (assumption'da açıkça yazılı).
- **Ay kuralı (adım 4–5):** 03 düzeldi. Ancak orijinal 07'de "geçen çeyrek" için few-shot Örnek 1'in tarih aralığı
  (2025-10-01 – 2025-12-31) kopyalandı; adım 2'de doğruydu. "En çok satan" = ciro kuralına rağmen 08 adete göre sıralamaya devam etti.
- **Farklı ifadeler 2 (adım 6): 3/8.** Hatalar:
  - 03: karmaşık ifadede ("Şubat'tan Haziran'a ... Ocak da dahil") ay kuralı uygulanmadı, yıl 2025 seçildi.
  - 04: "ortalama satır tutarı" → `AVG(UnitPrice)`; eş anlamlı ifade metrik tanımıyla eşleştirilmedi.
  - 06: "Hangi segment daha çok ciro getiriyor?" tek cevap istediği için `LIMIT 1` döndü. **Model hatası değil**, soru
    test 06'dan farklı bir şey soruyor.
  - 07: "Mart sonuna kadarki ilk üç ay" için yine Örnek 1'in tarih aralığı kopyalandı.
  - 08: Haziran filtresi doğru, ama "en çok satılan" yine adete göre.
- **Semantik katman (adım 8):** Tarih çözücü tarih hatalarını kalıcı olarak çözdü: 03 ve 07 bu adımdan sonra her sette geçti.
  Ama iki yeni hata çıktı: (1) tarih içermeyen 06'ya `2026-04-02 – 06-30` filtresi eklendi; model "Tarih notundan alındı"
  yazıp olmayan bir notu uydurdu (Örnek 1'in yeni assumption metnini taklit edip Örnek 2'nin tarihini kullandı);
  (2) "kategori bazında" 04'e `LIMIT 1` eklendi.
- **Notlar (adım 11):** Tarih yoksa "filtre ekleme" notu 06'yı düzeltmedi. Neden: Örnek 2'nin sorusunda ("kaç aktif müşterimiz var")
  tarih ifadesi yok, bu yüzden ona da "filtre ekleme" notu eklendi; ama cevabı tanım gereği son 90 gün filtresi içeriyor.
  Örnek, modele "nota uyma" demiş oldu.
- **Aktif müşteri notu (adım 14):** Tarih çözücü "aktif" kelimesini görünce son 90 günü not olarak ekliyor; Örnek 2'nin sorusu,
  notu ve cevabı tutarlı hale geldi. 06 bütün setlerde düzeldi.
- **Kural ve notla çözülemeyenler:** "En çok satan / satılan" bazen ciroya, bazen adete göre sıralanıyor (aynı prompt'la farklı
  ifadelerde farklı sonuç; adım 12'de model notu okuyup "ciroya göre değil, SUM(Quantity)" diye açıkça tersini yazdı).
  Gruplama sorusuna `LIMIT 1` eklenmesi (04) kurala rağmen sürüyor. 05'te ilk ölçümdeki "sipariş verisi yok" hatası geri döndü.
  Bunlar için muhtemel çözüm, ilgili kalıbı gösteren bir few-shot örneği.
- **Ana ders:** Bu 7B model **örnekleri kurallardan daha güçlü takip ediyor**, örneklerdeki somut değerleri (tarih aralığı) de
  kopyalıyor. Prompt'a yazılan kurallar (ay kuralı, "en çok satan" = ciro) basit ifadelerde işe yarıyor, karmaşık ifadelerde
  uygulanmıyor. Kodla üretilen notlar (tarih, metrik) kurallardan daha etkili; ama örnek ile not çelişirse model örneği izliyor.
  Sonuçlar ifadeden ifadeye dalgalanıyor (aynı prompt'la bir sette geçen soru diğerinde kalıyor). Görünen sorulardaki
  7/8 sonucu gizli test setinde garanti değil; kurallar ve notlar bu sorulardaki hatalara bakılarak eklendi.
- **Bağlam penceresi:** Adım 16'ya kadar Ollama varsayılanı 4096 token; adım 14'teki prompt ≈ 3255 token (adım 4: 2777).
  Pencere aşılırsa Ollama prompt'un başını (sistem prompt'u) sessizce keser. Adım 17'den itibaren `num_ctx = 8192`
  (`ollama ps` ile doğrulandı); CPU payı %18 → %24 arttı, yanıt süreleri belirgin değişmedi.
- **Süre:** Model belleğe tam sığmadığı için %18'i CPU'da çalışıyor (`ollama ps`). Yanıtlar ölçüme göre 3–60 sn arası değişti;
  darboğaz üretim hızı (~10 token/sn).
