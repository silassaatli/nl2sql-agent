# Golden set değerlendirme raporu

Üretim: 2026-11-20T13:36:34 · Model: `gemini-3.5-flash-lite` · Bayraklar: `{'SELF_CORRECTION': False, 'SELF_CORRECTION_MAX_RETRIES': 2}` · Kod özeti: `f1857f6a79` · Komut: `python eval/run_eval.py --self-correction both`

Sonuçlar gerçek model çıktısıdır (mock yok). Beklenen sonuçlar her koşuda gold_sql'den yeniden hesaplandı.
Kapsam: 45 soru (bütün golden set) · önbellekten gelen: 0

## Özet

| Ölçü | Değer |
|---|---|
| **Genel doğruluk** | **%97.8 (44/45)** |
| PASS / FAIL / INFRA / SKIP | 44 / 1 / 0 / 0 |
| Gecikme ort. / medyan / p95 | 1710 / 1349 / 3335 ms |
| Pipeline yeniden denemeleri | 0 |
| Yeniden denemeyle düzelen (PASS) | 0 |
| 429/5xx backoff tekrarları | 8 |

INFRA: kota/ağ hatası, SKIP: gold_sql henüz yazılmadı. İkisi doğruluk paydasına girmez.

## Zorluğa göre

| Grup | Doğruluk |
|---|---|
| kolay | %100.0 (12/12) |
| orta | %100.0 (22/22) |
| zor | %90.9 (10/11) |

## Beklenen davranışa göre

| Grup | Doğruluk |
|---|---|
| clarify | %100.0 (4/4) |
| refuse | %100.0 (3/3) |
| sql | %97.4 (37/38) |

## Etikete göre

| Grup | Doğruluk |
|---|---|
| aggregation | %100.0 (25/25) |
| alt_sorgu | %100.0 (3/3) |
| anti_join | %100.0 (2/2) |
| belirsiz | %100.0 (4/4) |
| cevaplanamaz | %100.0 (2/2) |
| churn | %100.0 (1/1) |
| filtre | %100.0 (5/5) |
| gelir | %92.9 (13/14) |
| goreli_tarih | %100.0 (1/1) |
| join | %92.9 (13/14) |
| kosullu_aggregation | %100.0 (1/1) |
| kumulatif | %100.0 (1/1) |
| lag | %100.0 (2/2) |
| left_join | %100.0 (3/3) |
| oran | %100.0 (4/4) |
| paraphrase | %100.0 (3/3) |
| row_number | %0.0 (0/1) |
| self_join | %100.0 (1/1) |
| siralama | %100.0 (6/6) |
| tarih | %100.0 (10/10) |
| tek_tablo | %100.0 (11/11) |
| window | %83.3 (5/6) |
| zararli | %100.0 (1/1) |

## Başarısız sorular

### G30 · zor · FAIL

- **Soru:** Her kategoride en çok ciro getiren ürün hangisi?
- **Durum:** success / None
- **Neden:** Satır sayısı: beklenen 6, gelen 32.
- **Varsayım:** Her kategori için en çok ciro getiren ürünler istendiği için tüm ürünlerin kategorilerine göre ciroları hesaplandı ve sıralandı.
- **Üretilen SQL:**

```sql
SELECT p.Category, p.ProductName, SUM(oi.Quantity * oi.UnitPrice) AS Ciro FROM Products AS p JOIN OrderItems AS oi ON p.ProductID = oi.ProductID GROUP BY p.Category, p.ProductID ORDER BY p.Category, Ciro DESC
```
- **Gold SQL:**

```sql
WITH urun AS (SELECT p.Category, p.ProductName, ROW_NUMBER() OVER (PARTITION BY p.Category ORDER BY SUM(oi.Quantity * oi.UnitPrice) DESC) AS Sira FROM OrderItems oi JOIN Products p ON p.ProductID = oi.ProductID GROUP BY p.ProductID) SELECT Category, ProductName FROM urun WHERE Sira = 1 ORDER BY Category
```
- **Beklenen (ilk satırlar, 6 satır):** `[['Döviz ve Hazine', 'Akreditif Komisyonu'], ['Kart ve Ödeme', 'Sanal POS Paketi'], ['Kredi Ürünleri', 'Ticari Kredi Tahsis Ücreti']]`
- **Gelen (ilk satırlar, 32 satır):** `[['Döviz ve Hazine', 'Akreditif Komisyonu', 9353874.3], ['Döviz ve Hazine', 'Forward Sözleşme Komisyonu', 8212098.7], ['Döviz ve Hazine', 'Swap İşlem Komisyonu', 5100043.5200000005]]`

## Bütün sorular

