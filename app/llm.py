"""
LLM ile SQL üretimi (Sorumlu: Kişi B)

Görev: Kullanıcının Türkçe sorusunu, Ollama üzerinden Qwen modeline göndererek JSON cevap almak.

Prompt'ta olması gerekenler (plan PDF'i, Ek C):
- Rol: "SQLite uzmanısın, tek bir SELECT üret, sadece JSON döndür"
- Şema (schema.py'den)
- Metrik tanımları (ciro = SUM(Quantity * UnitPrice), Price KULLANILMAZ ...)
- Hazır tarih aralıkları (config.DATE_RANGES), referans tarih 2026-06-30
- Kurallar: şemada olmayan bilgi → "unsupported", belirsiz soru → "clarify"
- 2–4 few-shot örnek (test sorularının birebir kopyası OLMASIN)

Ollama çağrısında: format="json", options={"temperature": 0}
"""

from config import MODEL_NAME, TEMPERATURE  # noqa: F401


class ModelUnavailableError(Exception):
    """Ollama kapalı / model yüklenemedi."""


def build_system_prompt() -> str:
    raise NotImplementedError


def generate_sql(question: str, previous_error: str | None = None) -> dict:
    """
    Döner: {"status": "ok" | "clarify" | "unsupported",
            "sql": "SELECT ...",
            "assumption": "...",
            "message": "..."}
    previous_error doluysa (yeniden deneme), hata mesajı modele geri verilir.
    Model erişilemezse ModelUnavailableError fırlatır.
    """
    raise NotImplementedError
