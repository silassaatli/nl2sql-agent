"""
SQL'in sade Türkçe açıklaması (config.SQL_EXPLAIN; app/ui.py gösterir). Model çağrısı yok.

Çalıştırılan SQL sqlglot ile ayrıştırılır ve ağacından (AST) şu bilgiler çıkarılır: kullanılan tablolar,
birleştirmeler (JOIN), filtreler (WHERE / HAVING), hesaplar (SUM, AVG, COUNT …), pencere fonksiyonları
(LAG, ROW_NUMBER …), ara sonuçlar (CTE), gruplama, sıralama ve satır sınırı. Açıklama SQL'den türetildiği
için her zaman çalıştırılan sorguyla tutarlıdır (modelin kendi anlatımına güvenilmez).
"""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError, TokenError

AGG_TR = {exp.Sum: "toplam", exp.Avg: "ortalama", exp.Count: "sayım", exp.Min: "en küçük", exp.Max: "en büyük"}
JOIN_TR = {"LEFT": "LEFT JOIN: soldaki tablonun eşleşmeyen satırları da korunur",
           "RIGHT": "RIGHT JOIN", "FULL": "FULL JOIN", "CROSS": "CROSS JOIN: her satır her satırla eşleşir"}


def _sql(node) -> str:
    return node.sql(dialect="sqlite")


def _condition_tr(node) -> str:
    """WHERE/HAVING koşulunu okunur hâle getirir: AND → 've', OR → 'veya', BETWEEN → 'arasında'."""
    if isinstance(node, exp.And):
        return f"{_condition_tr(node.this)} ve {_condition_tr(node.expression)}"
    if isinstance(node, exp.Or):
        return f"({_condition_tr(node.this)} veya {_condition_tr(node.expression)})"
    if isinstance(node, exp.Between):
        return f"{_sql(node.this)} {_sql(node.args['low'])} ile {_sql(node.args['high'])} arasında"
    if isinstance(node, exp.Not) and isinstance(node.this, exp.In):
        return f"{_sql(node.this.this)} alt sorgunun/listenin İÇİNDE DEĞİL"
    if isinstance(node, exp.In):
        return f"{_sql(node.this)} alt sorgunun/listenin içinde"
    return _sql(node)


def explain_sql(sql: str) -> list[str]:
    """SQL'i madde madde Türkçe açıklar. Ayrıştırılamazsa []."""
    try:
        tree = sqlglot.parse_one(sql, read="sqlite")
    except (ParseError, TokenError):
        return []
    if tree is None:
        return []

    lines = []
    ctes = [c.alias_or_name for c in tree.find_all(exp.CTE)]
    if ctes:
        lines.append(f"Önce ara sonuç(lar) hesaplanıyor (CTE): {', '.join(ctes)}.")

    cte_names = {c.lower() for c in ctes}
    tables = []
    for t in tree.find_all(exp.Table):
        if t.name.lower() not in cte_names and t.name not in tables:
            tables.append(t.name)
    if tables:
        lines.append(f"Kullanılan tablolar: {', '.join(tables)}.")

    for join in tree.find_all(exp.Join):
        target = join.this
        name = target.name if isinstance(target, exp.Table) else "alt sorgu"
        side = (join.args.get("side") or join.args.get("kind") or "").upper()
        on = join.args.get("on")
        text = f"{name} bağlanıyor" + (f": {_sql(on)}" if on else " (koşulsuz)")
        if side in JOIN_TR:
            text += f" ({JOIN_TR[side]})"
        lines.append(text + ".")

    select = tree if isinstance(tree, exp.Select) else tree.find(exp.Select)
    if select is None:
        return lines

    where = select.args.get("where")
    if where:
        lines.append(f"Filtre: {_condition_tr(where.this)}.")

    for projection in select.expressions:
        inner = projection.this if isinstance(projection, exp.Alias) else projection
        name = projection.alias_or_name
        windows = list(inner.find_all(exp.Window))
        if windows:
            funcs = ", ".join(sorted({type(w.this).__name__.upper() for w in windows}))
            lines.append(f"{name}: pencere fonksiyonu ({funcs}) ile satırlar arası hesap — {_sql(inner)}.")
            continue
        aggs = [AGG_TR[type(a)] for a in inner.find_all(*AGG_TR)]
        if aggs:
            lines.append(f"{name} = {_sql(inner)} ({', '.join(dict.fromkeys(aggs))}).")

    group = select.args.get("group")
    if group:
        lines.append(f"Gruplama: {', '.join(_sql(g) for g in group.expressions)} (her grup bir satır).")
    having = select.args.get("having")
    if having:
        lines.append(f"Grup filtresi (HAVING): {_condition_tr(having.this)}.")
    order = select.args.get("order")
    if order:
        parts = [f"{_sql(o.this)} {'azalan' if o.args.get('desc') else 'artan'}" for o in order.expressions]
        lines.append(f"Sıralama: {', '.join(parts)}.")
    limit = select.args.get("limit")
    if limit:
        lines.append(f"Yalnızca ilk {_sql(limit.expression)} satır döndürülüyor.")
    return lines
