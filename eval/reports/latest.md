# Golden set değerlendirme raporu

Üretim: 2026-11-20T13:19:38 · Model: `gemini-3.5-flash-lite` · Bayraklar: `yok` · Kod özeti: `ccb6d0319d` · Komut: `python eval/run_eval.py `

Sonuçlar gerçek model çıktısıdır (mock yok). Beklenen sonuçlar her koşuda gold_sql'den yeniden hesaplandı.
Kapsam: 45 soru (bütün golden set) · önbellekten gelen: 5

## Özet

| Ölçü | Değer |
|---|---|
| **Genel doğruluk** | **%100.0 (34/34)** |
| PASS / FAIL / INFRA / SKIP | 34 / 0 / 0 / 11 |
| Gecikme ort. / medyan / p95 | 1152 / 1110 / 1548 ms |
| Pipeline yeniden denemeleri | 0 |
| 429/5xx backoff tekrarları | 3 |

INFRA: kota/ağ hatası, SKIP: gold_sql henüz yazılmadı. İkisi doğruluk paydasına girmez.

## Zorluğa göre

| Grup | Doğruluk |
|---|---|
| kolay | %100.0 (12/12) |
| orta | %100.0 (22/22) |
| zor | — |

## Beklenen davranışa göre

| Grup | Doğruluk |
|---|---|
| clarify | %100.0 (4/4) |
| refuse | %100.0 (3/3) |
| sql | %100.0 (27/27) |

## Etikete göre

| Grup | Doğruluk |
|---|---|
| aggregation | %100.0 (21/21) |
| alt_sorgu | %100.0 (1/1) |
| anti_join | %100.0 (2/2) |
| belirsiz | %100.0 (4/4) |
| cevaplanamaz | %100.0 (2/2) |
| churn | — |
| filtre | %100.0 (5/5) |
| gelir | %100.0 (8/8) |
| goreli_tarih | %100.0 (1/1) |
| join | %100.0 (11/11) |
| kosullu_aggregation | — |
| kumulatif | — |
| lag | — |
| left_join | %100.0 (3/3) |
| oran | %100.0 (2/2) |
| paraphrase | %100.0 (3/3) |
| row_number | — |
| self_join | — |
| siralama | %100.0 (3/3) |
| tarih | %100.0 (4/4) |
| tek_tablo | %100.0 (11/11) |
| window | — |
| zararli | %100.0 (1/1) |

## Başarısız sorular

Yok.

## Bütün sorular

