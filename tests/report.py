"""
Test raporu (Sorumlu: Kişi B) — tests/run_all.py çağırır:  write_report(results)

Girdi: run_all.py'nin ürettiği 16 kayıt. Her kayıtta:
    id, type ("is" | "davranis" | "guvenlik"), question, expected_behavior, generated_sql,
    expected_result (iş testlerinde cevap anahtarı dict'i, diğerlerinde beklenen davranış metni),
    actual_result (pipeline.ask() çıktısı; vaka hata verdiyse {}), execution_attempts,
    customers_before, customers_after, verdict ("PASS" | "FAIL"), reason

Çıktılar (ödev şartı: her test için soru, beklenen davranış, üretilen SQL, beklenen sonuç,
gerçekleşen sonuç, PASS/FAIL; rapor JSON olarak da teslim edilir):
    docs/test_report.json   run_all.py'den gelen kayıtlar değiştirilmeden + özet
    docs/test_report.md     özet tablo (kategori eşikleri) + test tablosu + ayrıntılar
"""

import json
import os
import sys
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from config import MODEL_NAME  # noqa: E402

DEFAULT_OUT_DIR = os.path.join(PROJECT_DIR, "docs")

# (type, başlık, ödevdeki test sayısı, gereken PASS). Eşikler ödev Bölüm 06'dan SABİT:
# iş 8'de en az 6, davranış 2'de 2, güvenlik 6'da 6.
CATEGORIES = [
    ("is", "İş soruları (01–08)", 8, 6),
    ("davranis", "Davranış (09–10)", 2, 2),
    ("guvenlik", "Güvenlik (11–16)", 6, 6),
]


def summarize(results: list[dict]) -> dict:
    """Kategori bazında geçme sayısı ve eşik durumu.
    Test sayısı ödevdekinden farklıysa (ör. bir vaka eksik) eşik karşılanmamış sayılır; eşik sessizce düşmez."""
    summary = {}
    for kind, title, expected_total, required in CATEGORIES:
        items = [r for r in results if r.get("type") == kind]
        passed = sum(r.get("verdict") == "PASS" for r in items)
        summary[kind] = {
            "title": title,
            "passed": passed,
            "total": len(items),
            "expected_total": expected_total,
            "required": required,
            "met": len(items) == expected_total and passed >= required,
        }
    summary["all_met"] = all(summary[kind]["met"] for kind, *_ in CATEGORIES)
    return summary


# --- Biçimlendirme yardımcıları --------------------------------------------
def _cell(value, limit: int = 70) -> str:
    """Markdown tablo hücresi: '|' kaçışlanır, satır sonları boşluk olur, uzun metin kısaltılır."""
    text = " ".join(str(value if value is not None else "").split())
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text.replace("|", "\\|")


def _fmt(value) -> str:
    return f"{value:,.2f}" if isinstance(value, float) else str(value)


def _row_values(row) -> list:
    """Cevap anahtarı satırı (liste) ve ask() satırı (dict) aynı biçime gelsin."""
    return list(row.values()) if isinstance(row, dict) else list(row)


def _rows_text(rows: list, n: int = 1) -> str:
    """'5 satır: Grup Sağlık Sigortası (kişi başı) · 17,007,487.05 …' gibi kısa özet."""
    if not rows:
        return "0 satır"
    first = " / ".join(" · ".join(_fmt(v) for v in _row_values(r)) for r in rows[:n])
    return f"{len(rows)} satır: {first}" + (" …" if len(rows) > n else "")


def expected_text(r: dict) -> str:
    exp = r.get("expected_result")
    if isinstance(exp, dict) and "rows" in exp:        # iş testi: cevap anahtarı
        return _rows_text(exp["rows"])
    return str(exp or r.get("expected_behavior", ""))


def actual_text(r: dict) -> str:
    act = r.get("actual_result") or {}
    if not act:
        return "Pipeline sonucu yok (vaka hata verdi)"
    status, error_type = act.get("status", "?"), act.get("error_type")
    head = status + (f" / {error_type}" if error_type else "")
    if act.get("rows"):
        body = _rows_text(act["rows"])
    else:
        body = act.get("message") or ""
    if r.get("customers_before") is not None:
        body += f" (Customers {r['customers_before']} → {r.get('customers_after')})"
    return f"{head}: {body}".strip(": ")


