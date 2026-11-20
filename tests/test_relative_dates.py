"""config.RELATIVE_DATES: göreli tarih çözücü (app/semantic.py) ve varsayım eki (app/llm.py). Ağ yok."""

import io
import json
from unittest.mock import Mock

import pytest

import config
from app import llm
from app.semantic import date_note, relative_dates, resolve_dates


def spans(question):
    return [(s["start"], s["end"]) for s in relative_dates(question)]


@pytest.mark.parametrize("question,expected", [
    ("Geçen ayki satışlar ne kadar?", [("2026-05-01", "2026-05-31")]),
    ("Bu ay kaç sipariş var?", [("2026-06-01", "2026-06-30")]),
    ("Bu yıl toplam ciro?", [("2026-01-01", "2026-06-30")]),
    ("Yılbaşından bu yana ciro?", [("2026-01-01", "2026-06-30")]),
    ("Geçen yılın cirosu", [("2025-01-01", "2025-12-31")]),
    ("Bu çeyrekte ciro", [("2026-04-01", "2026-06-30")]),
    ("Son üç ayın cirosu", [("2026-04-01", "2026-06-30")]),
    ("Geçen hafta kaç sipariş?", [("2026-06-22", "2026-06-28")]),     # 2026-06-30 salı
    ("Bu hafta kaç sipariş?", [("2026-06-29", "2026-06-30")]),
    ("Dün kaç sipariş geldi?", [("2026-06-29", "2026-06-29")]),
])
def test_relative_spans(question, expected):
    assert spans(question) == expected


@pytest.mark.parametrize("question", [
    "Bugüne kadar hiç alım yapmamış müşteriler",   # "tüm zamanlar"; bugün filtresi DEĞİL
    "Son 6 ayın aylık ciro trendi nedir?".replace("Son 6 ayın ", ""),
    "Dünya kartı satışları",
    "Kategorilere göre toplam ciro nedir?",
])
def test_no_false_matches(question):
    assert relative_dates(question) == []


@pytest.mark.parametrize("phrase", ["son 6 ay", "son 30 gün", "son 90 gün"])
def test_general_rule_matches_config_ranges(phrase):
    """Genel kural, config.DATE_RANGES'te elle yazılmış aralıklarla aynı sonucu vermeli."""
    assert spans(phrase) == [config.DATE_RANGES[phrase]]


def test_flag_off_keeps_old_behavior(monkeypatch):
    monkeypatch.setattr(config, "RELATIVE_DATES", False)
    assert resolve_dates("Geçen ayki satışlar ne kadar?") == []
    assert "EKLEME" in date_note("Geçen ayki satışlar ne kadar?")


def test_flag_on_resolves_and_drops_misleading_note(monkeypatch):
    monkeypatch.setattr(config, "RELATIVE_DATES", True)
    note = date_note("Geçen ayki satışlar ne kadar?")
    assert "2026-05-01" in note and "2026-05-31" in note and "EKLEME" not in note


def test_flag_on_no_duplicate_with_config_range(monkeypatch):
    monkeypatch.setattr(config, "RELATIVE_DATES", True)
    assert len(resolve_dates("Son 6 ayın aylık ciro trendi nedir?")) == 1


def test_flag_on_month_inside_year_not_swallowed(monkeypatch):
    monkeypatch.setattr(config, "RELATIVE_DATES", True)
    found = [(s["start"], s["end"]) for s in resolve_dates("Bu yıl Mart ayında ciro ne kadar?")]
    assert ("2026-03-01", "2026-03-31") in found


# --- llm.py: varsayım eki ----------------------------------------------------
@pytest.fixture
def gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(llm, "build_system_prompt", lambda: "SQL system instructions")

    def answer(assumption):
        body = {"status": "ok", "sql": "SELECT 1", "assumption": assumption, "message": ""}
        envelope = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(body)}]}}]}
        monkeypatch.setattr(llm.request, "urlopen", Mock(return_value=io.BytesIO(json.dumps(envelope).encode())))
    return answer


def test_assumption_added_when_flag_on(gemini, monkeypatch):
    monkeypatch.setattr(config, "RELATIVE_DATES", True)
    gemini("Satış ciro olarak hesaplandı.")
    result = llm.generate_sql("Geçen ayki satışlar ne kadar?")
    assert result["assumption"].startswith("Satış ciro olarak hesaplandı.")
    assert "geçen ay (Mayıs 2026) = 2026-05-01 – 2026-05-31" in result["assumption"]


def test_assumption_unchanged_when_flag_off(gemini, monkeypatch):
    monkeypatch.setattr(config, "RELATIVE_DATES", False)
    gemini("Satış ciro olarak hesaplandı.")
    assert llm.generate_sql("Geçen ayki satışlar ne kadar?")["assumption"] == "Satış ciro olarak hesaplandı."
