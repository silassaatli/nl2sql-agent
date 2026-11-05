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
- **Ana ders:** Bu 7B model **örnekleri kurallardan daha güçlü takip ediyor**, örneklerdeki somut değerleri (tarih aralığı) de
  kopyalıyor. Prompt'a yazılan kurallar (ay kuralı, "en çok satan" = ciro) basit ifadelerde işe yarıyor, karmaşık ifadelerde
  uygulanmıyor. Görünen test sorularındaki 7–8/8 sonucu gizli test setinde garanti değil.
- **Bağlam penceresi:** Ollama 4096 token pencereyle çalışıyor; adım 4'teki prompt ≈ 2777 token. Pencere aşılırsa Ollama
  prompt'un başını (sistem prompt'u) sessizce keser.
- **Süre:** Model belleğe tam sığmadığı için %18'i CPU'da çalışıyor (`ollama ps`). Yanıtlar ölçüme göre 3–60 sn arası değişti;
  darboğaz üretim hızı (~10 token/sn).
