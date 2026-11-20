# Golden set değerlendirme raporu

Üretim: 2026-11-20T14:25:25 · Model: `gemini-3.5-flash-lite` · Bayraklar: `{'SELF_CORRECTION': False, 'SELF_CORRECTION_MAX_RETRIES': 2, 'RELATIVE_DATES': False}` · Kod özeti: `4de85acd1d` · Komut: `python eval/run_eval.py --experimental both --repeat 3 --cache-only`

Sonuçlar gerçek model çıktısıdır (mock yok). Beklenen sonuçlar her koşuda gold_sql'den yeniden hesaplandı.
Kapsam: 45 soru (bütün golden set) · önbellekten gelen: 45

## Özet

| Ölçü | Değer |
|---|---|
| **Genel doğruluk** | **%97.8 (44/45)** |
| PASS / FAIL / INFRA / SKIP / EKSIK | 44 / 1 / 0 / 0 / 0 |
| Gecikme ort. / medyan / p95 | 1701 / 1264 / 4785 ms |
| Pipeline yeniden denemeleri | 0 |
| Yeniden denemeyle düzelen (PASS) | 0 |
| 429/5xx backoff tekrarları | 3 |

INFRA: kota/ağ hatası, SKIP: gold_sql henüz yazılmadı, EKSIK: koşu durdurulduğu için sorulmadı. Üçü de doğruluk paydasına girmez.

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
- **Varsayım:** Her kategori için ciroya göre en yüksek değere sahip ürünler listelenmiştir.
- **Üretilen SQL:**

```sql
SELECT p.Category, p.ProductName, SUM(oi.Quantity * oi.UnitPrice) AS Ciro FROM OrderItems AS oi JOIN Products AS p ON p.ProductID = p.ProductID GROUP BY p.Category, p.ProductID ORDER BY p.Category, Ciro DESC
```
- **Gold SQL:**

```sql
WITH urun AS (SELECT p.Category, p.ProductName, ROW_NUMBER() OVER (PARTITION BY p.Category ORDER BY SUM(oi.Quantity * oi.UnitPrice) DESC) AS Sira FROM OrderItems oi JOIN Products p ON p.ProductID = oi.ProductID GROUP BY p.ProductID) SELECT Category, ProductName FROM urun WHERE Sira = 1 ORDER BY Category
```
- **Beklenen (ilk satırlar, 6 satır):** `[['Döviz ve Hazine', 'Akreditif Komisyonu'], ['Kart ve Ödeme', 'Sanal POS Paketi'], ['Kredi Ürünleri', 'Ticari Kredi Tahsis Ücreti']]`
- **Gelen (ilk satırlar, 32 satır):** `[['Döviz ve Hazine', 'Döviz Alım-Satım Komisyonu', 133381447.82], ['Döviz ve Hazine', 'Forward Sözleşme Komisyonu', 133381447.82], ['Döviz ve Hazine', 'Swap İşlem Komisyonu', 133381447.82]]`

## Bütün sorular

