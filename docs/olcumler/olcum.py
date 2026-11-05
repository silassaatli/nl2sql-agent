"""
Prompt geliştirme ölçümü (Sorumlu: Kişi B)

16 test sorusu → generate_sql → validate_sql → execute_sql → (01–08) cevap anahtarıyla karşılaştırma.
Amaç: prompt'taki her değişikliğin etkisini ayrı ayrı ölçmek (teknik değerlendirme için).
Sonuçlar GERÇEK model çıktısıdır; elle yazılmış veya mock sonuç yoktur.

Bu resmi test raporu DEĞİLDİR (o: tests/run_all.py). Farkları:
- Yeniden deneme YOK (pipeline'dan daha katı ölçer)
- Karşılaştırma CLAUDE.md ekip kararları 4–6'nın basit bir uygulamasıdır

Kullanım (proje kökünden):  python docs/olcumler/olcum.py <etiket>
Çıktı: docs/olcumler/<etiket>.json  (meta + her test için soru, status, SQL, sonuç, PASS/FAIL)
"""
import json, os, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LABEL = sys.argv[1] if len(sys.argv) > 1 else "olcum"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import app.llm as llm  # noqa: E402
from app.llm import generate_sql, ModelOutputError  # noqa: E402
from app.validator import validate_sql  # noqa: E402
from app.db import execute_sql  # noqa: E402

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
    if n_a > n_e and len(used) < n_e:
        return False, "beklenen sütunların hepsi bulunamadı"
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


def customers_count():
    return execute_sql("SELECT COUNT(*) AS n FROM Customers")[0][0]["n"]


cases = json.load(open("tests/test_cases.json", encoding="utf-8"))
before = customers_count()
results = []
for t in cases:
    tid, q = t["id"], t["input"]
    r = {"id": tid, "type": t["type"], "question": q}
    t0 = time.time()
    try:
        g = generate_sql(q)
        r.update(status=g["status"], sql=g["sql"], assumption=g["assumption"], message=g["message"])
    except ModelOutputError as e:
        r.update(status="model_output_error", sql="", message=str(e))
    r["llm_s"] = round(time.time() - t0, 1)
    if r["status"] == "ok":
        ok, clean, err = validate_sql(r["sql"])
        if not ok:
            r["exec"] = f"validator reddi: {err}"
        else:
            try:
                rows, _ = execute_sql(clean)
                r["exec"] = f"{len(rows)} satır"
                r["rows_preview"] = rows[:3]
                if t["type"] == "is":
                    r["pass"], r["why"] = compare(tid, rows)
            except Exception as e:
                r["exec"] = f"DB hatası: {type(e).__name__}: {e}"
    if t["type"] == "is" and "pass" not in r:
        r["pass"], r["why"] = False, r.get("exec", r["status"])
    results.append(r)
    print(f"{tid} [{r['llm_s']:>5}s] {r['status']:<12} {r.get('exec',''):<28} "
          f"{'' if 'pass' not in r else ('PASS ' if r['pass'] else 'FAIL ') + r['why']}", flush=True)

after = customers_count()
print(f"\nCustomers satır sayısı: önce {before}, sonra {after}")
biz = [r for r in results if r["type"] == "is"]
print(f"İş soruları: {sum(r['pass'] for r in biz)}/8 PASS")
meta = {
    "label": LABEL,
    "measured_at": datetime.now().isoformat(timespec="seconds"),   # sadece kayıt zamanı
    "model": llm.MODEL_NAME,
    "temperature": llm.TEMPERATURE,
    "few_shot_count": len(llm.FEW_SHOT_EXAMPLES),
    "system_prompt_chars": len(llm.build_system_prompt()),
    "retry": False,
    "business_pass": f"{sum(r['pass'] for r in biz)}/8",
    "customers_before_after": [before, after],
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{LABEL}.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"meta": meta, "results": results}, f, ensure_ascii=False, indent=1, default=str)
    f.write("\n")
print("Ayrıntı:", os.path.relpath(out, ROOT))
