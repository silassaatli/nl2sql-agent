"""
JSON log (Sorumlu: Kişi B) — app/pipeline.py her istekte bir kez çağırır:  write_log(record)

Her kayıt logs/queries.jsonl dosyasına TEK SATIR JSON olarak eklenir (JSON Lines). Dosya baştan okunmaz,
sadece sonuna yazılır. Pipeline'ın gönderdiği alanlar (ödev: soru, üretilen SQL, yürütme durumu, hata türü, süre):
    timestamp, question, sql, status, error_type, retry_count, row_count, duration_ms, model

timestamp yalnızca log zamanıdır; sorgu sonuçlarında sistem saati kullanılmaz (ödev kuralı).
"""

import json
import os
import sys

from config import LOG_PATH


def write_log(record: dict, path: str = LOG_PATH) -> None:
    """Kaydı JSONL dosyasına ekler. Log yazılamazsa uyarı verir ama pipeline'ı durdurmaz."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, default=str)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as e:     # disk dolu, izin yok vb. → kullanıcının cevabı log yüzünden kaybolmasın
        print(f"[logger] Log yazılamadı ({path}): {e}", file=sys.stderr)
