"""
Kayıtlı ölçümleri, modeli yeniden ÇAĞIRMADAN yeniden puanlar.

Her dosyadaki SQL (gerçek model çıktısı) aynen alınır, validate_sql + execute_sql ile yeniden çalıştırılır
ve olcum.py'deki güncel compare() ile karşılaştırılır. Model çıktısı değişmez; yalnızca puanlama düzelir.
Neden: olcum.py'deki karşılaştırmada esnek sütun eşleştirmesi hatalıydı (doğru şehir + yanlış ciro PASS sayılıyordu).

Kullanım (proje kökünden):  python docs/olcumler/yeniden_puanla.py
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from app.db import execute_sql  # noqa: E402
from app.validator import validate_sql  # noqa: E402
from karsilastir import compare  # noqa: E402  (olcum.py ile aynı karşılaştırma)

for path in sorted(glob.glob(os.path.join(HERE, "[0-9][0-9]_*.json"))):
    data = json.load(open(path, encoding="utf-8"))
    changed = []
    for r in data["results"]:
        if r["type"] != "is" or r.get("status") != "ok" or "pass" not in r:
            continue
        ok, clean, _ = validate_sql(r["sql"])
        if not ok:
            continue
        try:
            rows, _ = execute_sql(clean)
        except Exception:
            continue
        new_pass, why = compare(r["id"], rows)
        if new_pass != r["pass"]:
            changed.append(f"{r['id']}: {'PASS' if r['pass'] else 'FAIL'} → {'PASS' if new_pass else 'FAIL'} ({why})")
        r["pass"], r["why"] = new_pass, why
    biz = [r for r in data["results"] if r["type"] == "is"]
    old = data["meta"]["business_pass"]
    data["meta"]["business_pass"] = f"{sum(r['pass'] for r in biz)}/8"
    if changed:
        data["meta"]["rescored"] = ("Karşılaştırma hatası düzeltildikten sonra kayıtlı SQL'ler yeniden çalıştırılıp "
                                    f"yeniden puanlandı (model çağrılmadı). Önceki puan: {old}. Değişenler: "
                                    + "; ".join(changed))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=str)
        f.write("\n")
    print(f"{os.path.basename(path):<36} {old} → {data['meta']['business_pass']}  {'; '.join(changed)}")
