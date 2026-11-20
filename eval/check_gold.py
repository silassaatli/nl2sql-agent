"""
Golden set'teki her gold_sql'in sağlamlık kontrolü. Model çağrısı YAPMAZ, veritabanına salt-okunur bağlanır.

Çalıştırma:  python eval/check_gold.py

Her soru için:
1. Alanlar tutarlı mı? (sql sorusunda gold_sql var mı; clarify/refuse sorusunda gold_sql boş mu)
2. gold_sql projenin validate_sql katmanından geçiyor mu? (gold da aynı güvenlik kurallarına uymalı)
3. Hatasız çalışıp boş olmayan sonuç döndürüyor mu?
4. "İlk N" sorularında N. ve N+1. satırın sıralama değeri eşit mi? (eşitse cevap tek değildir, soru düzeltilmeli)

Zor sorularda gold_sql henüz yazılmadıysa "BEKLİYOR" yazar, hata saymaz.
Çıkış kodu: herhangi bir HATA varsa 1.
"""

import sys

import sqlglot
from sqlglot import exp

from gold import load_golden, run_gold

from app.validator import validate_sql  # gold.py proje kökünü sys.path'e ekledi


def boundary_tie(sql: str) -> str:
    """ORDER BY + LIMIT N varsa, N. ve N+1. satırın sıralama anahtarı eşit mi bakar. Eşitse açıklama, değilse "" döner."""
    tree = sqlglot.parse_one(sql, read="sqlite")
    limit, order = tree.args.get("limit"), tree.args.get("order")
    if not limit or not order:
        return ""
    n = int(limit.expression.name)

    # ORDER BY'da SELECT takma adı kullanıldıysa (ORDER BY Ciro) takma adın ifadesine çevir.
    aliases = {e.alias: e.this for e in tree.expressions if isinstance(e, exp.Alias)}
    keys = []
    for ordered in order.expressions:
        key = ordered.this
        if isinstance(key, exp.Column) and not key.table and key.name in aliases:
            key = aliases[key.name]
        keys.append(key.copy())

    # Orijinal SELECT listesi yerinde kalır (ORDER BY takma adları ve GROUP BY 1, 2 gibi sıra numaraları
    # bozulmasın); sıralama anahtarları listenin SONUNA eklenir ve yalnızca onlar karşılaştırılır.
    probe = tree.copy()
    probe.set("limit", None)
    probe.set("expressions", probe.expressions + keys)
    _, rows = run_gold(probe.sql(dialect="sqlite"))
    k = len(keys)
    if len(rows) > n and rows[n - 1][-k:] == rows[n][-k:]:
        return f"{n}. ve {n + 1}. satırın sıralama değeri eşit: {rows[n - 1][-k:]}"
    return ""


def main() -> None:
    items = load_golden()
    errors = pending = 0

    for item in items:
        gid, sql, behavior = item["id"], item["gold_sql"].strip(), item["expected_behavior"]

        if behavior != "sql":
            if sql:
                print(f"{gid} | HATA | {behavior} sorusunda gold_sql dolu olmamalı")
                errors += 1
            else:
                print(f"{gid} | OK   | {behavior}")
            continue

        if not sql:
            print(f"{gid} | BEKLİYOR | gold_sql yazılmadı ({item.get('author', '?')})")
            pending += 1
            continue

        valid, _, reason = validate_sql(sql)
        if not valid:
            print(f"{gid} | HATA | validate_sql reddetti: {reason}")
            errors += 1
            continue
        try:
            columns, rows = run_gold(sql)
        except Exception as exc:  # noqa: BLE001  (her türlü SQLite hatası raporlanır)
            print(f"{gid} | HATA | {type(exc).__name__}: {exc}")
            errors += 1
            continue
        if not rows:
            print(f"{gid} | HATA | boş sonuç (golden set'te anlamlı, boş olmayan sonuç beklenir)")
            errors += 1
            continue
        tie = boundary_tie(sql)
        if tie:
            print(f"{gid} | HATA | {tie}")
            errors += 1
            continue

        preview = " / ".join(" · ".join(str(v) for v in r) for r in rows[:2])
        print(f"{gid} | OK   | {len(rows)} satır, sütunlar {columns} | {preview}{' …' if len(rows) > 2 else ''}")

    print(f"\nToplam {len(items)} soru · hata {errors} · bekleyen gold_sql {pending}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