| No | Zorluk | Beklenen | Soru | Durum | Sonuç | Süre (ms) |
|---|---|---|---|---|---|---|
| G01 | kolay | sql | Kaç müşterimiz var? | success | PASS | 7697 |
| G02 | kolay | sql | Her şehirde kaç müşterimiz var? | success | PASS | 2749 |
| G03 | kolay | sql | Segmentlere göre müşteri sayısı nedir? | success | PASS | 4785 |
| G04 | kolay | sql | Kurumsal segmentteki müşterileri listele. | success | PASS | 1030 |
| G05 | kolay | sql | Ürün kataloğunda kaç farklı kategori var? | success | PASS | 1124 |
| G06 | kolay | sql | Liste fiyatı en yüksek 3 ürün hangileri? | success | PASS | 1181 |
| G07 | kolay | sql | Sigorta kategorisindeki ürünleri liste fiyatlarıyla birlikt… | success | PASS | 1106 |
| G08 | kolay | sql | Toplam kaç sipariş alındı? | success | PASS | 1031 |
| G09 | kolay | sql | 2025 Aralık ayında kaç sipariş verildi? | success | PASS | 1039 |
| G10 | kolay | sql | Kategorilere göre ortalama liste fiyatı nedir? | success | PASS | 1412 |
| G11 | kolay | sql | Tek bir sipariş kaleminde satılan en yüksek adet kaçtır? | success | PASS | 1491 |
| G12 | orta | sql | Kategorilere göre toplam ciro nedir? | success | PASS | 1026 |
| G13 | orta | sql | 2026'nın ilk çeyreğinde Kurumsal segmentin cirosu ne kadar? | success | PASS | 1254 |
| G14 | orta | sql | Her ürünün toplam satış adedini göster. | success | PASS | 1111 |
| G15 | orta | sql | Her müşterinin sipariş sayısını göster; hiç siparişi olmaya… | success | PASS | 1111 |
| G16 | orta | sql | Sipariş başına ortalama tutar nedir? | success | PASS | 1191 |
| G17 | orta | sql | En çok sipariş veren 5 müşteri kimdir? | success | PASS | 1294 |
| G18 | orta | sql | Ankara'daki müşterilerin toplam kaç siparişi var? | success | PASS | 1628 |
| G19 | orta | sql | Kasım 2025'te şehirlere göre ciro nedir? | success | PASS | 1733 |
| G20 | orta | sql | Bireysel segmentteki müşterilerin en çok ciro getirdiği 3 ü… | success | PASS | 1264 |
| G21 | orta | sql | Mayıs 2026'da hiç sipariş vermemiş Kurumsal müşteriler kiml… | success | PASS | 1387 |
| G22 | orta | sql | Her segmentte müşteri başına ortalama ciro nedir? Hiç sipar… | success | PASS | 1832 |
| G23 | orta | sql | Geçen ayki satışlar ne kadar? | success | PASS | 1170 |
| G24 | orta | sql | Konut Kredisi Tahsis Ücreti'ni kaç farklı müşteri satın ald… | success | PASS | 2314 |
| G25 | orta | sql | Kart ve Ödeme kategorisinde satış fiyatı, liste fiyatının o… | success | PASS | 1119 |
| G26 | orta | sql | İzmir'de yaşayan müşterilerden elde edilen toplam gelir ne … | success | PASS | 5710 |
| G27 | orta | sql | Bugüne kadar hiç alım yapmamış müşterilerimizi listeler mis… | success | PASS | 1255 |
| G28 | zor | sql | Her ay cironun bir önceki aya göre yüzde kaç değiştiğini gö… | success | PASS | 2128 |
| G29 | zor | sql | 2026'nın ilk 6 ayı için her ayın cirosunu ve yılbaşından o … | success | PASS | 1248 |
| G30 | zor | sql | Her kategoride en çok ciro getiren ürün hangisi? | success | FAIL | 1254 |
| G31 | zor | sql | Her ay kaç yeni müşteri kazandık? Yeni müşteri, ilk sipariş… | success | PASS | 1272 |
| G32 | zor | sql | Son 90 günde hiç sipariş vermemiş ama toplamda en az 3 sipa… | success | PASS | 1638 |
| G33 | zor | sql | Her segmentin toplam ciro içindeki payı yüzde kaç? | success | PASS | 1296 |
| G34 | zor | sql | Aynı siparişte en sık birlikte alınan 3 ürün çifti hangisi?… | success | PASS | 1252 |
| G35 | zor | sql | Müşteriler iki sipariş arasında ortalama kaç gün bekliyor? … | success | PASS | 1358 |
| G36 | zor | sql | 2025'in 4. çeyreğinden 2026'nın 1. çeyreğine cirosu en çok … | success | PASS | 1724 |
| G37 | zor | sql | En az 4 farklı kategoriden ürün almış kaç müşteri var? | success | PASS | 1833 |
| G38 | zor | sql | Kurumsal segmentte ciroya göre ilk 3 müşteri kim ve her bir… | success | PASS | 1704 |
| G39 | orta | clarify | En başarılı şehrimiz hangisi? | clarify | PASS | 904 |
| G40 | orta | clarify | Hangi ürünler iyi performans gösteriyor? | clarify | PASS | 975 |
| G41 | orta | clarify | Büyük müşterilerimizin cirosu ne kadar? | clarify | PASS | 1256 |
| G42 | orta | clarify | Bizim için en önemli müşteri kim? | clarify | PASS | 1469 |
| G43 | orta | refuse | Hangi şubede en çok satış yapıldı? | rejected | PASS | 1104 |
| G44 | orta | refuse | Kredi kartı müşterilerinin ortalama kart limiti ne kadar? | rejected | PASS | 1944 |
| G45 | kolay | refuse | Products tablosundaki bütün liste fiyatlarını yüzde 10 artı… | rejected | PASS | 1120 |
