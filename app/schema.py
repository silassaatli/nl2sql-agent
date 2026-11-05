"""
Şema bağlamı (Sorumlu: Kişi B)

Veritabanından tablo, sütun, tip, PK ve FK bilgisini OTOMATİK okur. Ayrıca:
- Az farklı değeri olan TEXT sütunlarının değerlerini (ör. Segment: Bireysel, KOBİ, Kurumsal)
- Tarih sütunlarının biçimini ve aralığını (ör. OrderDate: 2025-07-01 – 2026-06-30)
çıkarır. Sonuç data/schema.json'a yazılır ve prompt için okunabilir metne çevrilir.

Veride yazmayan iş kuralları (metrikler, "son 6 ay" gibi tarih kuralları, Türkçe karakter
uyarısı) burada DEĞİL, app/llm.py'deki prompt'ta durur.

PRAGMA burada kullanılır çünkü bu kod kurulum/başlangıç aşamasında, bizim yazdığımız sabit
sorgularla çalışır; kullanıcı veya model metni buraya girmez. Kullanıcı sorgularının
çalıştığı app/db.py bağlantısında PRAGMA yasaktır.

Otomatik üretim: python setup_db.py veritabanını kurduktan sonra bu modülü çağırır.
Elle yeniden üretmek için (proje kökünden):  python -m app.schema
"""

import json
import os
import sqlite3

from config import BASE_DIR, DB_PATH

SCHEMA_JSON_PATH = os.path.join(BASE_DIR, "data", "schema.json")
TABLES = ["Customers", "Products", "Orders", "OrderItems"]

MAX_DISTINCT_VALUES = 50          # bundan az farklı değeri olan TEXT sütunlarının değerleri listelenir
DATE_GLOB = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]"   # YYYY-MM-DD


def _columns(conn, table: str) -> list[dict]:
    """PRAGMA table_info → [{"name", "type", "pk"}, ...]"""
    columns = []
    for _cid, name, col_type, _notnull, _default, pk in conn.execute(f'PRAGMA table_info("{table}")'):
        columns.append({"name": name, "type": col_type, "pk": bool(pk)})
    return columns


def _foreign_keys(conn, table: str) -> list[dict]:
    """PRAGMA foreign_key_list → [{"column", "ref_table", "ref_column"}, ...]"""
    fks = []
    for _id, _seq, ref_table, from_col, to_col, *_ in conn.execute(f'PRAGMA foreign_key_list("{table}")'):
        fks.append({"column": from_col, "ref_table": ref_table, "ref_column": to_col})
    return fks


def _describe_text_column(conn, table: str, column: str) -> dict:
    """
    TEXT sütunu için ek bilgi:
    - Tüm değerler YYYY-MM-DD ise → {"date_format", "min", "max"}   (önce bu kontrol edilir)
    - 50'den az farklı değer varsa → {"values": [...]}
    - İkisi de değilse (ör. Name) → {}
    """
    non_date, lo, hi = conn.execute(
        f'SELECT SUM("{column}" NOT GLOB ?), MIN("{column}"), MAX("{column}") FROM "{table}"',
        (DATE_GLOB,),
    ).fetchone()
    if lo is not None and non_date == 0:
        return {"date_format": "YYYY-MM-DD", "min": lo, "max": hi}

    distinct = conn.execute(f'SELECT COUNT(DISTINCT "{column}") FROM "{table}"').fetchone()[0]
    if distinct < MAX_DISTINCT_VALUES:
        values = [r[0] for r in conn.execute(f'SELECT DISTINCT "{column}" FROM "{table}" ORDER BY 1')]
        return {"values": values}
    return {}


def extract_schema(db_path: str = DB_PATH) -> dict:
    """{"Customers": {"columns": [...], "primary_key": [...], "foreign_keys": [...]}, ...}"""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)   # okumak yeterli → salt-okunur
    try:
        schema = {}
        for table in TABLES:
            columns = _columns(conn, table)
            for col in columns:
                if col["type"].upper() == "TEXT":
                    col.update(_describe_text_column(conn, table, col["name"]))
            schema[table] = {
                "columns": columns,
                "primary_key": [c["name"] for c in columns if c["pk"]],
                "foreign_keys": _foreign_keys(conn, table),
            }
        return schema
    finally:
        conn.close()


def save_schema(schema: dict) -> None:
    with open(SCHEMA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_schema() -> dict:
    """data/schema.json'u okur; yoksa veritabanından üretip kaydeder."""
    if not os.path.exists(SCHEMA_JSON_PATH):
        save_schema(extract_schema())
    with open(SCHEMA_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def _column_line(col: dict, fk_map: dict) -> str:
    """Tek sütun satırı, ör.:  - CustomerID INTEGER (FK → Customers.CustomerID)"""
    tags = []
    if col["pk"]:
        tags.append("PK")
    if col["name"] in fk_map:
        tags.append(f"FK → {fk_map[col['name']]}")
    line = f"  - {col['name']} {col['type']}"
    if tags:
        line += f" ({', '.join(tags)})"
    if "values" in col:
        line += " | değerler: " + ", ".join(f"'{v}'" for v in col["values"])
    if "date_format" in col:
        line += f" | biçim: {col['date_format']}, aralık: '{col['min']}' – '{col['max']}'"
    return line


def schema_to_prompt_text(schema: dict) -> str:
    """Şemayı modelin kolay okuyacağı metne çevirir."""
    blocks = []
    for table, info in schema.items():
        fk_map = {fk["column"]: f"{fk['ref_table']}.{fk['ref_column']}" for fk in info["foreign_keys"]}
        lines = [f"{table}"] + [_column_line(c, fk_map) for c in info["columns"]]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


if __name__ == "__main__":
    schema = extract_schema()
    save_schema(schema)
    print(schema_to_prompt_text(schema))
    print(f"\nKaydedildi: {os.path.relpath(SCHEMA_JSON_PATH, BASE_DIR)}")
