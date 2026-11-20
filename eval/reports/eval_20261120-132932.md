# Golden set değerlendirme raporu

Üretim: 2026-11-20T13:29:32 · Model: `gemini-3.5-flash-lite` · Bayraklar: `yok` · Kod özeti: `1a6f86abe0` · Komut: `python eval/run_eval.py `

Sonuçlar gerçek model çıktısıdır (mock yok). Beklenen sonuçlar her koşuda gold_sql'den yeniden hesaplandı.
Kapsam: 45 soru (bütün golden set) · önbellekten gelen: 0

## Özet

| Ölçü | Değer |
|---|---|
| **Genel doğruluk** | **%97.8 (44/45)** |
| PASS / FAIL / INFRA / SKIP | 44 / 1 / 0 / 0 |
| Gecikme ort. / medyan / p95 | 1663 / 1318 / 2994 ms |
| Pipeline yeniden denemeleri | 0 |
| 429/5xx backoff tekrarları | 9 |

INFRA: kota/ağ hatası, SKIP: gold_sql henüz yazılmadı. İkisi doğruluk paydasına girmez.

## Zorluğa göre

| Grup | Doğruluk |
|---|---|
| kolay | %100.0 (12/12) |
| orta | %95.5 (21/22) |
| zor | %100.0 (11/11) |

## Beklenen davranışa göre

| Grup | Doğruluk |
|---|---|
| clarify | %100.0 (4/4) |
| refuse | %100.0 (3/3) |
| sql | %97.4 (37/38) |

## Etikete göre

| Grup | Doğruluk |
|---|---|
| aggregation | %96.0 (24/25) |
| alt_sorgu | %100.0 (3/3) |
| anti_join | %100.0 (2/2) |
| belirsiz | %100.0 (4/4) |
| cevaplanamaz | %100.0 (2/2) |
| churn | %100.0 (1/1) |
| filtre | %100.0 (5/5) |
| gelir | %100.0 (14/14) |
| goreli_tarih | %100.0 (1/1) |
| join | %92.9 (13/14) |
| kosullu_aggregation | %100.0 (1/1) |
| kumulatif | %100.0 (1/1) |
| lag | %100.0 (2/2) |
| left_join | %100.0 (3/3) |
| oran | %75.0 (3/4) |
| paraphrase | %100.0 (3/3) |
| row_number | %100.0 (1/1) |
| self_join | %100.0 (1/1) |
| siralama | %100.0 (6/6) |
| tarih | %100.0 (10/10) |
| tek_tablo | %100.0 (11/11) |
| window | %100.0 (6/6) |
| zararli | %100.0 (1/1) |

## Başarısız sorular

### G25 · orta · FAIL

- **Soru:** Kart ve Ödeme kategorisinde satış fiyatı, liste fiyatının ortalama yüzde kaçı?
- **Durum:** success / None
- **Neden:** Gold sütunları değerleriyle eşleşmedi.
- **Varsayım:** Satış fiyatının (UnitPrice) liste fiyatına (Price) oranı Kart ve Ödeme kategorisi için hesaplandı.
- **Üretilen SQL:**

```sql
SELECT AVG((oi.UnitPrice * 100.0) / p.Price) AS OrtalamaYuzde FROM OrderItems AS oi JOIN Products AS p ON p.ProductID = p.ProductID WHERE p.Category = 'Kart ve Ödeme'
```
- **Gold SQL:**

```sql
SELECT AVG(oi.UnitPrice * 100.0 / p.Price) AS OrtalamaYuzde FROM OrderItems oi JOIN Products p ON p.ProductID = oi.ProductID WHERE p.Category = 'Kart ve Ödeme'
```
- **Beklenen (ilk satırlar, 1 satır):** `[[92.06137768275687]]`
- **Gelen (ilk satırlar, 1 satır):** `[[1162.5458400724779]]`

## Bütün sorular

