"""
SQL doğrulama katmanı (Sorumlu: Kişi A)

Model ne üretirse üretsin, her SQL çalıştırılmadan önce buradan geçer.
Kurallar (ödev Bölüm 05):
  1. Tek ifade, sadece SELECT (WITH / UNION dahil)
  2. Sadece izinli 4 tablo; sqlite_master vb. sistem tabloları kapalı (CTE'lerin içi de kontrol edilir)
  3. INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/ATTACH/PRAGMA reddedilir
  4. Yorumlar (-- ve /* */) ayrıştırılıp atılır; çalıştırılan SQL yorumsuz, yeniden üretilmiş halidir
Not: Bu katman tek başına yeterli sayılmaz; db.py'deki salt-okunur bağlantı + authorizer ikinci savunma hattıdır.
"""

import sqlglot
from sqlglot import exp

from config import ALLOWED_TABLES

FORBIDDEN = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
             exp.Alter, exp.Command, exp.Pragma, exp.Attach, exp.Detach)


def validate_sql(sql: str) -> tuple[bool, str, str]:
    """Döner: (geçti_mi, temizlenmiş_sql, hata_türü)"""
    try:
        statements = [s for s in sqlglot.parse(sql, read="sqlite") if s is not None]
    except sqlglot.errors.ParseError:
        return False, "", "parse_error"
    if len(statements) != 1:
        return False, "", "multiple_statements"
    tree = statements[0]
    if not isinstance(tree, exp.Query):
        return False, "", "not_select"
    if tree.find(*FORBIDDEN):
        return False, "", "forbidden_statement"
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if name not in ALLOWED_TABLES and name not in cte_names:
            return False, "", f"table_not_allowed:{name}"
    clean_sql = tree.sql(dialect="sqlite", comments=False)
    return True, clean_sql, ""