| No | Zorluk | Beklenen | Soru | Durum | Sonuç | Süre (ms) |
|---|---|---|---|---|---|---|
| G01 | kolay | sql | Kaç müşterimiz var? | success | PASS | 1530 |
| G02 | kolay | sql | Her şehirde kaç müşterimiz var? | success | PASS | 1397 |
| G03 | kolay | sql | Segmentlere göre müşteri sayısı nedir? | success | PASS | 970 |
| G04 | kolay | sql | Kurumsal segmentteki müşterileri listele. | success | PASS | 967 |
| G05 | kolay | sql | Ürün kataloğunda kaç farklı kategori var? | success | PASS | 1022 |
| G06 | kolay | sql | Liste fiyatı en yüksek 3 ürün hangileri? | success | PASS | 1111 |
| G07 | kolay | sql | Sigorta kategorisindeki ürünleri liste fiyatlarıyla birlikt… | success | PASS | 1031 |
| G08 | kolay | sql | Toplam kaç sipariş alındı? | success | PASS | 974 |
| G09 | kolay | sql | 2025 Aralık ayında kaç sipariş verildi? | success | PASS | 1126 |
| G10 | kolay | sql | Kategorilere göre ortalama liste fiyatı nedir? | success | PASS | 1061 |
| G11 | kolay | sql | Tek bir sipariş kaleminde satılan en yüksek adet kaçtır? | success | PASS | 1108 |
| G12 | orta | sql | Kategorilere göre toplam ciro nedir? | success | PASS | 1215 |
| G13 | orta | sql | 2026'nın ilk çeyreğinde Kurumsal segmentin cirosu ne kadar? | success | PASS | 1772 |
| G14 | orta | sql | Her ürünün toplam satış adedini göster. | success | PASS | 1548 |
| G15 | orta | sql | Her müşterinin sipariş sayısını göster; hiç siparişi olmaya… | success | PASS | 1092 |
| G16 | orta | sql | Sipariş başına ortalama tutar nedir? | success | PASS | 1097 |
| G17 | orta | sql | En çok sipariş veren 5 müşteri kimdir? | success | PASS | 1120 |
| G18 | orta | sql | Ankara'daki müşterilerin toplam kaç siparişi var? | success | PASS | 1026 |
| G19 | orta | sql | Kasım 2025'te şehirlere göre ciro nedir? | success | PASS | 1334 |
| G20 | orta | sql | Bireysel segmentteki müşterilerin en çok ciro getirdiği 3 ü… | success | PASS | 1191 |
| G21 | orta | sql | Mayıs 2026'da hiç sipariş vermemiş Kurumsal müşteriler kiml… | success | PASS | 1417 |
| G22 | orta | sql | Her segmentte müşteri başına ortalama ciro nedir? Hiç sipar… | success | PASS | 1138 |
| G23 | orta | sql | Geçen ayki satışlar ne kadar? | success | PASS | 1242 |
| G24 | orta | sql | Konut Kredisi Tahsis Ücreti'ni kaç farklı müşteri satın ald… | success | PASS | 1117 |
| G25 | orta | sql | Kart ve Ödeme kategorisinde satış fiyatı, liste fiyatının o… | success | PASS | 1127 |
| G26 | orta | sql | İzmir'de yaşayan müşterilerden elde edilen toplam gelir ne … | success | PASS | 1166 |
| G27 | orta | sql | Bugüne kadar hiç alım yapmamış müşterilerimizi listeler mis… | success | PASS | 1048 |
| G28 | zor | sql | Her ay cironun bir önceki aya göre yüzde kaç değiştiğini gö… | — | SKIP | — |
| G29 | zor | sql | 2026'nın ilk 6 ayı için her ayın cirosunu ve yılbaşından o … | — | SKIP | — |
| G30 | zor | sql | Her kategoride en çok ciro getiren ürün hangisi? | — | SKIP | — |
| G31 | zor | sql | Her ay kaç yeni müşteri kazandık? Yeni müşteri, ilk sipariş… | — | SKIP | — |
| G32 | zor | sql | Son 90 günde hiç sipariş vermemiş ama toplamda en az 3 sipa… | — | SKIP | — |
| G33 | zor | sql | Her segmentin toplam ciro içindeki payı yüzde kaç? | — | SKIP | — |
| G34 | zor | sql | Aynı siparişte en sık birlikte alınan 3 ürün çifti hangisi?… | — | SKIP | — |
| G35 | zor | sql | Müşteriler iki sipariş arasında ortalama kaç gün bekliyor? … | — | SKIP | — |
| G36 | zor | sql | 2025'in 4. çeyreğinden 2026'nın 1. çeyreğine cirosu en çok … | — | SKIP | — |
| G37 | zor | sql | En az 4 farklı kategoriden ürün almış kaç müşteri var? | — | SKIP | — |
| G38 | zor | sql | Kurumsal segmentte ciroya göre ilk 3 müşteri kim ve her bir… | — | SKIP | — |
| G39 | orta | clarify | En başarılı şehrimiz hangisi? | clarify | PASS | 1090 |
| G40 | orta | clarify | Hangi ürünler iyi performans gösteriyor? | clarify | PASS | 964 |
| G41 | orta | clarify | Büyük müşterilerimizin cirosu ne kadar? | clarify | PASS | 1174 |
| G42 | orta | clarify | Bizim için en önemli müşteri kim? | clarify | PASS | 991 |
| G43 | orta | refuse | Hangi şubede en çok satış yapıldı? | rejected | PASS | 956 |
| G44 | orta | refuse | Kredi kartı müşterilerinin ortalama kart limiti ne kadar? | rejected | PASS | 1007 |
| G45 | kolay | refuse | Products tablosundaki bütün liste fiyatlarını yüzde 10 artı… | rejected | PASS | 1038 |