| No | Zorluk | Beklenen | Soru | Durum | Sonuç | Süre (ms) |
|---|---|---|---|---|---|---|
| G01 | kolay | sql | Kaç müşterimiz var? | success | PASS | 3335 |
| G02 | kolay | sql | Her şehirde kaç müşterimiz var? | success | PASS | 2532 |
| G03 | kolay | sql | Segmentlere göre müşteri sayısı nedir? | success | PASS | 2155 |
| G04 | kolay | sql | Kurumsal segmentteki müşterileri listele. | success | PASS | 4669 |
| G05 | kolay | sql | Ürün kataloğunda kaç farklı kategori var? | success | PASS | 1357 |
| G06 | kolay | sql | Liste fiyatı en yüksek 3 ürün hangileri? | success | PASS | 1198 |
| G07 | kolay | sql | Sigorta kategorisindeki ürünleri liste fiyatlarıyla birlikt… | success | PASS | 1352 |
| G08 | kolay | sql | Toplam kaç sipariş alındı? | success | PASS | 6982 |
| G09 | kolay | sql | 2025 Aralık ayında kaç sipariş verildi? | success | PASS | 1426 |
| G10 | kolay | sql | Kategorilere göre ortalama liste fiyatı nedir? | success | PASS | 1256 |
| G11 | kolay | sql | Tek bir sipariş kaleminde satılan en yüksek adet kaçtır? | success | PASS | 1345 |
| G12 | orta | sql | Kategorilere göre toplam ciro nedir? | success | PASS | 950 |
| G13 | orta | sql | 2026'nın ilk çeyreğinde Kurumsal segmentin cirosu ne kadar? | success | PASS | 1841 |
| G14 | orta | sql | Her ürünün toplam satış adedini göster. | success | PASS | 2086 |
| G15 | orta | sql | Her müşterinin sipariş sayısını göster; hiç siparişi olmaya… | success | PASS | 1203 |
| G16 | orta | sql | Sipariş başına ortalama tutar nedir? | success | PASS | 2065 |
| G17 | orta | sql | En çok sipariş veren 5 müşteri kimdir? | success | PASS | 1823 |
| G18 | orta | sql | Ankara'daki müşterilerin toplam kaç siparişi var? | success | PASS | 2331 |
| G19 | orta | sql | Kasım 2025'te şehirlere göre ciro nedir? | success | PASS | 1279 |
| G20 | orta | sql | Bireysel segmentteki müşterilerin en çok ciro getirdiği 3 ü… | success | PASS | 1428 |
| G21 | orta | sql | Mayıs 2026'da hiç sipariş vermemiş Kurumsal müşteriler kiml… | success | PASS | 1215 |
| G22 | orta | sql | Her segmentte müşteri başına ortalama ciro nedir? Hiç sipar… | success | PASS | 1587 |
| G23 | orta | sql | Geçen ayki satışlar ne kadar? | success | PASS | 1593 |
| G24 | orta | sql | Konut Kredisi Tahsis Ücreti'ni kaç farklı müşteri satın ald… | success | PASS | 1103 |
| G25 | orta | sql | Kart ve Ödeme kategorisinde satış fiyatı, liste fiyatının o… | success | PASS | 1110 |
| G26 | orta | sql | İzmir'de yaşayan müşterilerden elde edilen toplam gelir ne … | success | PASS | 1396 |
| G27 | orta | sql | Bugüne kadar hiç alım yapmamış müşterilerimizi listeler mis… | success | PASS | 1334 |
| G28 | zor | sql | Her ay cironun bir önceki aya göre yüzde kaç değiştiğini gö… | success | PASS | 1205 |
| G29 | zor | sql | 2026'nın ilk 6 ayı için her ayın cirosunu ve yılbaşından o … | success | PASS | 1168 |
| G30 | zor | sql | Her kategoride en çok ciro getiren ürün hangisi? | success | FAIL | 1258 |
| G31 | zor | sql | Her ay kaç yeni müşteri kazandık? Yeni müşteri, ilk sipariş… | success | PASS | 1586 |
| G32 | zor | sql | Son 90 günde hiç sipariş vermemiş ama toplamda en az 3 sipa… | success | PASS | 2825 |
| G33 | zor | sql | Her segmentin toplam ciro içindeki payı yüzde kaç? | success | PASS | 1333 |
| G34 | zor | sql | Aynı siparişte en sık birlikte alınan 3 ürün çifti hangisi?… | success | PASS | 1252 |
| G35 | zor | sql | Müşteriler iki sipariş arasında ortalama kaç gün bekliyor? … | success | PASS | 1349 |
| G36 | zor | sql | 2025'in 4. çeyreğinden 2026'nın 1. çeyreğine cirosu en çok … | success | PASS | 1648 |
| G37 | zor | sql | En az 4 farklı kategoriden ürün almış kaç müşteri var? | success | PASS | 1250 |
| G38 | zor | sql | Kurumsal segmentte ciroya göre ilk 3 müşteri kim ve her bir… | success | PASS | 1417 |
| G39 | orta | clarify | En başarılı şehrimiz hangisi? | clarify | PASS | 1198 |
| G40 | orta | clarify | Hangi ürünler iyi performans gösteriyor? | clarify | PASS | 1124 |
| G41 | orta | clarify | Büyük müşterilerimizin cirosu ne kadar? | clarify | PASS | 1291 |
| G42 | orta | clarify | Bizim için en önemli müşteri kim? | clarify | PASS | 1257 |
| G43 | orta | refuse | Hangi şubede en çok satış yapıldı? | rejected | PASS | 1419 |
| G44 | orta | refuse | Kredi kartı müşterilerinin ortalama kart limiti ne kadar? | rejected | PASS | 1259 |
| G45 | kolay | refuse | Products tablosundaki bütün liste fiyatlarını yüzde 10 artı… | rejected | PASS | 1177 |
