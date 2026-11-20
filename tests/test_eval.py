"""eval/run_eval.py'nin karşılaştırma ve backoff mantığı. Model ÇAĞRILMAZ (elle kurulmuş ask() çıktıları);
bu testler eval kodunun doğruluğunu ölçer, model başarısını değil."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))

import run_eval  # noqa: E402
from app.llm import ModelUnavailableError  # noqa: E402

GOLD = (["City", "Ciro"], [["İstanbul", 100.004], ["Ankara", 50.0]])


def item(**overrides):
    base = {"id": "T", "question": "q", "difficulty": "orta", "tags": [], "gold_sql": "SELECT 1",
            "order_matters": False, "expected_behavior": "sql"}
    return {**base, **overrides}


def ok(rows, **extra):
    return {"status": "success", "rows": rows, "truncated": False, "message": "", "assumption": "",
            "error_type": None, **extra}


def test_same_values_different_names_and_rounding():
    rows = [{"Sehir": "İstanbul", "Toplam": 100.0}, {"Sehir": "Ankara", "Toplam": 50.001}]
    assert run_eval.judge(item(), ok(rows), GOLD)[0] == "PASS"


def test_extra_column_allowed_when_all_gold_columns_match():
    rows = [{"ID": 1, "City": "Ankara", "Ciro": 50.0}, {"ID": 2, "City": "İstanbul", "Ciro": 100.0}]
    assert run_eval.judge(item(), ok(rows), GOLD)[0] == "PASS"     # sırasız


def test_wrong_value_fails():
    rows = [{"City": "İstanbul", "Ciro": 100.0}, {"City": "Ankara", "Ciro": 49.0}]
    assert run_eval.judge(item(), ok(rows), GOLD)[0] == "FAIL"


def test_missing_gold_column_fails():
    rows = [{"City": "İstanbul"}, {"City": "Ankara"}]
    assert run_eval.judge(item(), ok(rows), GOLD)[0] == "FAIL"


def test_order_matters():
    rows = [{"City": "Ankara", "Ciro": 50.0}, {"City": "İstanbul", "Ciro": 100.0}]
    assert run_eval.judge(item(order_matters=True), ok(rows), GOLD)[0] == "FAIL"
    assert run_eval.judge(item(order_matters=False), ok(rows), GOLD)[0] == "PASS"


def test_row_count_and_truncation():
    assert run_eval.judge(item(), ok([{"City": "Ankara", "Ciro": 50.0}]), GOLD)[0] == "FAIL"
    rows = [{"City": "İstanbul", "Ciro": 100.0}, {"City": "Ankara", "Ciro": 50.0}]
    assert run_eval.judge(item(), ok(rows, truncated=True), GOLD)[0] == "FAIL"


@pytest.mark.parametrize("status,verdict", [("clarify", "PASS"), ("success", "FAIL"), ("rejected", "FAIL")])
def test_clarify(status, verdict):
    result = {"status": status, "rows": [], "message": "m", "error_type": None}
    assert run_eval.judge(item(expected_behavior="clarify"), result, None)[0] == verdict


@pytest.mark.parametrize("status,rows,verdict", [("rejected", [], "PASS"), ("success", [{"a": 1}], "FAIL"),
                                                 ("clarify", [], "FAIL")])
def test_refuse(status, rows, verdict):
    result = {"status": status, "rows": rows, "message": "m", "error_type": "unsupported"}
    assert run_eval.judge(item(expected_behavior="refuse"), result, None)[0] == verdict


def test_model_unavailable_is_infra_not_fail():
    result = {"status": "error", "rows": [], "message": "x", "error_type": "model_unavailable"}
    assert run_eval.judge(item(), result, GOLD)[0] == "INFRA"


def test_expects_assumption():
    gold = (["Ciro"], [[9.0]])
    q = item(expects_assumption=True)
    assert run_eval.judge(q, ok([{"Ciro": 9.0}]), gold)[0] == "FAIL"
    assert run_eval.judge(q, ok([{"Ciro": 9.0}], assumption="Geçen ay = Mayıs 2026"), gold)[0] == "PASS"


def test_summary_excludes_infra_and_skip():
    records = [{"verdict": v, "difficulty": "kolay", "expected_behavior": "sql", "tags": ["x"], "latency_ms": 10}
               for v in ("PASS", "FAIL", "INFRA", "SKIP")]
    s = run_eval.summarize(records)
    assert s["overall"] == {"passed": 1, "scored": 2, "total": 4, "accuracy": 0.5}


def test_backoff_retries_only_retryable(monkeypatch):
    monkeypatch.setattr(run_eval.time, "sleep", lambda s: None)
    calls = []

    def flaky(question, previous_error=None):
        calls.append(1)
        if len(calls) < 3:
            raise ModelUnavailableError("Gemini API (HTTP 429): Kota")
        return {"status": "ok"}

    stats = {"backoff_ms": 0.0, "backoff_retries": 0}
    assert run_eval.with_backoff(flaky, 5, 0.01, stats)("q") == {"status": "ok"}
    assert stats["backoff_retries"] == 2

    def no_key(question, previous_error=None):
        raise ModelUnavailableError("GEMINI_API_KEY ortam değişkenini tanımlayın.")

    with pytest.raises(ModelUnavailableError):
        run_eval.with_backoff(no_key, 5, 0.01, {"backoff_ms": 0.0, "backoff_retries": 0})("q")
