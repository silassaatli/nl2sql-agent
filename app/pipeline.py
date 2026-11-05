"""
Uçtan uca akış + hata yönetimi + log (Sorumlu: Kişi A, B ile birlikte bağlanır)

Akış:
    soru → generate_sql → (status != ok ise kullanıcıya mesaj, SQL çalışmaz)
         → validate_sql → execute_sql → sonuç
    Doğrulama veya çalıştırma hatasında: hata modele geri verilir, EN FAZLA 1 kez (config.MAX_RETRIES) yeniden denenir.

Hata türleri (error_type):
    parse_error, multiple_statements, not_select, forbidden_statement, table_not_allowed,
    security_rejected, unknown_field, timeout, empty_result, model_unavailable,
    ambiguous (clarify), unsupported

Her istekte logs/queries.jsonl'a bir satır JSON yazılır:
    timestamp, question, sql, status, error_type, retry_count, row_count, duration_ms, model
"""

from config import LOG_PATH, MAX_RETRIES, MODEL_NAME  # noqa: F401


def ask(question: str) -> dict:
    """
    Döner: {"status": "success" | "clarify" | "rejected" | "error",
            "sql": str, "rows": list[dict], "truncated": bool,
            "message": str, "error_type": str | None, "duration_ms": int}
    """
    raise NotImplementedError


def write_log(record: dict) -> None:
    raise NotImplementedError
