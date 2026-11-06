"""
Prompt geliştirme ölçümü (Sorumlu: Kişi B)

16 test sorusu → generate_sql → validate_sql → execute_sql → (01–08) cevap anahtarıyla karşılaştırma.
Amaç: prompt'taki her değişikliğin etkisini ayrı ayrı ölçmek (teknik değerlendirme için).
Sonuçlar GERÇEK model çıktısıdır; elle yazılmış veya mock sonuç yoktur.

Bu resmi test raporu DEĞİLDİR (o: tests/run_all.py). Farkları:
- Yeniden deneme YOK (pipeline'dan daha katı ölçer)
- Karşılaştırma ekip kararlarının (yuvarlama, sıra, sütun eşleştirme) basit bir uygulamasıdır (karsilastir.py)

Kullanım (proje kökünden):
    python docs/olcumler/olcum.py <etiket>                  # tests/test_cases.json soruları
    python docs/olcumler/olcum.py <etiket> <soru_dosyası>   # ör. docs/olcumler/farkli_ifadeler.json
Soru dosyası test_cases.json biçimindedir (id, input, type). 01–08 yine tests/expected/ ile karşılaştırılır.
Çıktı: docs/olcumler/<etiket>.json  (meta + her test için soru, status, SQL, sonuç, PASS/FAIL)
"""
import json, os, sys, time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LABEL = sys.argv[1] if len(sys.argv) > 1 else "olcum"
QUESTIONS_FILE = sys.argv[2] if len(sys.argv) > 2 else "tests/test_cases.json"
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import app.llm as llm  # noqa: E402
from app.llm import generate_sql, ModelOutputError  # noqa: E402
from app.validator import validate_sql  # noqa: E402
from app.db import execute_sql  # noqa: E402
from karsilastir import compare  # noqa: E402  (aynı klasördeki modül)


def customers_count():
    return execute_sql("SELECT COUNT(*) AS n FROM Customers")[0][0]["n"]


cases = json.load(open(QUESTIONS_FILE, encoding="utf-8"))
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
    "questions_file": QUESTIONS_FILE.replace("\\", "/"),
    "measured_at": datetime.now().isoformat(timespec="seconds"),   # sadece kayıt zamanı
    "model": llm.MODEL_NAME,
    "temperature": llm.TEMPERATURE,
    "num_ctx": getattr(llm, "LLM_NUM_CTX", 4096),   # 4096 = Ollama varsayılanı (ölçüm 17'den önce)
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
