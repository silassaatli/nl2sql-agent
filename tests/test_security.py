
import pytest

from app.validator import validate_sql
from app.db import execute_sql


@pytest.mark.parametrize("sql, expected_valid", [
    ("SELECT * FROM Customers", True),
    ("DROP TABLE Customers", False),
    ("SELECT * FROM Customers; DELETE FROM Customers", False),
    ("SELECT * FROM sqlite_master", False),
    ("ATTACH DATABASE 'x.db' AS x", False),
    ("PRAGMA table_info(Customers)", False),
    ("SELECT * FROM Customers /* DELETE FROM Customers */", True),
])
def test_validator(sql, expected_valid):
    valid, clean_sql, error_type = validate_sql(sql)

    assert valid == expected_valid, (
        f"SQL: {sql}\n"
        f"Expected: {expected_valid}, Got: {valid}\n"
        f"Error: {error_type}"
    )

    if valid:
        assert clean_sql
    else:
        assert clean_sql == ""


def test_read_only_execution():
    valid, clean_sql, _ = validate_sql(
        "SELECT * FROM Customers LIMIT 5"
    )

    assert valid

    rows, truncated = execute_sql(clean_sql)

    assert len(rows) == 5
    assert truncated is False
    assert isinstance(rows[0], dict)


def test_database_unchanged():
    valid, _, _ = validate_sql("DELETE FROM Customers")

    assert valid is False

    rows, _ = execute_sql(
        "SELECT COUNT(*) AS total FROM Customers"
    )

    assert rows[0]["total"] == 200
