# Mimari

Diyagramlar [Mermaid](https://mermaid.js.org) ile yazıldı; GitHub dosyayı açınca çizer. PNG gerekirse
[mermaid.live](https://mermaid.live) üzerinden dışa aktarılır.

Renkler: **mavi** Kişi B (şema, LLM, semantik katman, arayüz, log), **kırmızı** Kişi A (veritabanı kurulumu, doğrulama,
çalıştırma, akış), **gri** veri / dosya. Kutulardaki `dosya:satır` referansları `sila/dokumanlar` dalındaki koda göredir.

## 1. Kurulum anı (bir kez)

```mermaid
flowchart LR
    CSV[("data/csv/*.csv<br/>sabit veri")] --> SETUP["setup_db.py<br/>build_database() · setup_db.py:85"]
    SETUP --> DB[("data/nl2sql.db")]
    SETUP --> SCHEMA["app/schema.py<br/>extract_schema() · schema.py:70<br/>tablo, sütun, tip, PK/FK,<br/>az değerli sütun değerleri, tarih aralığı"]
    SCHEMA --> SJ[("data/schema.json")]

    classDef b fill:#dbeafe,stroke:#1d4ed8,color:#000
    classDef a fill:#fee2e2,stroke:#b91c1c,color:#000
    classDef data fill:#f3f4f6,stroke:#6b7280,color:#000
    class SCHEMA b
    class SETUP a
    class CSV,DB,SJ data
```

## 2. Soru anı (her istek)

```mermaid
flowchart TD
    UI["app/ui.py · ui.py:118<br/>Streamlit: soru formu"] --> ASK["app/pipeline.py<br/>ask() · pipeline.py:52"]
    ASK --> ISSQL{"Girdi SQL mi?<br/>SQL_START regex · pipeline.py:19, 59<br/>baştaki boşluk ve yorumlar atlanır,<br/>ilk kelime SQL komutu mu"}

    ISSQL -- "hayır: doğal dil" --> SEM["app/semantic.py<br/>date_note() · semantic.py:173<br/>metric_note() · semantic.py:184"]
    ISSQL -- "evet: girdi aynen SQL<br/>modele gitmez · pipeline.py:107" --> VAL

    SEM --> LLM["app/llm.py · generate_sql() · llm.py:210<br/>sistem prompt'u (llm.py:152)<br/>+ 5 few-shot (llm.py:51) + soru"]
    SJ[("data/schema.json")] -.-> LLM
    CFG[("config.py<br/>referans tarih 2026-06-30<br/>tarih aralıkları · config.py:17")] -.-> LLM
    LLM <--> OLL["Ollama · qwen2.5-coder:7b<br/>temperature=0, format=json,<br/>num_ctx=8192 · llm.py:218"]

    LLM -- "ModelUnavailableError<br/>pipeline.py:116" --> E_MU["error · model_unavailable"]
    LLM -- "ModelOutputError<br/>pipeline.py:122" --> E_IM["error · invalid_model_response"]
    LLM -- "status: clarify<br/>pipeline.py:140" --> CL["clarify · ambiguous"]
    LLM -- "status: unsupported<br/>pipeline.py:147" --> R_UN["rejected · unsupported"]
    LLM -- "status: ok + SQL" --> VAL

    VAL{"app/validator.py<br/>validate_sql() · validator.py:22<br/>çağrı: pipeline.py:176<br/>SQLGlot: tek ifade, sadece SELECT/WITH,<br/>yasak ifade yok, izinli 4 tablo,<br/>yorumlar atılır"}
    VAL -- "güvenlik reddi · pipeline.py:183<br/>multiple_statements, not_select,<br/>forbidden_statement, table_not_allowed" --> R_VAL["rejected · hata türü"]
    VAL -- "parse_error" --> RETRY
    VAL -- "geçti: temiz SQL<br/>pipeline.py:193" --> EXE

    EXE{"app/db.py<br/>execute_sql() · db.py:30<br/>salt-okunur bağlantı + authorizer (db.py:20),<br/>5 sn süre sınırı, en fazla 500 satır"}
    DB[("data/nl2sql.db")] -.-> EXE
    EXE -- "authorizer reddi<br/>pipeline.py:200" --> R_SEC["rejected · security_rejected"]
    EXE -- "süre aşıldı<br/>pipeline.py:207" --> E_TO["error · timeout"]
    EXE -- "diğer DB hatası<br/>pipeline.py:214" --> E_DB["error · database_error"]
    EXE -- "no such column / syntax error" --> RETRY
    EXE -- "satırlar · pipeline.py:236" --> OK["success<br/>0 satır ise empty_result"]

    RETRY{"Doğrudan SQL mi<br/>ya da retry_count ≥ 1 mi?<br/>pipeline.py:245<br/>parse_error ve unknown_field<br/>AYNI tek hakkı paylaşır"}
    RETRY -- "hayır: modelin SQL'i, hak var<br/>önceki SQL + hata modele geri verilir<br/>pipeline.py:254" --> LLM
    RETRY -- "evet" --> E_RT["error · parse_error / unknown_field"]

    subgraph SONUC ["Sonuç: her çıkış yolu"]
        OK
        CL
        R_UN
        R_VAL
        R_SEC
        E_MU
        E_IM
        E_TO
        E_DB
        E_RT
    end
    SONUC --> LOG["app/logger.py · write_log() · logger.py:18<br/>logs/queries.jsonl, istek başına bir satır<br/>çağrı: pipeline.py:82"]
    SONUC --> SHOW["app/ui.py · show_result() · ui.py:65<br/>durum, SQL, varsayım, tablo, hata açıklaması"]

    classDef b fill:#dbeafe,stroke:#1d4ed8,color:#000
    classDef a fill:#fee2e2,stroke:#b91c1c,color:#000
    classDef data fill:#f3f4f6,stroke:#6b7280,color:#000
    class UI,SEM,LLM,OLL,LOG,SHOW b
    class ASK,ISSQL,VAL,EXE,RETRY a
    class SJ,CFG,DB data
```

## Notlar

- **Doğrudan SQL tespiti güvenlik kararı değildir.** `SQL_START` (`pipeline.py:19`) baştaki boşluk, `--` ve `/* */`
  yorumlarını atlayıp ilk kelimenin bir SQL komutu (SELECT, WITH, INSERT, DELETE, DROP, ATTACH, PRAGMA vb.) olup
  olmadığına bakar; yalnızca girdinin hangi yoldan gideceğini seçer. Regex bir SQL'i kaçırırsa girdi modele gider ve
  modelin SQL'i yine validator'dan geçer; bir soruyu yanlışlıkla SQL sayarsa validator reddeder. İki yol da aynı
  validator ve authorizer'dan geçer. Doğrudan SQL girdilerinin logunda `model` alanı `null` olur (`pipeline.py:91`).
- **Yeniden deneme yalnızca modelin SQL'i için ve tek haktır.** `pipeline.py`'de tek bir `retry_count` sayacı var
  (`pipeline.py:55`, `config.MAX_RETRIES = 1` · `config.py:14`). Validator'ın `parse_error`'ı ile veritabanının
  `no such column` / `syntax error` hataları aynı yere düşer (`pipeline.py:245`). İlk denemede `parse_error`, ikincide
  `unknown_field` çıkarsa ikinci bir hak yoktur. Kullanıcının kendi yazdığı SQL hatalıysa modele düzelttirilmez, hata
  doğrudan döner. Diğer hatalar (güvenlik reddi, timeout, model erişilemezliği, bozuk model cevabı) hiç yeniden denenmez.
- **Yalnızca temiz SQL çalışır.** Validator'ın yorumlardan arındırıp yeniden ürettiği SQL (`validator.py:40`)
  `execute_sql`'e gider (`pipeline.py:193`). Kullanıcının ya da modelin orijinal metni hiç çalışmaz. Test 14'te
  `SELECT * FROM Customers /* DELETE FROM Customers */` girdisinden yürütücüye yalnızca `SELECT * FROM Customers` ulaştı.
- **İki savunma hattı.** Validator (SQLGlot) bir şeyi kaçırsa bile salt-okunur bağlantı (`db.py:32`) ve authorizer
  (`db.py:20`) yazmayı, ATTACH/PRAGMA'yı ve izinli 4 tablo dışını SQLite motoru seviyesinde reddeder.
- **Boş soru** LLM'e gitmeden `clarify · ambiguous` döner (`pipeline.py:96`, diyagramda gösterilmedi).
