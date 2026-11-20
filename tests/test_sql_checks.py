"""app/sql_checks.py: sütunun kendisiyle karşılaştırıldığı (her zaman doğru) koşullar. Ağ yok."""

import json
from pathlib import Path

import pytest

from app.sql_checks import find_tautologies

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("sql", [
    # Gerçek model çıktısı (eval G25): JOIN koşulu tabloyu kendisine bağlıyor
    "SELECT AVG((oi.UnitPrice * 100.0) / p.Price) FROM OrderItems AS oi JOIN Products AS p "
    "ON p.ProductID = p.ProductID WHERE p.Category = 'Kart ve Ödeme'",
    "SELECT * FROM Orders o JOIN Customers c ON o.CustomerID = o.CustomerID",
    "SELECT * FROM Products WHERE ProductID = ProductID",
    "SELECT * FROM Products p WHERE p.Price >= p.Price",
    "SELECT * FROM Orders o WHERE o.OrderID IN (SELECT oi.OrderID FROM OrderItems oi WHERE oi.ProductID = oi.ProductID)",
])
def test_detects(sql):
    assert find_tautologies(sql)


@pytest.mark.parametrize("sql", [
    "SELECT * FROM OrderItems oi JOIN Products p ON p.ProductID = oi.ProductID",
    "SELECT * FROM Orders o WHERE EXISTS (SELECT 1 FROM Orders o2 WHERE o2.CustomerID = o.CustomerID)",
    "SELECT * FROM Products WHERE 1 = 1",
    "SELECT * FROM Products p WHERE p.Price > p.Price",     # her zaman yanlış: boş sonuç kuralı yakalar
    "SELECT * FROM",                                        # ayrıştırılamaz: validator'ın işi
])
def test_no_false_alarm(sql):
    assert find_tautologies(sql) == []


def test_no_false_alarm_on_any_reference_sql():
    """Golden set ve ödev cevap anahtarındaki bütün doğru SQL'lerde alarm çıkmamalı."""
    golden = [g["gold_sql"] for g in json.loads((ROOT / "eval" / "golden_set.json").read_text(encoding="utf-8"))
              if g["gold_sql"]]
    expected = [json.loads(p.read_text(encoding="utf-8"))["reference_sql"]
                for p in sorted((ROOT / "tests" / "expected").glob("0*.json"))]
    assert len(golden) == 38 and len(expected) == 8
    assert {sql: find_tautologies(sql) for sql in golden + expected if find_tautologies(sql)} == {}
