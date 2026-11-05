"""
Ölçüm karşılaştırması: model sonucu ↔ tests/expected/<id>.json

CLAUDE.md ekip kararları 4–6'nın basit uygulaması:
- Float değerler 2 ondalığa yuvarlanır (madde 4)
- 04, 05, 06 sırasız karşılaştırılır (madde 5)
- Esnek sütun eşleştirmesi (madde 6): sadece model DAHA AZ sütun döndürdüyse ve döndürdüğü her sütun
  eşleştiyse. En az beklenen kadar sütun döndüyse beklenen sütunların hepsi eşleşmeli.
"""
import json


UNORDERED = {"04", "05", "06"}


def norm(v):
    return round(v, 2) if isinstance(v, float) else v


def compare(test_id, rows):
    exp = json.load(open(f"tests/expected/{test_id}.json", encoding="utf-8"))
    e_rows = [[norm(v) for v in r] for r in exp["rows"]]
    a_rows = [[norm(v) for v in r.values()] for r in rows]
    if len(a_rows) != len(e_rows):
        return False, f"satır sayısı {len(a_rows)} ≠ {len(e_rows)}"
    if not a_rows:
        return True, "ikisi de boş"
    n_e, n_a = len(e_rows[0]), len(a_rows[0])
    # gerçek sütunları beklenen sütunlarla değerlerine göre eşleştir (madde 6)
    e_cols = [[r[i] for r in e_rows] for i in range(n_e)]
    a_cols = [[r[i] for r in a_rows] for i in range(n_a)]
    if test_id in UNORDERED:
        e_cols = [sorted(map(str, c)) for c in e_cols]
        a_cols = [sorted(map(str, c)) for c in a_cols]
    used, mapping = set(), []
    for ac in a_cols:
        j = next((j for j, ec in enumerate(e_cols) if j not in used and ec == ac), None)
        if j is not None:
            used.add(j); mapping.append(j)
    if not used:
        return False, "hiçbir sütun eşleşmedi"
    # Esnek eşleştirme (madde 6) SADECE model daha az sütun döndürdüyse ve döndürdüğü her sütun eşleştiyse.
    # Model en az beklenen kadar sütun döndürdüyse beklenen sütunların HEPSİ eşleşmeli
    # (ör. doğru şehir + yanlış ciro → FAIL).
    if n_a >= n_e and len(used) < n_e:
        return False, f"beklenen {n_e} sütunun {len(used)}'i eşleşti (diğer değerler farklı)"
    if n_a < n_e and len(used) < n_a:
        return False, "döndürülen sütunlardan bazıları eşleşmedi"
    # eşleşen sütunlarla satırları birlikte karşılaştır (sırasızlarda satır kümesi)
    e_sub = [tuple(str(r[j]) for j in sorted(used)) for r in e_rows]
    a_idx = [a_cols.index(next(ac for ac in a_cols if ac == e_cols[j])) for j in sorted(used)]
    a_sub = [tuple(str(r[i]) for i in a_idx) for r in a_rows]
    if test_id in UNORDERED:
        e_sub, a_sub = sorted(e_sub), sorted(a_sub)
    if e_sub != a_sub:
        return False, "satırlar eşleşmedi"
    note = "" if len(used) == n_e else f" (sadece {len(used)}/{n_e} sütun döndü)"
    return True, "eşleşti" + note


