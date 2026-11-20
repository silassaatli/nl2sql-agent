"""Panelin "Değerlendirme" sayfası: eval/run_eval.py'nin son TAM koşu raporunu gösterir.

Yalnızca dosya okur; model çağrısı yapmaz, eval'i panelden başlatmaz (API kotası yanlışlıkla harcanmasın).
Rapor üretmek için:  python eval/run_eval.py
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from config import BASE_DIR

REPORT_DIR = Path(BASE_DIR) / "eval" / "reports"


def _load(name: str) -> dict | None:
    path = REPORT_DIR / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _pct(stat: dict | None) -> str:
    if not stat or stat.get("accuracy") is None:
        return "—"
    return f"%{stat['accuracy'] * 100:.1f} ({stat['passed']}/{stat['scored']})"


def _group_table(groups: dict) -> pd.DataFrame:
    return pd.DataFrame([{"Grup": k, "Doğruluk": _pct(v), "Geçen": v["passed"], "Puanlanan": v["scored"],
                          "Toplam": v["total"]} for k, v in groups.items()])


def render_eval() -> None:
    report = _load("latest.json")
    if report is None:
        st.info("Henüz değerlendirme raporu yok. Proje kökünden `python eval/run_eval.py` çalıştırın.")
        return

    meta, s = report["meta"], report["summary"]
    st.caption(f"Son tam koşu: {meta['finished_at']} · Model: {meta['model']} · Bayraklar: {meta['flags'] or 'yok'} · "
               f"Kod özeti: {meta['code_hash']} · {meta['question_count']} soru (golden set: {meta['golden_set']})")
    st.caption("Sonuçlar gerçek model çıktısıdır. Bu sayfa yalnızca raporu gösterir; eval'i çalıştırmaz.")

    a, b, c, d = st.columns(4)
    a.metric("Genel doğruluk", _pct(s["overall"]))
    v = s["verdicts"]
    b.metric("PASS / FAIL", f"{v['PASS']} / {v['FAIL']}")
    c.metric("Puanlanmayan", f"{v['INFRA']} INFRA · {v['SKIP']} SKIP",
             help="INFRA: kota/ağ hatası. SKIP: gold_sql henüz yazılmadı. Doğruluk paydasına girmezler.")
    lat = s["latency"]
    d.metric("Gecikme (ort. / p95)", f"{lat['avg_ms']} / {lat['p95_ms']} ms" if lat["count"] else "—")

    left, right = st.columns(2)
    with left:
        st.markdown("**Zorluğa göre**")
        st.dataframe(_group_table(s["by_difficulty"]), hide_index=True, width="stretch")
        st.markdown("**Beklenen davranışa göre**")
        st.dataframe(_group_table(s["by_behavior"]), hide_index=True, width="stretch")
    with right:
        st.markdown("**Etikete göre**")
        st.dataframe(_group_table(s["by_tag"]), hide_index=True, width="stretch")

    failures = [r for r in report["results"] if r["verdict"] in ("FAIL", "INFRA")]
    st.subheader(f"Başarısız sorular ({len(failures)})")
    if not failures:
        st.write("Başarısız soru yok.")
    for r in failures:
        with st.expander(f"{r['id']} · {r['verdict']} · {r['question']}"):
            st.write(f"**Neden:** {r['reason']}")
            st.write(f"**Durum:** {r['status']} / {r['error_type']}")
            if r.get("assumption"):
                st.write(f"**Varsayım:** {r['assumption']}")
            st.markdown("**Üretilen SQL**")
            st.code(r["sql"] or "-- yok", language="sql")
            if r["expected_behavior"] == "sql":
                st.markdown("**Gold SQL**")
                st.code(r["gold_sql"], language="sql")
                st.write(f"Beklenen ({r['expected_row_count']} satır, ilk satırlar): {r['expected_preview']}")
                st.write(f"Gelen ({r['row_count']} satır, ilk satırlar): {r['actual_preview']}")

    repeated = _load("repeat_latest.json")
    if repeated:
        st.subheader("Tekrarlı koşular (ortalama)")
        st.caption("Her ayar birden fazla kez koşturuldu; ortalama, model değişkenliğinin etkisini azaltır.")
        st.dataframe(pd.DataFrame([{
            "Ayar": g["label"], "Koşu": g["runs"],
            "Tam koşuların ort.": (f"%{g['mean_complete'] * 100:.1f} ({g['complete_runs']} koşu)"
                                   if g.get("mean_complete") is not None else "—"),
            "Ortalama": f"%{g['accuracy']['mean'] * 100:.1f}",
            "Eksik soru": g.get("missing_total", 0),
            "En düşük": f"%{g['accuracy']['min'] * 100:.1f}", "En yüksek": f"%{g['accuracy']['max'] * 100:.1f}",
            "Ort. gecikme (ms)": g["latency_mean_ms"], "Düzelen (toplam)": g["recovered_total"],
        } for g in repeated["groups"]]), hide_index=True, width="stretch")
        labels = [g["label"] for g in repeated["groups"]]
        def cell(runs):
            asked = [v for v in runs if v != "EKSIK"]      # sorulmamış koşu başarısızlık sayılmaz
            return f"{asked.count('PASS')}/{len(asked)}"

        unstable = [{"No": qid, "Soru": q["question"], **{label: cell(q["passes"].get(label, [])) for label in labels}}
                    for qid, q in sorted(repeated["questions"].items())
                    if any(v in ("FAIL", "INFRA") for runs in q["passes"].values() for v in runs)]
        if unstable:
            st.markdown("**En az bir koşuda FAIL / INFRA olan sorular** (geçen koşu / sorulan koşu)")
            st.dataframe(pd.DataFrame(unstable), hide_index=True, width="stretch")

    comparison = _load("compare_latest.json")
    if comparison:
        st.subheader("Son karşılaştırma (A → B)")
        st.caption(f"A: {Path(comparison['a']['file']).name} · bayraklar {comparison['a']['meta']['flags'] or 'yok'}  |  "
                   f"B: {Path(comparison['b']['file']).name} · bayraklar {comparison['b']['meta']['flags'] or 'yok'}")
        st.dataframe(pd.DataFrame([{"Grup": row["group"], "A": _pct(row["a"]), "B": _pct(row["b"])}
                                   for row in comparison["rows"]]), hide_index=True, width="stretch")
        flips = comparison["flips"]
        st.write("Sonucu değişen sorular: " + (", ".join(f"{f['id']} ({f['a']} → {f['b']})" for f in flips) or "yok"))

    with st.expander("Bütün sorular"):
        st.dataframe(pd.DataFrame([{"No": r["id"], "Zorluk": r["difficulty"], "Beklenen": r["expected_behavior"],
                                    "Soru": r["question"], "Durum": r["status"], "Sonuç": r["verdict"],
                                    "Süre (ms)": r["latency_ms"]} for r in report["results"]]),
                     hide_index=True, width="stretch")
