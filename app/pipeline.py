"""Soruları modele, doğrudan SQL girdilerini doğrulayıcıya yönlendirir."""

import re
import sqlite3
from datetime import datetime, timezone
from time import perf_counter

from sqlglot.errors import ParseError, TokenError

from app.db import execute_sql
from app.llm import ModelUnavailableError, generate_sql
from app.logger import write_log
from app.validator import validate_sql
from config import MAX_RETRIES, MAX_ROWS, MODEL_NAME
import config  # SELF_CORRECTION bayrakları sorgu anında okunur (eval aynı süreçte açıp kapatabilsin)

EMPTY_RESULT_HINT = (
    "Sorgu hatasız çalıştı ama hiç satır döndürmedi. Filtre değerlerini (şemadaki yazım, tarih aralığı) "
    "ve JOIN koşullarını kontrol et. Sonuç gerçekten boşsa aynı SQL'i döndür."
)


# Başlangıçtaki boşluk ve yorumları atlayıp ilk SQL komutunu tanır.
# Güvenlik kararı validate_sql() ve SQLite authorizer tarafından verilir.
SQL_START = re.compile(
    r"\A(?:\s|--[^\r\n]*(?:\r?\n|$)|/\*[\s\S]*?\*/)*"
    r"(?:SELECT|WITH|VALUES|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|"
    r"ATTACH|DETACH|PRAGMA|REPLACE|EXPLAIN|VACUUM|REINDEX|ANALYZE|"
    r"BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE|END)\b",
    re.IGNORECASE,
)


def _db_error_type(exc: sqlite3.DatabaseError) -> str:
    """SQLite hatasını pipeline'ın kullandığı hata türüne çevirir."""
    message = str(exc).lower()
    code = getattr(exc, "sqlite_errorcode", None)

    if (
        code == sqlite3.SQLITE_AUTH
        or "not authorized" in message
        or "prohibited" in message
    ):
        return "security_rejected"

    if code == sqlite3.SQLITE_INTERRUPT or message == "interrupted":
        return "timeout"

    if "no such column" in message or "ambiguous column name" in message:
        return "unknown_field"

    if "syntax error" in message or "incomplete input" in message:
        return "parse_error"

    return "database_error"


