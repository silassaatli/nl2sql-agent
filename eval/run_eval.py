"""
Golden set değerlendirmesi: her soruyu MEVCUT ajandan (app.pipeline.ask) geçirir, beklenen sonucu her koşuda
gold_sql'den yeniden hesaplar, karşılaştırır ve rapor üretir. Gerçek Gemini çağrısı yapar (GEMINI_API_KEY gerekli).

Çalıştırma (proje kökünden):
    python eval/run_eval.py                      # bütün golden set
    python eval/run_eval.py --ids G01,G12        # alt küme
    python eval/run_eval.py --limit 5            # ilk 5 soru
    python eval/run_eval.py --sleep 2            # çağrılar arası 2 sn bekle
    python eval/run_eval.py --fresh              # önbelleği yok say, baştan sor
    python eval/run_eval.py --compare A.json B.json   # iki raporu karşılaştır (model çağrısı yok)

Kurallar:
- Karşılaştırma tests/run_all.py'deki columns_match ile yapılır (aynı kural, kopya yok): sütun adlarına bakılmaz,
  float'lar 2 ondalığa yuvarlanır, order_matters false ise satırlar sırasız (çoklu küme) karşılaştırılır,
  fazladan sütun serbest ama gold sütunlarının HEPSİ değerleriyle eşleşmeli.
- clarify sorusu: ajan "clarify" döndürmeli. refuse sorusu: ajan "rejected" döndürmeli ve satır dönmemeli.
- expects_assumption: değer doğru olmalı VE varsayım/mesajda çözülen tarih ("Mayıs" veya "2026-05") görünmeli.
- Kota/ağ hatası (model_unavailable) INFRA sayılır, gold_sql'i olmayan soru SKIP: ikisi de doğruluk paydasına girmez.

Kota ve kesinti:
- --sleep: model çağrısı yapılan sorular arasında bekleme.
- HTTP 429/5xx'te exponential backoff (generate_sql dışarıdan sarılır; ajanın mantığı değişmez). Bekleme süresi
  gecikmeden düşülür.
- Her cevap alındığı anda eval/cache/<koşu>.jsonl dosyasına yazılır; koşu kesilirse aynı komut kaldığı yerden
  devam eder. Önbellek anahtarı model + bayraklar + kod özeti (hash) içerir: prompt veya kod değişince eski cevaplar
  yeni koşuya karışmaz.
- Eval çağrılarının pipeline logu eval/logs/<koşu>.jsonl'e gider (uygulamanın logs/queries.jsonl dosyası şişmez).
"""

import argparse
import hashlib
import json
import math
import random
import re
import shutil
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime
from functools import partial
from pathlib import Path
from unittest.mock import patch

from gold import EVAL_DIR, GOLDEN_PATH, PROJECT_DIR, load_golden, run_gold

sys.path.insert(0, str(PROJECT_DIR / "tests"))

import config  # noqa: E402
from app import pipeline  # noqa: E402
from app.llm import ModelUnavailableError  # noqa: E402
from app.logger import write_log  # noqa: E402
from run_all import columns_match  # noqa: E402  (import edilince test çalıştırmaz: main() __main__ altında)

CACHE_DIR = EVAL_DIR / "cache"
LOG_DIR = EVAL_DIR / "logs"
REPORT_DIR = EVAL_DIR / "reports"

# Ajan akışını değiştiren config bayrakları. Var olanlar rapora ve önbellek anahtarına yazılır.
FLAG_NAMES = ["SELF_CORRECTION", "SELF_CORRECTION_MAX_RETRIES", "CLARIFY_GATE"]

# Kod özeti: bunlardan biri değişirse önbellek yeni dosyaya geçer.
CODE_FILES = ["config.py", "data/schema.json", *sorted(str(p.relative_to(PROJECT_DIR)) for p in (PROJECT_DIR / "app").glob("*.py"))]

RETRYABLE_HTTP = re.compile(r"HTTP (429|500|502|503|504)\b")


