# Eval karşılaştırması

- **A:** `eval_20261120-133634.json` · bayraklar `{'SELF_CORRECTION': False, 'SELF_CORRECTION_MAX_RETRIES': 2}` · kod `f1857f6a79`
- **B:** `eval_20261120-133918_sc-on.json` · bayraklar `{'SELF_CORRECTION': True, 'SELF_CORRECTION_MAX_RETRIES': 2}` · kod `f1857f6a79`

| Grup | A | B | Fark (B − A) |
|---|---|---|---|
| Genel | %97.8 (44/45) | %97.8 (44/45) | +0.0 puan |
| Zorluk: kolay | %100.0 (12/12) | %100.0 (12/12) | +0.0 puan |
| Zorluk: orta | %100.0 (22/22) | %95.5 (21/22) | -4.5 puan |
| Zorluk: zor | %90.9 (10/11) | %100.0 (11/11) | +9.1 puan |
| Davranış: clarify | %100.0 (4/4) | %100.0 (4/4) | +0.0 puan |
| Davranış: refuse | %100.0 (3/3) | %100.0 (3/3) | +0.0 puan |
| Davranış: sql | %97.4 (37/38) | %97.4 (37/38) | +0.0 puan |
| Etiket: aggregation | %100.0 (25/25) | %100.0 (25/25) | +0.0 puan |
| Etiket: alt_sorgu | %100.0 (3/3) | %100.0 (3/3) | +0.0 puan |
| Etiket: anti_join | %100.0 (2/2) | %100.0 (2/2) | +0.0 puan |
| Etiket: belirsiz | %100.0 (4/4) | %100.0 (4/4) | +0.0 puan |
| Etiket: cevaplanamaz | %100.0 (2/2) | %100.0 (2/2) | +0.0 puan |
| Etiket: churn | %100.0 (1/1) | %100.0 (1/1) | +0.0 puan |
| Etiket: filtre | %100.0 (5/5) | %100.0 (5/5) | +0.0 puan |
| Etiket: gelir | %92.9 (13/14) | %92.9 (13/14) | +0.0 puan |
| Etiket: goreli_tarih | %100.0 (1/1) | %0.0 (0/1) | -100.0 puan |
| Etiket: join | %92.9 (13/14) | %92.9 (13/14) | +0.0 puan |
| Etiket: kosullu_aggregation | %100.0 (1/1) | %100.0 (1/1) | +0.0 puan |
| Etiket: kumulatif | %100.0 (1/1) | %100.0 (1/1) | +0.0 puan |
| Etiket: lag | %100.0 (2/2) | %100.0 (2/2) | +0.0 puan |
| Etiket: left_join | %100.0 (3/3) | %100.0 (3/3) | +0.0 puan |
| Etiket: oran | %100.0 (4/4) | %100.0 (4/4) | +0.0 puan |
| Etiket: paraphrase | %100.0 (3/3) | %100.0 (3/3) | +0.0 puan |
| Etiket: row_number | %0.0 (0/1) | %100.0 (1/1) | +100.0 puan |
| Etiket: self_join | %100.0 (1/1) | %100.0 (1/1) | +0.0 puan |
| Etiket: siralama | %100.0 (6/6) | %100.0 (6/6) | +0.0 puan |
| Etiket: tarih | %100.0 (10/10) | %100.0 (10/10) | +0.0 puan |
| Etiket: tek_tablo | %100.0 (11/11) | %100.0 (11/11) | +0.0 puan |
| Etiket: window | %83.3 (5/6) | %100.0 (6/6) | +16.7 puan |
| Etiket: zararli | %100.0 (1/1) | %100.0 (1/1) | +0.0 puan |

Ortalama gecikme: A 1710 ms · B 1369 ms. Pipeline yeniden denemeleri: A 0 · B 0. Yeniden denemeyle düzelen: A 0 · B 0.

> Not: model deterministik değil (aynı soru farklı koşularda farklı SQL üretebilir). Tek koşuluk farkın bir kısmı bayraktan değil bu değişkenlikten gelebilir; değişen sorularda B'nin denemelerine (attempts) bakın.

## Sonucu değişen sorular

- G23: PASS → FAIL · Geçen ayki satışlar ne kadar?
- G30: FAIL → PASS · Her kategoride en çok ciro getiren ürün hangisi?
