# Tekrarlı eval özeti

Her ayar aynı golden set üzerinde birden fazla kez koşturuldu (her tekrar ayrı önbellek, gerçek model).
Ortalama, model değişkenliğinin tek koşuluk sonucu yanıltmasını azaltır.

Her koşunun doğruluğu yalnızca o koşuda puanlanan sorular üzerinden hesaplanır (INFRA ve EKSIK paydaya girmez); ortalama, koşu doğruluklarının ortalamasıdır.

| Ayar | Koşu | Puanlanan soru (koşu başına) | Tam koşuların ortalaması | Bütün koşuların ortalaması | En düşük | En yüksek | Ort. gecikme | Yeniden denemeyle düzelen (toplam) | INFRA (toplam) | EKSIK (toplam) |
|---|---|---|---|---|---|---|---|---|---|---|
| SELF_CORRECTION=False, RELATIVE_DATES=False | 3 | 45 / 43 / 45 | **%97.8** (2 koşu) | %97.0 | %95.3 | %97.8 | 2545 ms | 0 | 0 | 2 |
| SELF_CORRECTION=True, RELATIVE_DATES=True | 3 | 45 / 45 / 17 | **%98.9** (2 koşu) | %99.3 | %97.8 | %100.0 | 1429 ms | 2 | 0 | 28 |

## Zorluğa göre ortalama

| Zorluk | SELF_CORRECTION=False, RELATIVE_DATES=False | SELF_CORRECTION=True, RELATIVE_DATES=True |
|---|---|---|
| kolay | %100.0 | %100.0 |
| orta | %98.5 | %100.0 |
| zor | %90.2 | %95.5 |

## Eksik kalan sorular (koşu durduruldu, sorulmadı)

- **SELF_CORRECTION=False, RELATIVE_DATES=False:** 2 soru (G34–G35): G34, G35
- **SELF_CORRECTION=True, RELATIVE_DATES=True:** 28 soru (G18–G45): G18, G19, G20, G21, G22, G23, G24, G25, G26, G27, G28, G29, G30, G31, G32, G33, G34, G35, G36, G37, G38, G39, G40, G41, G42, G43, G44, G45

## En az bir koşuda FAIL / INFRA olan sorular

Hücre: geçen koşu / sorulan koşu (EKSIK koşular sayılmaz).

| No | Soru | SELF_CORRECTION=False, RELATIVE_DATES=False | SELF_CORRECTION=True, RELATIVE_DATES=True |
|---|---|---|---|
| G23 | Geçen ayki satışlar ne kadar? | 2/3 (FAIL) | 2/2 |
| G30 | Her kategoride en çok ciro getiren ürün hangisi? | 0/3 (FAIL, FAIL, FAIL) | 1/2 (FAIL) |