# --- Koşu kimliği ------------------------------------------------------------
def active_flags() -> dict:
    return {name: getattr(config, name) for name in FLAG_NAMES if hasattr(config, name)}


def code_hash() -> str:
    h = hashlib.sha256()
    for rel in CODE_FILES:
        path = PROJECT_DIR / rel
        if path.exists():
            h.update(rel.encode() + b"\0" + path.read_bytes())
    return h.hexdigest()[:10]


def run_name(flags: dict, digest: str) -> str:
    flag_part = "_".join(f"{k}-{v}" for k, v in flags.items()) or "varsayilan"
    model = re.sub(r"[^\w.-]+", "-", config.MODEL_NAME)
    return f"{model}__{flag_part}__{digest}"


# --- 429 backoff -------------------------------------------------------------
def with_backoff(generate, max_retries: int, base_s: float, stats: dict):
    """generate_sql'i sarar: yalnızca HTTP 429/5xx'te bekleyip tekrar dener. Diğer hatalar aynen yükselir."""
    def wrapped(question, previous_error=None):
        for attempt in range(max_retries + 1):
            try:
                return generate(question, previous_error=previous_error)
            except ModelUnavailableError as exc:
                if attempt == max_retries or not RETRYABLE_HTTP.search(str(exc)):
                    raise
                wait = base_s * 2 ** attempt + random.uniform(0, base_s)
                stats["backoff_ms"] += wait * 1000
                stats["backoff_retries"] += 1
                print(f"    {exc} → {wait:.1f} sn bekleniyor (deneme {attempt + 1}/{max_retries})")
                time.sleep(wait)
    return wrapped


# --- Önbellek ----------------------------------------------------------------
def load_cache(path: Path) -> dict:
    cache = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                cache[record["id"]] = record
    return cache


