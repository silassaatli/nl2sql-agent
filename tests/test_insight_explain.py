"""app/insight.py (kural tabanlı yorum) ve app/explain.py (SQL'in Türkçe açıklaması). Model ve ağ yok."""

import pytest
from streamlit.testing.v1 import AppTest

from app.explain import explain_sql
from app.insight import fmt, generate_insights


# --- insight -----------------------------------------------------------------
def test_number_format():
    assert fmt(1234567.891) == "1.234.567,89"
    assert fmt(1234.0) == "1.234"


def test_time_series():
    rows = [{"Ay": "2026-01", "Ciro": 100.0}, {"Ay": "2026-02", "Ciro": 150.0}, {"Ay": "2026-03", "Ciro": 120.0}]
    out = generate_insights(rows)
    assert out[0] == "Ciro, 2026-01 döneminden 2026-03 dönemine %20,0 arttı (100 → 120)."
    assert out[1] == "En yüksek değer 2026-02 (150), en düşük değer 2026-01 (100)."
    assert out[2] == "Dönemden döneme en büyük değişim 2026-02 döneminde: %50,0 artış."


def test_categorical_share_and_ratio():
    rows = [{"Segment": "A", "Ciro": 60.0}, {"Segment": "B", "Ciro": 30.0}, {"Segment": "C", "Ciro": 10.0}]
    assert generate_insights(rows) == [
        "Ciro en yüksek A (60), en düşük C (10).",
        "A grubunun toplam içindeki payı %60,0 (3 grup).",
        "En yüksek değer, en düşük değerin yaklaşık 6,0 katı.",
    ]


def test_ratio_metric_only_high_low():
    rows = [{"Segment": "A", "PayYuzde": 60.0}, {"Segment": "B", "PayYuzde": 40.0}]
    assert generate_insights(rows) == ["PayYuzde en yüksek A (60), en düşük B (40)."]


def test_id_column_ignored_and_no_share_for_many_groups():
    rows = [{"CustomerID": i, "Name": f"M{i}", "Siparis": i} for i in range(1, 30)]
    out = generate_insights(rows)
    assert out[0] == "Siparis en yüksek M29 (29), en düşük M1 (1)."
    assert not any("payı" in line for line in out)


@pytest.mark.parametrize("rows", [[], [{"Ciro": 5.0}], [{"Name": "A"}, {"Name": "B"}]])
def test_no_insight_without_label_and_metric(rows):
    assert generate_insights(rows) == []


# --- explain -----------------------------------------------------------------
def test_explain_join_filter_aggregate():
    sql = ("SELECT c.City, SUM(oi.Quantity * oi.UnitPrice) AS Ciro FROM Customers c "
           "JOIN Orders o ON o.CustomerID = c.CustomerID JOIN OrderItems oi ON oi.OrderID = o.OrderID "
           "WHERE o.OrderDate BETWEEN '2025-11-01' AND '2025-11-30' GROUP BY c.City ORDER BY Ciro DESC LIMIT 3")
    assert explain_sql(sql) == [
        "Kullanılan tablolar: Customers, Orders, OrderItems.",
        "Orders bağlanıyor: o.CustomerID = c.CustomerID.",
        "OrderItems bağlanıyor: oi.OrderID = o.OrderID.",
        "Filtre: o.OrderDate '2025-11-01' ile '2025-11-30' arasında.",
        "Ciro = SUM(oi.Quantity * oi.UnitPrice) (toplam).",
        "Gruplama: c.City (her grup bir satır).",
        "Sıralama: Ciro azalan.",
        "Yalnızca ilk 3 satır döndürülüyor.",
    ]


def test_explain_left_join_window_cte_not_in():
    left = explain_sql("SELECT c.Name, COUNT(o.OrderID) AS n FROM Customers c LEFT JOIN Orders o "
                       "ON o.CustomerID = c.CustomerID GROUP BY c.CustomerID")
    assert any("LEFT JOIN" in line for line in left)
    window = explain_sql("WITH aylik AS (SELECT 1 AS Ay, 2 AS Ciro FROM Orders) "
                         "SELECT Ay, LAG(Ciro) OVER (ORDER BY Ay) AS Onceki FROM aylik")
    assert window[0] == "Önce ara sonuç(lar) hesaplanıyor (CTE): aylik."
    assert any("pencere fonksiyonu (LAG)" in line for line in window)
    assert "Kullanılan tablolar: Orders." in window          # CTE adı tablo sayılmaz
    anti = explain_sql("SELECT Name FROM Customers WHERE CustomerID NOT IN (SELECT CustomerID FROM Orders)")
    assert "Filtre: CustomerID alt sorgunun/listenin İÇİNDE DEĞİL." in anti


def test_explain_unparseable():
    assert explain_sql("SELECT * FROM") == []


# --- arayüz: bayrak açık / kapalı ---------------------------------------------
SCRIPT = """
import sys, os
sys.path.insert(0, os.getcwd())
from unittest.mock import patch
import config, app.platform_ui
config.INSIGHTS = config.SQL_EXPLAIN = {flag}
with patch.object(app.platform_ui, "render_platform", lambda f: None):
    from app.ui import show_result
show_result({{"status": "success", "sql": "SELECT Segment, SUM(Quantity) AS Adet FROM OrderItems GROUP BY Segment",
             "rows": [{{"Segment": "A", "Adet": 3}}, {{"Segment": "B", "Adet": 1}}], "message": "m",
             "assumption": "", "error_type": None, "retry_count": 0, "duration_ms": 5}})
"""


@pytest.mark.parametrize("flag", [True, False])
def test_ui_shows_only_when_flag_on(flag):
    at = AppTest.from_string(SCRIPT.format(flag=flag), default_timeout=60).run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert ("Otomatik yorum" in text) is flag
    assert ("Bu SQL ne yapıyor?" in text) is flag
