"""
NL2SQL Agent — veritabanı kurulumu.

data/csv/ klasöründeki SABİT veri dosyalarını okuyup SQLite veritabanını sıfırdan oluşturur.
Rastgelelik yoktur: her çalıştırmada birebir aynı veritabanı oluşur.

Kullanım:
    python setup_db.py              # data/nl2sql.db oluşturur (varsa silip yeniden kurar)
    python setup_db.py --db yol.db  # farklı bir dosya yolu
"""

import argparse
import csv
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_DIR = os.path.join(BASE_DIR, "data", "csv")
DEFAULT_DB = os.path.join(BASE_DIR, "data", "nl2sql.db")

SCHEMA_SQL = """
CREATE TABLE Customers (
    CustomerID  INTEGER PRIMARY KEY,
    Name        TEXT    NOT NULL,
    City        TEXT    NOT NULL,
    Segment     TEXT    NOT NULL CHECK (Segment IN ('Bireysel', 'KOBİ', 'Kurumsal'))
);

CREATE TABLE Products (
    ProductID   INTEGER PRIMARY KEY,
    ProductName TEXT    NOT NULL,
    Category    TEXT    NOT NULL,
    Price       REAL    NOT NULL CHECK (Price > 0)
);

CREATE TABLE Orders (
    OrderID     INTEGER PRIMARY KEY,
    CustomerID  INTEGER NOT NULL REFERENCES Customers(CustomerID),
    OrderDate   TEXT    NOT NULL   -- 'YYYY-MM-DD' (saat bilgisi yok)
);

CREATE TABLE OrderItems (
    OrderItemID INTEGER PRIMARY KEY,
    OrderID     INTEGER NOT NULL REFERENCES Orders(OrderID),
    ProductID   INTEGER NOT NULL REFERENCES Products(ProductID),
    Quantity    INTEGER NOT NULL CHECK (Quantity > 0),
    UnitPrice   REAL    NOT NULL CHECK (UnitPrice > 0)
);

CREATE INDEX idx_orders_customer ON Orders(CustomerID);
CREATE INDEX idx_orders_date     ON Orders(OrderDate);
CREATE INDEX idx_items_order     ON OrderItems(OrderID);
CREATE INDEX idx_items_product   ON OrderItems(ProductID);
"""

# Tablo adı -> sütun dönüştürücüleri (CSV metnini doğru tipe çevirir)
TABLES = {
    "Customers":  [int, str, str, str],
    "Products":   [int, str, str, float],
    "Orders":     [int, int, str],
    "OrderItems": [int, int, int, int, float],
}

QUALITY_CHECKS = {
    "FK ihlali yok": "SELECT COUNT(*) FROM pragma_foreign_key_check",
    "Tarih aralığı dışında sipariş yok":
        "SELECT COUNT(*) FROM Orders WHERE OrderDate < '2025-07-01' OR OrderDate > '2026-06-30'",
    "Kalemsiz sipariş yok":
        "SELECT COUNT(*) FROM Orders o WHERE NOT EXISTS "
        "(SELECT 1 FROM OrderItems i WHERE i.OrderID = o.OrderID)",
}


def load_csv(table, converters):
    path = os.path.join(CSV_DIR, f"{table}.csv")
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # başlık satırı
        return [tuple(conv(v) for conv, v in zip(converters, row)) for row in reader]


def build_database(db_path):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        for table, converters in TABLES.items():
            rows = load_csv(table, converters)
            placeholders = ", ".join("?" * len(converters))
            conn.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
            print(f"  {table:<11}: {len(rows)} satır")
        conn.commit()

        for name, sql in QUALITY_CHECKS.items():
            bad = conn.execute(sql).fetchone()[0]
            if bad:
                raise RuntimeError(f"Veri kalitesi kontrolü başarısız: {name} ({bad} satır)")
    finally:
        conn.close()
    print(f"Veritabanı hazır: {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NL2SQL veritabanı kurulumu (sabit CSV'lerden)")
    parser.add_argument("--db", default=DEFAULT_DB, help="veritabanı dosya yolu")
    build_database(parser.parse_args().db)