| No | Zorluk | Beklenen | Soru | Durum | Sonuç | Süre (ms) |
|---|---|---|---|---|---|---|
| G01 | kolay | sql | Kaç müşterimiz var? | success | PASS | 1719 |
| G02 | kolay | sql | Her şehirde kaç müşterimiz var? | success | PASS | 1122 |
| G03 | kolay | sql | Segmentlere göre müşteri sayısı nedir? | success | PASS | 1513 |
| G04 | kolay | sql | Kurumsal segmentteki müşterileri listele. | success | PASS | 1294 |
| G05 | kolay | sql | Ürün kataloğunda kaç farklı kategori var? | success | PASS | 4873 |
| G06 | kolay | sql | Liste fiyatı en yüksek 3 ürün hangileri? | success | PASS | 1027 |
| G07 | kolay | sql | Sigorta kategorisindeki ürünleri liste fiyatlarıyla birlikt… | success | PASS | 903 |
| G08 | kolay | sql | Toplam kaç sipariş alındı? | success | PASS | 978 |
| G09 | kolay | sql | 2025 Aralık ayında kaç sipariş verildi? | success | PASS | 1072 |
| G10 | kolay | sql | Kategorilere göre ortalama liste fiyatı nedir? | success | PASS | 1042 |
| G11 | kolay | sql | Tek bir sipariş kaleminde satılan en yüksek adet kaçtır? | success | PASS | 993 |
| G12 | orta | sql | Kategorilere göre toplam ciro nedir? | success | PASS | 1893 |
| G13 | orta | sql | 2026'nın ilk çeyreğinde Kurumsal segmentin cirosu ne kadar? | success | PASS | 1318 |
| G14 | orta | sql | Her ürünün toplam satış adedini göster. | success | PASS | 1208 |
| G15 | orta | sql | Her müşterinin sipariş sayısını göster; hiç siparişi olmaya… | success | PASS | 1109 |
| G16 | orta | sql | Sipariş başına ortalama tutar nedir? | success | PASS | 1213 |
| G17 | orta | sql | En çok sipariş veren 5 müşteri kimdir? | success | PASS | 1054 |
| G18 | orta | sql | Ankara'daki müşterilerin toplam kaç siparişi var? | success | PASS | 1679 |
| G19 | orta | sql | Kasım 2025'te şehirlere göre ciro nedir? | success | PASS | 2994 |
| G20 | orta | sql | Bireysel segmentteki müşterilerin en çok ciro getirdiği 3 ü… | success | PASS | 1484 |
| G21 | orta | sql | Mayıs 2026'da hiç sipariş vermemiş Kurumsal müşteriler kiml… | success | PASS | 1574 |
| G22 | orta | sql | Her segmentte müşteri başına ortalama ciro nedir? Hiç sipar… | success | PASS | 1535 |
| G23 | orta | sql | Geçen ayki satışlar ne kadar? | success | PASS | 1629 |
| G24 | orta | sql | Konut Kredisi Tahsis Ücreti'ni kaç farklı müşteri satın ald… | success | PASS | 1417 |
| G25 | orta | sql | Kart ve Ödeme kategorisinde satış fiyatı, liste fiyatının o… | success | FAIL | 1299 |
| G26 | orta | sql | İzmir'de yaşayan müşterilerden elde edilen toplam gelir ne … | success | PASS | 1125 |
| G27 | orta | sql | Bugüne kadar hiç alım yapmamış müşterilerimizi listeler mis… | success | PASS | 1449 |
| G28 | zor | sql | Her ay cironun bir önceki aya göre yüzde kaç değiştiğini gö… | success | PASS | 8470 |
| G29 | zor | sql | 2026'nın ilk 6 ayı için her ayın cirosunu ve yılbaşından o … | success | PASS | 1543 |
| G30 | zor | sql | Her kategoride en çok ciro getiren ürün hangisi? | success | PASS | 1345 |
| G31 | zor | sql | Her ay kaç yeni müşteri kazandık? Yeni müşteri, ilk sipariş… | success | PASS | 2074 |
| G32 | zor | sql | Son 90 günde hiç sipariş vermemiş ama toplamda en az 3 sipa… | success | PASS | 1584 |
| G33 | zor | sql | Her segmentin toplam ciro içindeki payı yüzde kaç? | success | PASS | 1601 |
| G34 | zor | sql | Aynı siparişte en sık birlikte alınan 3 ürün çifti hangisi?… | success | PASS | 1579 |
| G35 | zor | sql | Müşteriler iki sipariş arasında ortalama kaç gün bekliyor? … | success | PASS | 1279 |
| G36 | zor | sql | 2025'in 4. çeyreğinden 2026'nın 1. çeyreğine cirosu en çok … | success | PASS | 2879 |
| G37 | zor | sql | En az 4 farklı kategoriden ürün almış kaç müşteri var? | success | PASS | 1269 |
| G38 | zor | sql | Kurumsal segmentte ciroya göre ilk 3 müşteri kim ve her bir… | success | PASS | 1980 |
| G39 | orta | clarify | En başarılı şehrimiz hangisi? | clarify | PASS | 1052 |
| G40 | orta | clarify | Hangi ürünler iyi performans gösteriyor? | clarify | PASS | 1201 |
| G41 | orta | clarify | Büyük müşterilerimizin cirosu ne kadar? | clarify | PASS | 1187 |
| G42 | orta | clarify | Bizim için en önemli müşteri kim? | clarify | PASS | 1068 |
| G43 | orta | refuse | Hangi şubede en çok satış yapıldı? | rejected | PASS | 1950 |
| G44 | orta | refuse | Kredi kartı müşterilerinin ortalama kart limiti ne kadar? | rejected | PASS | 1062 |
| G45 | kolay | refuse | Products tablosundaki bütün liste fiyatlarını yüzde 10 artı… | rejected | PASS | 1183 |
