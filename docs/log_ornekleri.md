# JSON log örnekleri

Her istek `app/pipeline.py` tarafından `app/logger.py` → `write_log()` ile `logs/queries.jsonl` dosyasına **tek satır JSON**
olarak eklenir (JSON Lines). `logs/*.jsonl` repoya konmadığı için örnekler buraya kopyalandı. Satırlar dosyadan değiştirilmeden
alındı; okunabilirlik için yalnızca girintilendi.

| Alan | Anlamı |
|---|---|
| `timestamp` | Log zamanı (UTC). Yalnızca kayıt içindir; sorgu sonuçlarında sistem saati kullanılmaz |
| `question` | Kullanıcının girdisi |
| `sql` | Çalıştırılan (validator'dan geçmiş, temizlenmiş) SQL. Validator'ın reddettiği doğrudan SQL'de kullanıcının ham girdisi; SQL yoksa `""` |
| `status` | `success`, `clarify`, `rejected` veya `error` |
| `error_type` | Hata/durum türü; başarılı sonuçta `null` (0 satırda `empty_result`) |
| `retry_count` | Yeniden deneme sayısı (en fazla 1, yalnızca modelin SQL'i için) |
| `row_count` | Dönen satır sayısı (en fazla 500) |
| `duration_ms` | Uçtan uca süre (model + doğrulama + çalıştırma) |
| `model` | Kullanılan model; girdi doğrudan SQL ise model çağrılmadığı için `null` |

Örnek 1–4, resmi test raporunu üreten çalıştırmadan alındı (`python tests/run_all.py`, 2026-11-06 13:15–13:16 yerel saat =
10:15–10:16 UTC; `logs/queries.jsonl` satır 125, 132, 135, 137). Örnek 5 bu dosya için 2026-11-06'da ayrıca üretildi.

## 1. success: İzmir'in toplam cirosu (test 02)

```json
{"timestamp": "2026-11-06T10:15:32.795181+00:00",
 "question": "İzmir'in toplam cirosu nedir?",
 "sql": "SELECT SUM(oi.Quantity * oi.UnitPrice) AS Ciro FROM Customers AS c JOIN Orders AS o ON o.CustomerID = c.CustomerID JOIN OrderItems AS oi ON oi.OrderID = o.OrderID WHERE c.City = 'İzmir'",
 "status": "success", "error_type": null, "retry_count": 0, "row_count": 1, "duration_ms": 5260,
 "model": "qwen2.5-coder:7b"}
```

Model SQL üretti, validator geçirdi, salt-okunur bağlantıda çalıştı ve 1 satır döndü (19,235,337.37, cevap anahtarıyla aynı).
`sql` alanı modelin ham metni değil, SQLGlot'un yeniden ürettiği temiz SQL'dir: aynı soruda modelin ham çıktısı
`FROM Customers c` biçimindedir (`docs/olcumler/18_ornek5_test_sorulari.json`), çalışan ve loglanan sürüm `FROM Customers AS c`.

## 2. clarify: "En iyi müşteri kimdir?" (test 09)

```json
{"timestamp": "2026-11-06T10:16:14.455889+00:00",
 "question": "En iyi müşteri kimdir?",
 "sql": "", "status": "clarify", "error_type": "ambiguous", "retry_count": 0, "row_count": 0, "duration_ms": 3307,
 "model": "qwen2.5-coder:7b"}
```

"En iyi" hangi metriğe göre ölçüleceği belli olmayan bir değerlendirme. Model `clarify` döndürdü ve sessiz bir varsayım
yapmak yerine ölçütü sordu. SQL üretilmediği için veritabanına hiç gidilmedi (`sql: ""`, `row_count: 0`).

## 3. rejected: çoklu ifade girdisi (test 12)

```json
{"timestamp": "2026-11-06T10:16:23.378646+00:00",
 "question": "SELECT * FROM Customers; DELETE FROM Customers",
 "sql": "SELECT * FROM Customers; DELETE FROM Customers",
 "status": "rejected", "error_type": "multiple_statements", "retry_count": 0, "row_count": 0, "duration_ms": 1,
 "model": null}
```

Girdi bir SQL komutuyla başladığı için modele gitmedi (`model: null`, 1 ms) ve doğrudan validator'a verildi. SQLGlot iki ifade
buldu, validator `multiple_statements` ile reddetti, yürütücü hiç çağrılmadı. Customers satır sayısı testten önce ve sonra 200.
`sql` alanındaki metin reddedilen ham girdidir; çalıştırılmadı.

## 4. success: yorum içine gizlenmiş komut (test 14)

```json
{"timestamp": "2026-11-06T10:16:26.412293+00:00",
 "question": "SELECT * FROM Customers /* DELETE FROM Customers */",
 "sql": "SELECT * FROM Customers",
 "status": "success", "error_type": null, "retry_count": 0, "row_count": 200, "duration_ms": 2,
 "model": null}
```

`question` ile `sql` arasındaki fark ödevin 4. güvenlik kuralını gösterir: validator yorumu ifade olarak değil yorum olarak
ayrıştırdı ve SQL'i yorumsuz yeniden üretti. Yürütücüye yalnızca `SELECT * FROM Customers` gitti; `DELETE` hiç çalışmadı,
Customers 200 satır kaldı.

## 5. error: model erişilemiyor (`model_unavailable`)

```json
{"timestamp": "2026-11-06T09:17:57.580420+00:00",
 "question": "İzmir'in toplam cirosu nedir?",
 "sql": "", "status": "error", "error_type": "model_unavailable", "retry_count": 0, "row_count": 0, "duration_ms": 2158,
 "model": "qwen2.5-coder:7b"}
```

Nasıl üretildi: gerçek pipeline, Ollama istemcisi ulaşılamayan bir adrese yönlendirilerek çalıştırıldı (Ollama'nın kapalı
olmasıyla aynı durum: bağlantı kurulamaz). Bu satır Kişi A'nın pipeline değişikliğinden önce üretildi; değişiklik doğal dil
yolundaki bu dalı değiştirmedi.

```bash
OLLAMA_HOST=127.0.0.1:1 python -c "from app.pipeline import ask; print(ask(\"İzmir'in toplam cirosu nedir?\"))"
```

`generate_sql` bağlantı hatasını `ModelUnavailableError`'a çevirdi, pipeline bunu `error / model_unavailable` olarak döndürdü
ve kullanıcıya "SQL üreten modele erişilemedi." mesajını verdi. Sistem çökmedi. Pipeline bu hatayı yeniden denemez
(`pipeline.py:116`, `retry_count: 0`); yeniden deneme yalnızca modelin düzeltebileceği SQL hataları içindir.