def ask(question: str) -> dict:
    started = perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    retry_count = 0
    previous_error = None
    sql = ""
    assumption = ""
    direct_sql = bool(SQL_START.match(question))

    # Deneysel self-correction (config.SELF_CORRECTION). Kapalıyken: MAX_RETRIES, yalnızca
    # parse_error / unknown_field yeniden denenir, "attempts" alanı oluşmaz (bugünkü davranış).
    self_correction = bool(config.SELF_CORRECTION) and not direct_sql
    max_retries = config.SELF_CORRECTION_MAX_RETRIES if self_correction else MAX_RETRIES
    attempts = []
    last_empty_sql = None

    def finish(
        status,
        message,
        error_type=None,
        *,
        rows=None,
        truncated=False,
    ):
        """Her çıkışta aynı sonuç biçimini ve bir log kaydını üretir."""
        result = {
            "status": status,
            "sql": sql,
            "rows": rows if rows is not None else [],
            "truncated": truncated,
            "message": message,
            "assumption": assumption,
            "error_type": error_type,
            "retry_count": retry_count,
            "duration_ms": round((perf_counter() - started) * 1000),
        }
        record = {
            "timestamp": timestamp,
            "question": question,
            "sql": sql,
            "status": status,
            "error_type": error_type,
            "retry_count": retry_count,
            "row_count": len(result["rows"]),
            "duration_ms": result["duration_ms"],
            "model": None if direct_sql else MODEL_NAME,
        }
        if self_correction:
            attempts.append({"attempt": retry_count + 1, "sql": sql, "status": status, "error_type": error_type})
            result["attempts"] = attempts
            record["attempts"] = attempts

        write_log(record)

        return result

    if not question.strip():
        return finish(
            "clarify",
            "Hangi soruyu yanıtlamamı istersiniz?",
            "ambiguous",
        )

    while True:
        sql = ""
        assumption = ""

        if direct_sql:
            # Kullanıcının SQL'i doğrudan ortak doğrulama aşamasına gider.
            sql = question.strip()
        else:
            try:
                reply = generate_sql(
                    question,
                    previous_error=previous_error,
                )
            except ModelUnavailableError:
                return finish(
                    "error",
                    "SQL üreten modele erişilemedi.",
                    "model_unavailable",
                )
            except ValueError:
                return finish(
                    "error",
                    "Model yanıtı okunamadı.",
                    "invalid_model_response",
                )

            if not isinstance(reply, dict):
                return finish(
                    "error",
                    "Model yanıtının biçimi geçersiz.",
                    "invalid_model_response",
                )

            model_status = reply.get("status")
            message = reply.get("message")
            message = message.strip() if isinstance(message, str) else ""

            if model_status == "clarify":
                return finish(
                    "clarify",
                    message or "Sorunuzu netleştirir misiniz?",
                    "ambiguous",
                )

            if model_status == "unsupported":
                return finish(
                    "rejected",
                    message or "Bu bilgi veri setinde yok.",
                    "unsupported",
                )

            if model_status != "ok":
                return finish(
                    "error",
                    "Model bilinmeyen bir durum döndürdü.",
                    "invalid_model_response",
                )

            candidate = reply.get("sql")
            if not isinstance(candidate, str) or not candidate.strip():
                return finish(
                    "error",
                    "Model bir SQL sorgusu döndürmedi.",
                    "invalid_model_response",
                )

            sql = candidate.strip()

            if isinstance(reply.get("assumption"), str):
                assumption = reply["assumption"].strip()

        # Her iki giriş yolu da aynı validator'dan geçer.
        try:
            valid, clean_sql, reason = validate_sql(sql)
        except (ParseError, TokenError):
            valid, clean_sql, reason = False, "", "parse_error"

        if not valid:
            error_type = reason.partition(":")[0]

            if error_type != "parse_error":
                return finish(
                    "rejected",
                    "Sorgu güvenlik kurallarını geçemedi.",
                    error_type,
                )

            detail = "SQL, SQLite sözdizimine göre ayrıştırılamadı."
        else:
            # Yürütücü yalnızca validator'ın temizlediği SQL'i alır.
            sql = clean_sql

            try:
                rows, truncated = execute_sql(sql)
            except sqlite3.DatabaseError as exc:
                error_type = _db_error_type(exc)

                if error_type == "security_rejected":
                    return finish(
                        "rejected",
                        "Veritabanı bu sorguya izin vermedi.",
                        error_type,
                    )

                if error_type == "timeout":
                    return finish(
                        "error",
                        "Sorgu süre sınırını aştı.",
                        error_type,
                    )

                if error_type == "database_error" and not self_correction:
                    return finish(
                        "error",
                        "Veritabanı sorguyu çalıştıramadı.",
                        error_type,
                    )

                detail = str(exc)
            else:
                # Self-correction açıkken boş sonuç da düzeltme denemesi tetikler. Model aynı SQL'i
                # geri gönderirse sonuç gerçekten boş kabul edilir (aşağıdaki normal başarı yolu).
                if (not rows and self_correction and retry_count < max_retries
                        and sql != last_empty_sql):
                    last_empty_sql = sql
                    attempts.append({"attempt": retry_count + 1, "sql": sql, "error_type": "empty_result"})
                    previous_error = f"Önceki SQL:\n{sql}\nHata: {EMPTY_RESULT_HINT}"
                    retry_count += 1
                    continue

                if not rows:
                    message = "Bu koşullara uyan kayıt bulunamadı."
                elif truncated:
                    message = f"İlk {MAX_ROWS} satır gösteriliyor."
                else:
                    message = "Sorgu tamamlandı."

                if assumption:
                    message = (
                        f"{message} Kullanılan varsayım: {assumption}"
                    )

                return finish(
                    "success",
                    message,
                    None if rows else "empty_result",
                    rows=rows,
                    truncated=truncated,
                )

        # Kullanıcının SQL'i hatalıysa sonucu doğrudan döndür.
        # Modelin ürettiği SQL için en fazla max_retries düzeltme denemesi yap
        # (bayrak kapalıyken MAX_RETRIES = 1).
        if direct_sql or retry_count >= max_retries:
            if error_type == "unknown_field":
                message = "Sorgudaki sütun adı çözümlenemedi."
            elif error_type == "database_error":    # yalnızca self-correction açıkken buraya gelir
                message = "Veritabanı sorguyu çalıştıramadı."
            else:
                message = "Geçerli bir SQL sorgusu elde edilemedi."

            return finish("error", message, error_type)

        if self_correction:
            attempts.append({"attempt": retry_count + 1, "sql": sql, "error_type": error_type})
        previous_error = f"Önceki SQL:\n{sql}\nHata: {detail}"
        retry_count += 1