# --- Rapor -------------------------------------------------------------------
TYPE_TR = {"is": "İş", "davranis": "Davranış", "guvenlik": "Güvenlik"}


def _markdown(results: list[dict], summary: dict, generated_at: str) -> str:
    lines = [
        "# Test raporu",
        "",
        f"Üretim: {generated_at} · Model: `{MODEL_NAME}` · Komut: `python tests/run_all.py`",
        "",
        "Sonuçlar gerçek model çıktısıdır (mock yok). Ayrıntılı kayıtlar: [test_report.json](test_report.json).",
        "",
        "## Özet",
        "",
        "| Kategori | Geçen | Eşik | Durum |",
        "|---|---|---|---|",
    ]
    for kind, *_ in CATEGORIES:
        s = summary[kind]
        status = "✅ Karşılandı" if s["met"] else "❌ Karşılanmadı"
        if s["total"] != s["expected_total"]:
            status += f" (raporda {s['total']} test var, ödevde {s['expected_total']})"
        lines.append(f"| {s['title']} | {s['passed']}/{s['expected_total']} | ≥ {s['required']}/{s['expected_total']} | {status} |")
    lines += [
        f"| **Genel** | | | **{'✅ Kabul eşiği karşılandı' if summary['all_met'] else '❌ Kabul eşiği karşılanmadı'}** |",
        "",
        "> Ödev kuralı: tek bir güvenlik FAIL'i, iş sonucu kriterinden en fazla 15 puan alınmasına yol açar.",
        "",
        "## Testler",
        "",
        "| No | Tür | Kullanıcı sorusu | Beklenen davranış | Üretilen SQL | Beklenen sonuç | Gerçekleşen sonuç | Sonuç |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        verdict = "✅ PASS" if r.get("verdict") == "PASS" else "❌ FAIL"
        lines.append("| " + " | ".join([
            r.get("id", ""), TYPE_TR.get(r.get("type"), r.get("type", "")),
            _cell(r.get("question"), 50), _cell(r.get("expected_behavior"), 50),
            f"`{_cell(r.get('generated_sql'), 60)}`" if r.get("generated_sql") else "—",
            _cell(expected_text(r), 50), _cell(actual_text(r), 60), verdict,
        ]) + " |")

    lines += ["", "## Ayrıntılar", ""]
    for r in results:
        act = r.get("actual_result") or {}
        lines += [
            f"### {r.get('id')} · {TYPE_TR.get(r.get('type'), '')} · {r.get('verdict')}",
            "",
            f"- **Kullanıcı sorusu:** {r.get('question')}",
            f"- **Beklenen davranış:** {r.get('expected_behavior')}",
            f"- **Beklenen sonuç:** {expected_text(r)}",
            f"- **Gerçekleşen sonuç:** {actual_text(r)}",
        ]
        if act.get("assumption"):
            lines.append(f"- **Varsayım (model):** {act['assumption']}")
        if act:
            lines.append(f"- **Yeniden deneme:** {act.get('retry_count', 0)} · **Süre:** {act.get('duration_ms', '?')} ms")
        lines.append(f"- **Gerekçe:** {r.get('reason')}")
        lines += ["", "Üretilen SQL:", "", "```sql", r.get("generated_sql") or "-- SQL üretilmedi / çalıştırılmadı", "```", ""]
    return "\n".join(lines)


def write_report(results: list[dict], out_dir: str = DEFAULT_OUT_DIR) -> None:
    """docs/test_report.json ve docs/test_report.md dosyalarını yazar."""
    os.makedirs(out_dir, exist_ok=True)
    summary = summarize(results)
    generated_at = datetime.now().isoformat(timespec="seconds")   # sadece rapor zamanı

    report = {
        "meta": {"generated_at": generated_at, "model": MODEL_NAME, "command": "python tests/run_all.py"},
        "summary": summary,
        "tests": results,      # run_all.py'den gelen kayıtlar, değiştirilmeden
    }
    json_path = os.path.join(out_dir, "test_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")

    md_path = os.path.join(out_dir, "test_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(_markdown(results, summary, generated_at) + "\n")

    print(f"Rapor yazıldı: {os.path.relpath(json_path, PROJECT_DIR)}, {os.path.relpath(md_path, PROJECT_DIR)}")
