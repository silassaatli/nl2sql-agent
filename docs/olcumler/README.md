# Prompt geliştirme ölçümleri

Prompt'taki her değişikliğin etkisini ayrı ayrı görmek için 16 test sorusu her adımdan sonra modele soruldu.
Sonuçlar **gerçek model çıktısıdır** (`qwen2.5-coder:7b`, `temperature=0`, `format=json`); elle yazılmış veya mock sonuç yoktur.

Bu ölçümler resmi test raporu değildir (o: `tests/run_all.py`). Farklar: **yeniden deneme yok** (pipeline'dan daha katı) ve
karşılaştırma, CLAUDE.md ekip kararları 4–6'nın basit bir uygulamasıdır (2 ondalık yuvarlama, 04/05/06 sırasız, eksik sütunda esnek eşleştirme).

Yeniden çalıştırma (proje kökünden): `python docs/olcumler/olcum.py <etiket>`

## Sonuçlar

| Adım | Dosya | Prompt'ta ne değişti | İş (01–08) | 09 | 10 | 11–16 |
|---|---|---|---|---|---|---|
| 0 | [00_baslangic.json](00_baslangic.json) | İlk sürüm: rol, şema, metrikler, tarih aralıkları, kurallar, JSON formatı. Few-shot yok | **4/8** (01, 03, 04, 07) | clarify ✓ | unsupported ✓ | SQL çalışmadı ✓ |
| 1 | [01_kural_iliskiler.json](01_kural_iliskiler.json) | + Varsayılan ölçüt kuralı ("ilk N / en yüksek" → ciro, assumption'a yazılır; "en iyi / en değerli" → clarify) + şemadan otomatik **İlişkiler (JOIN koşulları)** bölümü | **5/8** (+02) | clarify ✓ | unsupported ✓ | SQL çalışmadı ✓ |
| 2 | [02_fewshot.json](02_fewshot.json) | + 4 few-shot örnek (2 ok, 1 clarify, 1 unsupported; test sorularının kopyası değil) | **8/8** | clarify ✓ | unsupported ✓ | SQL çalışmadı ✓ |

Her ölçümde Customers satır sayısı 200 → 200 (hiçbir veri değişmedi).

## Gözlemler

- **Adım 0 → 1:** Model kuralları okuyor ama uygulamıyordu. 02 ve 05'te var olan tabloları/sütunları "yok" sayıp `unsupported`
  döndü; 06'da `Customers` JOIN'ini unuttu; 08'de "ilk 3 ürün"ü birim fiyata göre sıraladı. İlişkiler bölümü 02'yi düzeltti.
  Varsayılan ölçüt kuralı 08'i düzeltmedi; 06'da ise kuralı fazla uygulayıp "karşılaştırma" sorusuna `LIMIT 1` ekledi.
- **Adım 1 → 2:** Few-shot örnekleri kalan üç hatayı (05, 06, 08) düzeltti. Kuralı anlatmak yerine uygulanmış halini göstermek
  küçük modelde belirgin şekilde daha etkili oldu. Örnek 1 "2025'in son çeyreği"ni içerdiği hâlde 07'de "geçen çeyrek" için
  doğru aralık (2026 Q1) kullanıldı.
- **Bağlam penceresi:** Ollama modeli 4096 token pencereyle çalıştırıyor; adım 2'deki prompt (sistem + 4 örnek + soru) ≈ 2385 token.
  Pencere aşılırsa Ollama prompt'un başını (sistem prompt'u) sessizce keser; prompt büyütülürken bu sınır izlenmeli.
- **Süre:** Adım 2'de yanıtlar 12–60 sn. Darboğaz üretim (~10 token/sn): model belleğe tam sığmadığı için %18'i CPU'da çalışıyor
  (`ollama ps`). Few-shot örnekleri daha uzun assumption/message yazdırdığı için üretilen token sayısı arttı.
- **Sınırlılık:** 8/8 sonucu görünen test sorularında alındı; kurallar bu sorulardaki hatalara bakılarak eklendi. Gizli test seti
  farklı formülasyonlar kullanacağı için aynı soruların farklı ifadeleriyle ayrıca ölçülmeli.
