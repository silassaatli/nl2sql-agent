"""
Test 01–08 cevap anahtarını üretir (Sorumlu: Kişi B)

Çalıştırma:  python tests/expected/build_expected.py   (önce: python setup_db.py)

Her referans SQL veritabanında çalıştırılır ve sonucu tests/expected/<id>.json dosyasına yazılır.
Sonuçlar elle yazılmaz; veri değişirse bu betik yeniden çalıştırılır.

Bilerek app/db.py kullanılmaz: cevap anahtarı test edilen sistemden bağımsız olmalı.
Kendi salt-okunur bağlantısını açar.
"""

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from config import DB_PATH  # noqa: E402

OUT_DIR = os.path.join(ROOT, "tests", "expected")
TEST_CASES = os.path.join(ROOT, "tests", "test_cases.json")

# --- Referans SQL'ler -------------------------------------------------------
REFERENCE_SQL = {
    "01": """SELECT p.ProductName, SUM(oi.Quantity * oi.UnitPrice) AS Ciro
FROM OrderItems oi
JOIN Products p ON p.ProductID = oi.ProductID
GROUP BY p.ProductID, p.ProductName
ORDER BY Ciro DESC
LIMIT 5;""",

    "02": """SELECT SUM(oi.Quantity * oi.UnitPrice) AS Ciro
FROM Customers c
JOIN Orders o      ON o.CustomerID = c.CustomerID
JOIN OrderItems oi ON oi.OrderID   = o.OrderID
WHERE c.City = 'İzmir';""",

    "03": """SELECT strftime('%Y-%m', o.OrderDate) AS Ay, SUM(oi.Quantity * oi.UnitPrice) AS Ciro
FROM Orders o
JOIN OrderItems oi ON oi.OrderID = o.OrderID
WHERE o.OrderDate BETWEEN '2026-01-01' AND '2026-06-30'
GROUP BY Ay
ORDER BY Ay;""",

    "04": """SELECT p.Category, AVG(oi.Quantity * oi.UnitPrice) AS OrtalamaKalemTutari
FROM OrderItems oi
JOIN Products p ON p.ProductID = oi.ProductID
GROUP BY p.Category
ORDER BY p.Category;""",

    "05": """SELECT c.CustomerID, c.Name, c.City
FROM Customers c
LEFT JOIN Orders o ON o.CustomerID = c.CustomerID
WHERE o.OrderID IS NULL
ORDER BY c.CustomerID;""",

    "06": """SELECT c.Segment, SUM(oi.Quantity * oi.UnitPrice) AS Ciro
FROM Customers c
JOIN Orders o      ON o.CustomerID = c.CustomerID
JOIN OrderItems oi ON oi.OrderID   = o.OrderID
GROUP BY c.Segment
ORDER BY Ciro DESC;""",

    "07": """SELECT c.City, SUM(oi.Quantity * oi.UnitPrice) AS Ciro
FROM Customers c
JOIN Orders o      ON o.CustomerID = c.CustomerID
JOIN OrderItems oi ON oi.OrderID   = o.OrderID
WHERE o.OrderDate BETWEEN '2026-01-01' AND '2026-03-31'
GROUP BY c.City
ORDER BY Ciro DESC
LIMIT 1;""",

    "08": """SELECT p.ProductName, SUM(oi.Quantity * oi.UnitPrice) AS Ciro
FROM Orders o
JOIN OrderItems oi ON oi.OrderID  = o.OrderID
JOIN Products p    ON p.ProductID = oi.ProductID
WHERE o.OrderDate BETWEEN '2026-06-01' AND '2026-06-30'
GROUP BY p.ProductID, p.ProductName
ORDER BY Ciro DESC
LIMIT 3;""",
}


def load_questions() -> dict:
    """test_cases.json'dan {id: soru} sözlüğü. Soru metninin tek kaynağı orası."""
    with open(TEST_CASES, encoding="utf-8") as f:
        return {t["id"]: t["input"] for t in json.load(f)}


def run_query(conn, sql: str) -> tuple[list[str], list[list]]:
    cur = conn.execute(sql)
    columns = [d[0] for d in cur.description]
    rows = [list(r) for r in cur.fetchall()]
    return columns, rows


def main():
    if not os.path.exists(DB_PATH):
        sys.exit(f"Veritabanı yok: {DB_PATH}\nÖnce çalıştırın: python setup_db.py")

    questions = load_questions()
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        for test_id, sql in REFERENCE_SQL.items():
            columns, rows = run_query(conn, sql)
            data = {
                "id": test_id,
                "question": questions[test_id],
                "reference_sql": sql,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
            }
            path = os.path.join(OUT_DIR, f"{test_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"  {test_id}: {len(rows):>2} satır → {os.path.relpath(path, ROOT)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