def append_cache(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


# --- Karşılaştırma -----------------------------------------------------------
def _round(value):
    return round(value, 2) if isinstance(value, float) else value


def judge(item: dict, result: dict, gold: tuple | None) -> tuple[str, str]:
    """Döner: (verdict, açıklama). verdict: PASS | FAIL | INFRA."""
    status = result.get("status")
    error_type = result.get("error_type")
    message = (result.get("message") or "").strip()
    behavior = item["expected_behavior"]

    if status == "error" and error_type == "model_unavailable":
        return "INFRA", f"Model erişilemedi: {message}"

    if behavior == "clarify":
        if status == "clarify":
            return "PASS", "Netleştirme istendi."
        return "FAIL", f"Netleştirme beklendi, gelen: {status}/{error_type}. {message}"

    if behavior == "refuse":
        if status == "rejected" and not result.get("rows"):
            return "PASS", f"Reddedildi ({error_type})."
        return "FAIL", f"Ret beklendi, gelen: {status}/{error_type}. {message}"

    # behavior == "sql"
    if status != "success":
        return "FAIL", f"Başarı beklendi, gelen: {status}/{error_type}. {message}"
    if result.get("truncated"):
        return "FAIL", "Sonuç satır limitinde kesildi."
    gold_columns, gold_rows = gold
    rows = result.get("rows") or []
    if len(rows) != len(gold_rows):
        return "FAIL", f"Satır sayısı: beklenen {len(gold_rows)}, gelen {len(rows)}."

    actual_values = [tuple(_round(v) for v in row.values()) for row in rows]
    expected_values = [tuple(_round(v) for v in row) for row in gold_rows]
    matched = columns_match(actual_values, expected_values, gold_columns, gold_columns,
                            ordered=item["order_matters"])
    if matched is None:
        return "FAIL", "Gold sütunları değerleriyle eşleşmedi" + (" (sıra dahil)." if item["order_matters"] else ".")

    if item.get("expects_assumption"):
        text = f"{result.get('assumption') or ''} {message}"
        if not re.search(r"Mayıs|2026-05", text):
            return "FAIL", "Değerler doğru ama çözülen tarih (Mayıs 2026) varsayım olarak görünmüyor."
    return "PASS", "Sonuç gold ile eşleşti."


def preview(rows, n: int = 3) -> list:
    return [list(r.values()) if isinstance(r, dict) else list(r) for r in (rows or [])[:n]]


# --- Özet ve rapor -----------------------------------------------------------
def rate(items: list[dict]) -> dict:
    scored = [r for r in items if r["verdict"] in ("PASS", "FAIL")]
    passed = sum(r["verdict"] == "PASS" for r in scored)
    return {"passed": passed, "scored": len(scored), "total": len(items),
            "accuracy": round(passed / len(scored), 4) if scored else None}


def latency_stats(records: list[dict]) -> dict:
    values = sorted(r["latency_ms"] for r in records if r["latency_ms"] is not None and r["verdict"] != "SKIP")
    if not values:
        return {"count": 0, "avg_ms": None, "median_ms": None, "p95_ms": None}
    p95 = values[max(0, math.ceil(0.95 * len(values)) - 1)]
    return {"count": len(values), "avg_ms": round(statistics.mean(values)),
            "median_ms": round(statistics.median(values)), "p95_ms": p95}


def summarize(records: list[dict]) -> dict:
    groups = {"difficulty": defaultdict(list), "behavior": defaultdict(list), "tag": defaultdict(list)}
    for r in records:
        groups["difficulty"][r["difficulty"]].append(r)
        groups["behavior"][r["expected_behavior"]].append(r)
        for tag in r["tags"]:
            groups["tag"][tag].append(r)
    return {
        "overall": rate(records),
        "by_difficulty": {k: rate(v) for k, v in sorted(groups["difficulty"].items())},
        "by_behavior": {k: rate(v) for k, v in sorted(groups["behavior"].items())},
        "by_tag": {k: rate(v) for k, v in sorted(groups["tag"].items())},
        "verdicts": {v: sum(r["verdict"] == v for r in records) for v in ("PASS", "FAIL", "INFRA", "SKIP")},
        "latency": latency_stats(records),
        "pipeline_retries": sum(r.get("retry_count") or 0 for r in records),
        "backoff_retries": sum(r.get("backoff_retries") or 0 for r in records),
    }


def _pct(stat: dict) -> str:
    if stat["accuracy"] is None:
        return "—"
    return f"%{stat['accuracy'] * 100:.1f} ({stat['passed']}/{stat['scored']})"


def _cell(value, limit: int = 80) -> str:
    text = " ".join(str(value if value is not None else "").split())
    return (text[: limit - 1] + "…" if len(text) > limit else text).replace("|", "\\|")


def to_markdown(report: dict) -> str:
    meta, s = report["meta"], report["summary"]
    lat = s["latency"]
    lines = [
        "# Golden set değerlendirme raporu", "",
        f"Üretim: {meta['finished_at']} · Model: `{meta['model']}` · Bayraklar: `{meta['flags'] or 'yok'}` · "
        f"Kod özeti: `{meta['code_hash']}` · Komut: `{meta['command']}`", "",
        "Sonuçlar gerçek model çıktısıdır (mock yok). Beklenen sonuçlar her koşuda gold_sql'den yeniden hesaplandı.",
        f"Kapsam: {meta['question_count']} soru" + (" (alt küme)" if meta["subset"] else " (bütün golden set)")
        + f" · önbellekten gelen: {meta['from_cache']}", "",
        "## Özet", "",
        "| Ölçü | Değer |", "|---|---|",
        f"| **Genel doğruluk** | **{_pct(s['overall'])}** |",
        f"| PASS / FAIL / INFRA / SKIP | {s['verdicts']['PASS']} / {s['verdicts']['FAIL']} / "
        f"{s['verdicts']['INFRA']} / {s['verdicts']['SKIP']} |",
        f"| Gecikme ort. / medyan / p95 | {lat['avg_ms']} / {lat['median_ms']} / {lat['p95_ms']} ms |",
        f"| Pipeline yeniden denemeleri | {s['pipeline_retries']} |",
        f"| 429/5xx backoff tekrarları | {s['backoff_retries']} |", "",
        "INFRA: kota/ağ hatası, SKIP: gold_sql henüz yazılmadı. İkisi doğruluk paydasına girmez.", "",
    ]
    for title, key in (("Zorluğa göre", "by_difficulty"), ("Beklenen davranışa göre", "by_behavior"),
                       ("Etikete göre", "by_tag")):
        lines += [f"## {title}", "", "| Grup | Doğruluk |", "|---|---|"]
        lines += [f"| {k} | {_pct(v)} |" for k, v in s[key].items()]
        lines.append("")

    failures = [r for r in report["results"] if r["verdict"] in ("FAIL", "INFRA")]
    lines += ["## Başarısız sorular", ""]
    if not failures:
        lines += ["Yok.", ""]
    for r in failures:
        lines += [
            f"### {r['id']} · {r['difficulty']} · {r['verdict']}", "",
            f"- **Soru:** {r['question']}",
            f"- **Durum:** {r['status']} / {r['error_type']}",
            f"- **Neden:** {r['reason']}",
            f"- **Varsayım:** {r['assumption'] or '—'}",
            "- **Üretilen SQL:**", "", "```sql", r["sql"] or "-- yok", "```",
        ]
        if r["expected_behavior"] == "sql":
            lines += ["- **Gold SQL:**", "", "```sql", r["gold_sql"], "```",
                      f"- **Beklenen (ilk satırlar, {r['expected_row_count']} satır):** `{r['expected_preview']}`",
                      f"- **Gelen (ilk satırlar, {r['row_count']} satır):** `{r['actual_preview']}`"]
        lines.append("")

    lines += ["## Bütün sorular", "", "| No | Zorluk | Beklenen | Soru | Durum | Sonuç | Süre (ms) |",
              "|---|---|---|---|---|---|---|"]
    for r in report["results"]:
        lines.append(f"| {r['id']} | {r['difficulty']} | {r['expected_behavior']} | {_cell(r['question'], 60)} | "
                     f"{r['status'] or '—'} | {r['verdict']} | {r['latency_ms'] if r['latency_ms'] is not None else '—'} |")
    return "\n".join(lines) + "\n"


def write_outputs(report: dict, stem: str, update_latest: bool) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / f"{stem}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (REPORT_DIR / f"{stem}.md").write_text(to_markdown(report), encoding="utf-8")
    if update_latest:   # panel en son TAM koşuyu gösterir; alt küme koşuları latest'i ezmez
        shutil.copyfile(json_path, REPORT_DIR / "latest.json")
        shutil.copyfile(REPORT_DIR / f"{stem}.md", REPORT_DIR / "latest.md")
    return json_path


# --- İki raporu karşılaştırma ------------------------------------------------
def compare(path_a: Path, path_b: Path) -> dict:
    a, b = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (path_a, path_b))
    va = {r["id"]: r["verdict"] for r in a["results"]}
    vb = {r["id"]: r["verdict"] for r in b["results"]}
    common = sorted(set(va) & set(vb))
    flips = [{"id": i, "question": next(r["question"] for r in b["results"] if r["id"] == i),
              "a": va[i], "b": vb[i]} for i in common if va[i] != vb[i]]
    rows = []
    for title, key in (("Genel", None), ("Zorluk", "by_difficulty"), ("Davranış", "by_behavior"), ("Etiket", "by_tag")):
        if key is None:
            rows.append({"group": "Genel", "a": a["summary"]["overall"], "b": b["summary"]["overall"]})
            continue
        for k in sorted(set(a["summary"][key]) | set(b["summary"][key])):
            rows.append({"group": f"{title}: {k}", "a": a["summary"][key].get(k), "b": b["summary"][key].get(k)})
    return {"a": {"file": str(path_a), "meta": a["meta"], "latency": a["summary"]["latency"],
                  "pipeline_retries": a["summary"]["pipeline_retries"]},
            "b": {"file": str(path_b), "meta": b["meta"], "latency": b["summary"]["latency"],
                  "pipeline_retries": b["summary"]["pipeline_retries"]},
            "rows": rows, "flips": flips}


