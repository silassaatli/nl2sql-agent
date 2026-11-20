"""
Sessiz hata kontrolleri — GÜVENLİK KATMANI DEĞİLDİR (o iş app/validator.py + app/db.py'de, burada değişmez).

Buradaki kontroller sorgunun çalışıp YANLIŞ sonuç vermesine yol açan kalıpları yakalar. Yalnızca
config.SELF_CORRECTION açıkken, validator'dan geçmiş temiz SQL üzerinde, çalıştırmadan önce kullanılır
(app/pipeline.py); bulunan sorun modele geri verilip düzeltme istenir.

find_tautologies(): bir sütunun kendisiyle karşılaştırıldığı koşullar (ör. p.ProductID = p.ProductID).
NULL olmayan her satırda doğrudur; JOIN koşulundaysa tabloları kartezyen çarpıma çevirir
(gerçek örnek: eval G25, sonuç %92 yerine %1162 çıktı).
"""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError, TokenError

# Sütun kendisiyle karşılaştırıldığında her zaman doğru olan karşılaştırmalar.
# (<>, <, > ise her zaman yanlıştır; onlar boş sonuç verir ve boş sonuç kuralı yakalar.)
ALWAYS_TRUE = (exp.EQ, exp.GTE, exp.LTE)


def find_tautologies(sql: str) -> list[str]:
    """Sütunun kendisiyle karşılaştırıldığı koşulları SQL metni olarak döndürür; yoksa []."""
    try:
        tree = sqlglot.parse_one(sql, read="sqlite")
    except (ParseError, TokenError):
        return []           # ayrıştırılamayan SQL'i validator zaten reddeder
    found = []
    for node in tree.find_all(*ALWAYS_TRUE):
        left, right = node.this, node.expression
        # sqlglot düğümleri yapısal olarak karşılaştırılır: aynı tablo takma adı + aynı sütun adı
        if isinstance(left, exp.Column) and left == right:
            found.append(node.sql(dialect="sqlite"))
    return found
