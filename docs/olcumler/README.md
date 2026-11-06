# Prompt geliştirme ölçümleri

Prompt'taki her değişikliğin etkisini ayrı ayrı görmek için test soruları her adımdan sonra modele soruldu.
Sonuçlar **gerçek model çıktısıdır** (`qwen2.5-coder:7b`, `temperature=0`, `format=json`); elle yazılmış veya mock sonuç yoktur.

Bu ölçümler resmi test raporu değildir (o: `tests/run_all.py` → [../test_report.md](../test_report.md)). Fark: **yeniden deneme yok**
(pipeline'dan daha katı). Karşılaştırma ([karsilastir.py](karsilastir.py)) ekip kararlarını `run_all.py`'nin
2026-11-06 öncesi kuralıyla uygular (güncel kural: ana README → Testler; farkı yalnızca test 05'i etkiler): 2 ondalık yuvarlama; 01/03/08 sıralı, 04/05/06 sırasız; eksik sütun yalnızca 01/07/08'de ve ürün/şehir
sütunu dönmüşse; fazla sütun, beklenen sütunların hepsi doğru değerlerle varsa kabul.

| Dosya | Ne işe yarar |
|---|---|
| [olcum.py](olcum.py) | Ölçümü çalıştırır: `python docs/olcumler/olcum.py <etiket> [soru_dosyası]` |
| [karsilastir.py](karsilastir.py) | Model sonucunu cevap anahtarıyla karşılaştırır |
| [yeniden_puanla.py](yeniden_puanla.py) | Kayıtlı SQL'leri modeli çağırmadan yeniden çalıştırıp güncel karşılaştırmayla puanlar |
| [farkli_ifadeler.json](farkli_ifadeler.json), [farkli_ifadeler_2.json](farkli_ifadeler_2.json), [farkli_ifadeler_2_duzeltilmis.json](farkli_ifadeler_2_duzeltilmis.json) | Gizli test hazırlığı: test 01–10'un farklı ifadeleri |

## Sonuçlar

Puanlar, aşağıdaki "Yeniden puanlama" bölümündeki düzeltmelerden sonraki değerlerdir.

| # | Dosya | Soru seti | Prompt | İş (01–08) | 09 | 10 | 11–16 |
|---|---|---|---|---|---|---|---|
| 0 | [00_baslangic.json](00_baslangic.json) | Test soruları | İlk sürüm; few-shot yok | **4/8** | clarify ✓ | unsupported ✓ | SQL çalışmadı ✓ |
| 1 | [01_kural_iliskiler.json](01_kural_iliskiler.json) | Test soruları | + varsayılan ölçüt kuralı + otomatik İlişkiler (JOIN) | **5/8** | ✓ | ✓ | ✓ |
| 2 | [02_fewshot.json](02_fewshot.json) | Test soruları | + 4 few-shot (2 ok, 1 clarify, 1 unsupported) | **7/8** | ✓ | ✓ | ✓ |
| 3 | [03_farkli_ifadeler.json](03_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 2 | **6/8** | ✓ | ✓ | — |
| 4 | [04_ay_kurali_test_sorulari.json](04_ay_kurali_test_sorulari.json) | Test soruları | + yılsız ay kuralı (REFERENCE_DATE'ten) + "en çok satan" = ciro | **6/8** | ✓ | ✓ | ✓ |
| 5 | [05_ay_kurali_farkli_ifadeler.json](05_ay_kurali_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 4 | **7/8** | ✓ | ✓ | — |
| 6 | [06_yeni_ifadeler.json](06_yeni_ifadeler.json) | Farklı ifadeler 2 | = adım 4 | **2/8** | ✓ | ✓ | — |
| 7 | [07_ifadeler2_duzeltilmis_eski_prompt.json](07_ifadeler2_duzeltilmis_eski_prompt.json) | Farklı ifadeler 2 **düzeltilmiş** (04, 06, 07) | = adım 4 | **5/8** | ✓ | ✓ | — |
| 8 | [08_semantik_test_sorulari.json](08_semantik_test_sorulari.json) | Test soruları | + semantik katman: tarih çözücü (Tarih notu) + metrik sözlüğü (eş anlamlılar) + Örnek 1'de somut tarih yerine "Mayıs ayında" | **6/8** | ✓ | ✓ | ✓ |
| 9 | [09_semantik_farkli_ifadeler.json](09_semantik_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 8 | **5/8** | ✓ | ✓ | — |
| 10 | [10_semantik_ifadeler2_duzeltilmis.json](10_semantik_ifadeler2_duzeltilmis.json) | Farklı ifadeler 2 düzeltilmiş | = adım 8 | **4/8** | ✓ | ✓ | — |
| 11 | [11_notlar_test_sorulari.json](11_notlar_test_sorulari.json) | Test soruları | + tarih yoksa "filtre ekleme" notu + metrik notu (riskli eş anlamlılar) + gruplamada LIMIT yok kuralı | **5/8** | ✓ | ✓ | ✓ |
| 12 | [12_notlar_farkli_ifadeler.json](12_notlar_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 11 | **6/8** | ✓ | ✓ | — |
| 13 | [13_notlar_ifadeler2_duzeltilmis.json](13_notlar_ifadeler2_duzeltilmis.json) | Farklı ifadeler 2 düzeltilmiş | = adım 11 | **4/8** | ✓ | ✓ | — |
| 14 | [14_aktif_test_sorulari.json](14_aktif_test_sorulari.json) | Test soruları | + "aktif müşteri" → son 90 gün tarih notu (Örnek 2'deki çelişki giderildi) | **7/8** | ✓ | ✓ | ✓ |
| 15 | [15_aktif_farkli_ifadeler.json](15_aktif_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 14 | **7/8** | ✓ | ✓ | — |
| 16 | [16_aktif_ifadeler2_duzeltilmis.json](16_aktif_ifadeler2_duzeltilmis.json) | Farklı ifadeler 2 düzeltilmiş | = adım 14 | **6/8** | ✓ | ✓ | — |
| 17 | [17_numctx8192_test_sorulari.json](17_numctx8192_test_sorulari.json) | Test soruları | + `num_ctx = 8192` (önceki ölçümler Ollama varsayılanı 4096); "işlem tutarı" eş anlamlılardan çıkarıldı | **7/8** | ✓ | ✓ | ✓ |
| 18 | [18_ornek5_test_sorulari.json](18_ornek5_test_sorulari.json) | Test soruları | + 5. few-shot: "Şehir bazında sipariş adetlerini göster." (gruplama, LIMIT yok) (**güncel**) | **7/8** | ✓ | ✓ | ✓ |
| 19 | [19_ornek5_farkli_ifadeler.json](19_ornek5_farkli_ifadeler.json) | Farklı ifadeler 1 | = adım 18 (**güncel**) | **8/8** | ✓ | ✓ | — |
| 20 | [20_ornek5_ifadeler2_duzeltilmis.json](20_ornek5_ifadeler2_duzeltilmis.json) | Farklı ifadeler 2 düzeltilmiş | = adım 18 (**güncel**) | **7/8** | ✓ | ✓ | — |

Her ölçümde Customers satır sayısı 200 → 200 (hiçbir veri değişmedi). Davranış testleri (09, 10) her ölçümde doğru.

## 5. few-shot örneği: önce / sonra (güncel karar)

Amaç 04'teki `LIMIT 1` hatasıydı. Aynı karşılaştırma kuralıyla (yeniden puanlama sonrası):

| Set | Örnek öncesi | Örnek sonrası | Değişen |
|---|---|---|---|
| Test soruları | 7/8 (adım 17; 04 FAIL) | 7/8 (adım 18; 05 FAIL) | 04 düzeldi, **05 bozuldu** |
| Farklı ifadeler 1 | 7/8 (adım 15; 05 FAIL) | 8/8 (adım 19) | 05 düzeldi |
| Farklı ifadeler 2 düzeltilmiş | 6/8 (adım 16; 05, 08 FAIL) | 7/8 (adım 20; 05 FAIL) | 08 düzeldi |
| **Toplam (3 set)** | **20/24** | **22/24** | +2 |
| Resmi `run_all.py` | 7/8 (04 FAIL) | 7/8 (05 FAIL) | aynı |

**Karar:** Örnek tutuldu. Resmi sonuç iki durumda da 7/8, ama üç setin toplamı 20/24 → 22/24 çıktığı için gizli test setine
daha iyi hazırlık sayıldı.

**05'teki yeni hata (eksik sütun):** Örnekten sonra model test 05'te ("Hiç sipariş vermemiş müşteriler kimler?") doğru 12 müşteriyi
buluyor ama yalnızca `CustomerID, Name` döndürüyor; cevap anahtarındaki `City` sütunu yok. Eksik sütun kuralı (madde 6) sadece
"hangi ürün/şehir?" soruları (01/07/08) için geçerli olduğundan 05 FAIL. Örnekten önce aynı soruda model 3 (bazen 4) sütun
döndürüyordu. Muhtemel neden: yeni örnek iki sütunlu (`City, SiparisAdedi`) bir sonuç gösteriyor.

## Yeniden puanlama (ölçüm aracındaki hatalar)

`yeniden_puanla.py` kayıtlı SQL'leri modeli çağırmadan yeniden çalıştırıp güncel karşılaştırmayla puanlar; model çıktısı değişmez.
Değişen dosyalarda `meta.rescored` alanı nedenini ve önceki puanı açıklar. İki hata düzeltildi:

1. **Doğru şehir + yanlış ciro PASS sayılıyordu.** Model beklenen kadar sütun döndürüp biri yanlış olduğunda esnek eşleştirme
   devreye giriyordu. Düzeltme sonrası değişen tek sonuç: adım 4, test 07 PASS → FAIL.
2. **Eksik sütun bütün testlerde kabul ediliyordu.** Madde 6 bunu yalnızca 01/07/08 için tanımlıyor; `run_all.py` de öyle uyguluyor.
   Bu fark adım 18'de fark edildi: ölçüm 05'i PASS, resmi rapor aynı SQL'i FAIL saydı. Düzeltme sonrası adım 2, 4, 6, 7, 8, 10, 11,
   13, 16, 18 ve 20'de test 05 PASS → FAIL (model bu ölçümlerde 05'e 2 sütun döndürmüştü). Yeniden puanlama betiği ilk denemede
   yalnızca `0*.json` dosyalarını okuyordu; kalıp düzeltilip 10–20 de puanlandı.

Sonuç: ilk sürümde yayınlanan bazı puanlar (ör. adım 2 "8/8", adım 14–16 "üç sette de 7/8") gerçeğinden yüksekti. Tablo düzeltilmiş
puanları gösterir.

**Soru düzeltmesi (adım 7):** Farklı ifadeler 2'deki üç soru ödevdeki beklenen davranışla uyuşmuyordu ("Hangi segment
daha çok…" tek cevap istiyor; "ortalama satır tutarı" ve "Mart sonuna kadarki ilk üç ay" belirsiz). Eski SQL'ler eski sorulara
verilmiş cevaplar olduğundan yeniden puanlamak yerine düzeltilmiş sorular **aynı prompt'la (adım 4) yeniden soruldu**: 2/8 → 5/8.
Orijinal dosya ([farkli_ifadeler_2.json](farkli_ifadeler_2.json)) değiştirilmedi.

## Gözlemler

- **0 → 1:** Model kuralları okuyor ama uygulamıyordu (02, 05'te var olan tabloları "yok" saydı; 06'da `Customers` JOIN'ini
  unuttu; 08'de birim fiyata göre sıraladı). İlişkiler bölümü 02'yi düzeltti.
- **1 → 2:** Few-shot örnekleri 06 ve 08'i düzeltti, 05'i SQL üretir hale getirdi (ama 2 sütunla). Kuralı anlatmak yerine
  uygulanmış halini göstermek belirgin şekilde etkili.
- **Farklı ifadeler 1 (adım 3):** Yılı yazılmamış aylarda model yılı uydurdu (03: "Ocak'tan Haziran'a" → 2023; 08: "Haziranda"
  filtresi tamamen atlandı). "En çok satan" adete göre yorumlandı (assumption'da açıkça yazılı).
- **Ay kuralı (adım 4–5):** 03 düzeldi. Ancak orijinal 07'de "geçen çeyrek" için few-shot Örnek 1'in tarih aralığı
  (2025-10-01 – 2025-12-31) kopyalandı. "En çok satan" = ciro kuralına rağmen 08 adete göre sıralamaya devam etti.
- **Farklı ifadeler 2 (adım 6):** 03'te karmaşık ifadede yıl yanlış; 04'te "ortalama satır tutarı" → `AVG(UnitPrice)`; 06 soru tek
  cevap istediği için `LIMIT 1` (**model hatası değil**); 07'de yine Örnek 1'in tarih aralığı; 08 adete göre.
- **Semantik katman (adım 8):** Tarih çözücü tarih hatalarını kalıcı olarak çözdü: 03 ve 07 bu adımdan sonra her sette geçti.
  Ama iki yeni hata çıktı: tarih içermeyen 06'ya `2026-04-02 – 06-30` filtresi eklendi (model "Tarih notundan alındı" yazıp olmayan
  bir notu uydurdu) ve "kategori bazında" 04'e `LIMIT 1` eklendi.
- **Notlar (adım 11):** Tarih yoksa "filtre ekleme" notu 06'yı düzeltmedi: Örnek 2'nin sorusunda tarih ifadesi yok ama cevabı tanım
  gereği son 90 gün filtresi içeriyor; örnek modele "nota uyma" demiş oldu.
- **Aktif müşteri notu (adım 14):** Tarih çözücü "aktif" kelimesini görünce son 90 günü not olarak ekliyor; 06 bütün setlerde düzeldi.
- **5. örnek (adım 18–20):** 04'teki `LIMIT 1` düzeldi; 08 (adet) düzeldi; 05'te eksik sütun hatası ortaya çıktı (yukarıda).
- **Ana ders:** Bu 7B model **örnekleri kurallardan daha güçlü takip ediyor**, örneklerdeki somut değerleri (tarih aralığı, sütun
  sayısı) de kopyalıyor. Kodla üretilen notlar (tarih, metrik) kurallardan daha etkili; ama örnek ile not çelişirse model örneği
  izliyor. Bir hatayı düzelten örnek başka bir testi bozabiliyor (05). Sonuçlar ifadeden ifadeye dalgalanıyor; görünen sorulardaki
  sonuç gizli test setinde garanti değil, kurallar ve örnekler bu sorulardaki hatalara bakılarak eklendi.
- **Bağlam penceresi:** Adım 16'ya kadar Ollama varsayılanı 4096 token. Pencere aşılırsa Ollama prompt'un başını (sistem prompt'u)
  sessizce keser. Adım 17'den itibaren `num_ctx = 8192` (`ollama ps` ile doğrulandı); prompt adım 18'de ≈ 3446 token.
- **Süre:** Model belleğe tam sığmıyor (`ollama ps`: num_ctx 4096'da %18, 8192'de %24 CPU). Yanıtlar genelde 2–10 sn, model
  belleğe ilk yüklenirken ~15 sn; bazı ölçümlerde 60 sn'ye kadar çıktı. Darboğaz üretim hızı (~10 token/sn).
