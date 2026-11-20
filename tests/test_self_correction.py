"""config.SELF_CORRECTION bayrağının pipeline davranışı. Model ve veritabanı sahte (mock); ağ yok.
Bayrak KAPALIYKEN davranışın eskisiyle aynı olduğu da burada sabitlenir."""

import sqlite3
from unittest.mock import Mock

import pytest

import config
from app import pipeline


def ok(sql):
    return {"status": "ok", "sql": sql, "assumption": "", "message": ""}


@pytest.fixture
def env(monkeypatch):
    """generate_sql sırayla verilen SQL'leri döndürür; execute_sql her SQL için tanımlı sonucu verir."""
    monkeypatch.setattr(pipeline, "write_log", Mock())
    state = {"replies": [], "outcomes": {}, "prompts": []}

    def fake_generate(question, previous_error=None):
        state["prompts"].append(previous_error)
        return ok(state["replies"].pop(0))

    def fake_execute(sql):
        outcome = state["outcomes"][sql]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome, False

    monkeypatch.setattr(pipeline, "generate_sql", fake_generate)
    monkeypatch.setattr(pipeline, "execute_sql", fake_execute)
    return state


def flag(monkeypatch, on, max_retries=2):
    monkeypatch.setattr(config, "SELF_CORRECTION", on)
    monkeypatch.setattr(config, "SELF_CORRECTION_MAX_RETRIES", max_retries)


BAD = "SELECT Yok FROM Customers"
BAD2 = "SELECT Yok2 FROM Customers"
GOOD = "SELECT Name FROM Customers"
EMPTY = "SELECT Name FROM Customers WHERE City = 'izmir'"
NO_COL = sqlite3.OperationalError("no such column: Yok")


# --- Bayrak kapalı: bugünkü davranış ----------------------------------------
def test_off_unknown_field_retried_once(env, monkeypatch):
    flag(monkeypatch, False)
    env["replies"] = [BAD, BAD2]
    env["outcomes"] = {BAD: NO_COL, BAD2: NO_COL}
    r = pipeline.ask("soru")
    assert (r["status"], r["error_type"], r["retry_count"]) == ("error", "unknown_field", 1)
    assert "attempts" not in r


def test_off_empty_result_not_retried(env, monkeypatch):
    flag(monkeypatch, False)
    env["replies"] = [EMPTY]
    env["outcomes"] = {EMPTY: []}
    r = pipeline.ask("soru")
    assert (r["status"], r["error_type"], r["retry_count"]) == ("success", "empty_result", 0)
    assert "attempts" not in r
    log = pipeline.write_log.call_args.args[0]
    assert "attempts" not in log


def test_off_database_error_not_retried(env, monkeypatch):
    flag(monkeypatch, False)
    env["replies"] = [BAD]
    env["outcomes"] = {BAD: sqlite3.OperationalError("no such function: MEDIAN")}
    r = pipeline.ask("soru")
    assert (r["status"], r["error_type"], r["retry_count"]) == ("error", "database_error", 0)


# --- Bayrak açık -------------------------------------------------------------
def test_on_two_corrections_then_success(env, monkeypatch):
    flag(monkeypatch, True)
    env["replies"] = [BAD, BAD2, GOOD]
    env["outcomes"] = {BAD: NO_COL, BAD2: NO_COL, GOOD: [{"Name": "A"}]}
    r = pipeline.ask("soru")
    assert (r["status"], r["retry_count"]) == ("success", 2)
    assert [a["error_type"] for a in r["attempts"]] == ["unknown_field", "unknown_field", None]
    assert "no such column" in env["prompts"][1]          # hata modele geri verildi
    assert pipeline.write_log.call_args.args[0]["attempts"] == r["attempts"]


def test_on_retry_limit_from_config(env, monkeypatch):
    flag(monkeypatch, True, max_retries=1)
    env["replies"] = [BAD, BAD2]
    env["outcomes"] = {BAD: NO_COL, BAD2: NO_COL}
    r = pipeline.ask("soru")
    assert (r["status"], r["retry_count"]) == ("error", 1)


def test_on_empty_result_triggers_retry(env, monkeypatch):
    flag(monkeypatch, True)
    env["replies"] = [EMPTY, GOOD]
    env["outcomes"] = {EMPTY: [], GOOD: [{"Name": "A"}]}
    r = pipeline.ask("soru")
    assert (r["status"], r["retry_count"], r["rows"]) == ("success", 1, [{"Name": "A"}])
    assert "hiç satır döndürmedi" in env["prompts"][1]


def test_on_same_empty_sql_accepted_as_truly_empty(env, monkeypatch):
    flag(monkeypatch, True)
    env["replies"] = [EMPTY, EMPTY]
    env["outcomes"] = {EMPTY: []}
    r = pipeline.ask("soru")
    assert (r["status"], r["error_type"], r["retry_count"]) == ("success", "empty_result", 1)
    assert len(env["prompts"]) == 2                       # üçüncü çağrı yapılmadı


def test_on_database_error_retried(env, monkeypatch):
    flag(monkeypatch, True)
    env["replies"] = [BAD, GOOD]
    env["outcomes"] = {BAD: sqlite3.OperationalError("no such function: MEDIAN"), GOOD: [{"Name": "A"}]}
    r = pipeline.ask("soru")
    assert (r["status"], r["retry_count"]) == ("success", 1)


def test_on_security_rejection_never_retried(env, monkeypatch):
    flag(monkeypatch, True)
    env["replies"] = ["SELECT name FROM sqlite_master"]
    r = pipeline.ask("soru")
    assert (r["status"], r["retry_count"]) == ("rejected", 0)
    assert len(env["prompts"]) == 1


def test_on_timeout_never_retried(env, monkeypatch):
    flag(monkeypatch, True)
    env["replies"] = [GOOD]
    env["outcomes"] = {GOOD: sqlite3.OperationalError("interrupted")}
    r = pipeline.ask("soru")
    assert (r["status"], r["error_type"], r["retry_count"]) == ("error", "timeout", 0)


def test_on_direct_sql_not_affected(env, monkeypatch):
    flag(monkeypatch, True)
    env["outcomes"] = {"SELECT Name FROM Customers": []}
    r = pipeline.ask("SELECT Name FROM Customers")
    assert (r["status"], r["retry_count"]) == ("success", 0)
    assert "attempts" not in r and env["prompts"] == []
