"""
Golden set yardımcıları (check_gold.py ve run_eval.py ortak kullanır).

- load_golden(): eval/golden_set.json'u okur, alanları ve id tekrarlarını kontrol eder.
- run_gold(sql): gold_sql'i KENDİ salt-okunur bağlantısıyla çalıştırır (mode=ro URI).
  Bilerek app/db.py kullanılmaz: beklenen sonucu hesaplayan kod, test edilen kodla aynı olmamalı
  (tests/expected/build_expected.py ile aynı ilke). Veritabanı hiçbir koşulda değiştirilemez.
"""

import json
import sqlite3
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
PROJECT_DIR = EVAL_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from config import DB_PATH  # noqa: E402

GOLDEN_PATH = EVAL_DIR / "golden_set.json"
BEHAVIORS = {"sql", "clarify", "refuse"}
DIFFICULTIES = {"kolay", "orta", "zor"}
REQUIRED_FIELDS = {"id", "question", "difficulty", "tags", "gold_sql", "order_matters", "expected_behavior"}


def load_golden(path: Path = GOLDEN_PATH) -> list[dict]:
    """Golden set'i okur; yapısal hata varsa ValueError (sessizce eksik veriyle koşmasın)."""
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    seen = set()
    for item in items:
        missing = REQUIRED_FIELDS - item.keys()
        if missing:
            raise ValueError(f"{item.get('id', '?')}: eksik alan {sorted(missing)}")
        if item["id"] in seen:
            raise ValueError(f"Tekrarlanan id: {item['id']}")
        seen.add(item["id"])
        if item["expected_behavior"] not in BEHAVIORS:
            raise ValueError(f"{item['id']}: bilinmeyen expected_behavior {item['expected_behavior']!r}")
        if item["difficulty"] not in DIFFICULTIES:
            raise ValueError(f"{item['id']}: bilinmeyen difficulty {item['difficulty']!r}")
    return items


def connect_ro() -> sqlite3.Connection:
    """Salt-okunur bağlantı: dosya URI'si + mode=ro. Yazma denemesi 'attempt to write a readonly database' verir."""
    return sqlite3.connect(Path(DB_PATH).resolve().as_uri() + "?mode=ro", uri=True)


def run_gold(sql: str) -> tuple[list[str], list[list]]:
    """gold_sql'i çalıştırır. Döner: (sütun adları, satırlar [liste listesi])."""
    conn = connect_ro()
    try:
        cur = conn.execute(sql)
        columns = [d[0] for d in cur.description]
        return columns, [list(r) for r in cur.fetchall()]
    finally:
        conn.close()