def compare_markdown(c: dict) -> str:
    def acc(stat):
        return _pct(stat) if stat else "—"

    def delta(sa, sb):
        if not sa or not sb or sa["accuracy"] is None or sb["accuracy"] is None:
            return "—"
        return f"{(sb['accuracy'] - sa['accuracy']) * 100:+.1f} puan"

    a, b = c["a"], c["b"]
    lines = [
        "# Eval karşılaştırması", "",
        f"- **A:** `{Path(a['file']).name}` · bayraklar `{a['meta']['flags'] or 'yok'}` · kod `{a['meta']['code_hash']}`",
        f"- **B:** `{Path(b['file']).name}` · bayraklar `{b['meta']['flags'] or 'yok'}` · kod `{b['meta']['code_hash']}`", "",
        "| Grup | A | B | Fark (B − A) |", "|---|---|---|---|",
    ]
    lines += [f"| {r['group']} | {acc(r['a'])} | {acc(r['b'])} | {delta(r['a'], r['b'])} |" for r in c["rows"]]
    lines += ["", f"Ortalama gecikme: A {a['latency']['avg_ms']} ms · B {b['latency']['avg_ms']} ms. "
              f"Pipeline yeniden denemeleri: A {a['pipeline_retries']} · B {b['pipeline_retries']}.", "",
              "## Sonucu değişen sorular", ""]
    if not c["flips"]:
        lines.append("Yok.")
    lines += [f"- {f['id']}: {f['a']} → {f['b']} · {f['question']}" for f in c["flips"]]
    return "\n".join(lines) + "\n"


