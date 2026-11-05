"""
Güvenli sorgu çalıştırma (Sorumlu: Kişi A)

- Salt-okunur bağlantı (mode=ro): veri değiştirilemez
- Authorizer: SQLite motoru seviyesinde sadece izinli 4 tablonun okunmasına izin verir
- Süre sınırı (TIMEOUT_S) ve satır limiti (MAX_ROWS)

Hatalar:
- Süre aşımı → sqlite3.OperationalError("interrupted")  → pipeline'da "timeout"
- Authorizer reddi → sqlite3.DatabaseError("not authorized") → "security_rejected"
- Olmayan sütun → sqlite3.OperationalError("no such column") → "unknown_field"
"""

import sqlite3
import time

from config import ALLOWED_TABLES, DB_PATH, MAX_ROWS, TIMEOUT_S


def _authorizer(action, arg1, arg2, db_name, trigger):
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and arg1 and arg1.lower() in ALLOWED_TABLES:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def execute_sql(sql: str) -> tuple[list[dict], bool]:
    """Döner: (satırlar, 500'den fazla olup kesildi_mi)"""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.set_authorizer(_authorizer)
    start = time.time()
    conn.set_progress_handler(lambda: 1 if time.time() - start > TIMEOUT_S else 0, 10000)
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(MAX_ROWS + 1)
        return [dict(zip(cols, r)) for r in rows[:MAX_ROWS]], len(rows) > MAX_ROWS
    finally:
        conn.close()