# --- Ana akış ----------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Golden set değerlendirmesi")
    parser.add_argument("--ids", help="virgülle ayrılmış soru id'leri (ör. G01,G12)")
    parser.add_argument("--limit", type=int, help="ilk N soru")
    parser.add_argument("--sleep", type=float, default=1.0, help="model çağrısı yapılan sorular arası bekleme (sn)")
    parser.add_argument("--max-backoff", type=int, default=5, help="429/5xx'te en fazla kaç kez beklenip denensin")
    parser.add_argument("--backoff-base", type=float, default=2.0, help="ilk bekleme (sn); her denemede 2 katına çıkar")
    parser.add_argument("--fresh", action="store_true", help="önbelleği yok say, bütün soruları yeniden sor")
    parser.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"), help="iki raporu karşılaştır")
    args = parser.parse_args()

    if args.compare:
        c = compare(Path(args.compare[0]), Path(args.compare[1]))
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stem = "compare_" + datetime.now().strftime("%Y%m%d-%H%M%S")
        md = compare_markdown(c)
        for name in (stem, "compare_latest"):
            (REPORT_DIR / f"{name}.json").write_text(json.dumps(c, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            (REPORT_DIR / f"{name}.md").write_text(md, encoding="utf-8")
        print(md)
        print(f"Kaydedildi: {REPORT_DIR / (stem + '.md')}")
        return

    items = load_golden()
    if args.ids:
        wanted = [i.strip() for i in args.ids.split(",") if i.strip()]
        unknown = set(wanted) - {it["id"] for it in items}
        if unknown:
            parser.error(f"golden set'te olmayan id: {sorted(unknown)}")
        items = [it for it in items if it["id"] in wanted]
    if args.limit:
        items = items[: args.limit]
    subset = bool(args.ids or args.limit)

    flags, digest = active_flags(), code_hash()
    name = run_name(flags, digest)
    cache_path = CACHE_DIR / f"{name}.jsonl"
    if args.fresh and cache_path.exists():
        cache_path.unlink()
    cache = load_cache(cache_path)
    log_path = LOG_DIR / f"{name}.jsonl"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    started = datetime.now().isoformat(timespec="seconds")
    print(f"Koşu: {name} · {len(items)} soru · önbellekte {len(cache)} cevap")

    records, from_cache, model_called_before = [], 0, False
    for item in items:
        gid = item["id"]
        gold = None
        if item["expected_behavior"] == "sql":
            if not item["gold_sql"].strip():
                records.append({**_base(item), "verdict": "SKIP", "reason": "gold_sql henüz yazılmadı.",
                                **_empty_result()})
                print(f"{gid} | SKIP | gold_sql yok")
                continue
            gold = run_gold(item["gold_sql"])   # beklenen sonuç her koşuda yeniden hesaplanır

        cached = cache.get(gid)
        if cached and cached["question"] == item["question"]:
            entry = cached
            from_cache += 1
        else:
            if model_called_before and args.sleep > 0:
                time.sleep(args.sleep)
            stats = {"backoff_ms": 0.0, "backoff_retries": 0}
            wrapped = with_backoff(pipeline.generate_sql, args.max_backoff, args.backoff_base, stats)
            with patch.object(pipeline, "generate_sql", wrapped), \
                 patch.object(pipeline, "write_log", partial(write_log, path=str(log_path))):
                result = pipeline.ask(item["question"])
            model_called_before = True
            entry = {"id": gid, "question": item["question"], "result": result,
                     "backoff_ms": round(stats["backoff_ms"]), "backoff_retries": stats["backoff_retries"],
                     "asked_at": datetime.now().isoformat(timespec="seconds")}
            infra = result.get("status") == "error" and result.get("error_type") == "model_unavailable"
            if not infra:            # kota hatası önbelleğe yazılmaz: devam edince yeniden sorulur
                append_cache(cache_path, entry)

        result = entry["result"]
        verdict, reason = judge(item, result, gold)
        duration = result.get("duration_ms")
        latency = None if duration is None else max(0, duration - entry.get("backoff_ms", 0))
        records.append({
            **_base(item), "verdict": verdict, "reason": reason,
            "status": result.get("status"), "error_type": result.get("error_type"),
            "sql": result.get("sql") or "", "assumption": result.get("assumption") or "",
            "message": result.get("message") or "", "retry_count": result.get("retry_count"),
            "row_count": len(result.get("rows") or []), "actual_preview": preview(result.get("rows")),
            "expected_row_count": len(gold[1]) if gold else None, "expected_preview": preview(gold[1]) if gold else None,
            "latency_ms": latency, "backoff_retries": entry.get("backoff_retries", 0),
        })
        print(f"{gid} | {verdict} | {reason}")

    report = {
        "meta": {"started_at": started, "finished_at": datetime.now().isoformat(timespec="seconds"),
                 "model": config.MODEL_NAME, "flags": flags, "code_hash": digest, "run_name": name,
                 "golden_set": str(GOLDEN_PATH.relative_to(PROJECT_DIR)),
                 "golden_hash": hashlib.sha256(GOLDEN_PATH.read_bytes()).hexdigest()[:10],
                 "question_count": len(items), "subset": subset, "from_cache": from_cache,
                 "command": "python eval/run_eval.py " + " ".join(sys.argv[1:])},
        "summary": summarize(records),
        "results": records,
    }
    stem = "eval_" + datetime.now().strftime("%Y%m%d-%H%M%S") + ("_altkume" if subset else "")
    path = write_outputs(report, stem, update_latest=not subset)
    s = report["summary"]
    print(f"\nGenel doğruluk: {_pct(s['overall'])} · PASS {s['verdicts']['PASS']} · FAIL {s['verdicts']['FAIL']} · "
          f"INFRA {s['verdicts']['INFRA']} · SKIP {s['verdicts']['SKIP']}")
    print(f"Rapor: {path} (+ .md)")


def _base(item: dict) -> dict:
    return {k: item.get(k) for k in ("id", "question", "difficulty", "tags", "expected_behavior",
                                     "order_matters", "gold_sql")}


def _empty_result() -> dict:
    return {"status": None, "error_type": None, "sql": "", "assumption": "", "message": "", "retry_count": None,
            "row_count": 0, "actual_preview": [], "expected_row_count": None, "expected_preview": None,
            "latency_ms": None, "backoff_retries": 0}


if __name__ == "__main__":
    main()
