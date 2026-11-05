"""
Minimum arayüz (Sorumlu: Kişi B)

Çalıştırma:  streamlit run app/ui.py

Ekranda olanlar (ödev şartı): soru girişi, üretilen SQL, durum, sonuç tablosu, hata veya açıklama mesajı.
Ek olarak: modelin varsayımı (test 09: sessiz varsayım olmasın), süre ve yeniden deneme sayısı, demo için örnek sorular.

Arayüz HİÇBİR güvenlik kontrolü yapmaz; sadece app.pipeline.ask()'ı çağırır ve sonucunu gösterir.
Bütün kontroller (validate_sql + salt-okunur bağlantı + authorizer) pipeline'dadır.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st  # noqa: E402

from app.pipeline import ask  # noqa: E402
from config import MAX_ROWS, MODEL_NAME, REFERENCE_DATE  # noqa: E402

# ask() durumu → (ekranda görünen ad, Streamlit kutusu)
STATUS_VIEW = {
    "success": ("Başarılı", st.success),
    "clarify": ("Netleştirme gerekli", st.info),
    "rejected": ("Reddedildi", st.warning),
    "error": ("Hata", st.error),
}

# Pipeline'ın hata türleri → kısa Türkçe açıklama
ERROR_TYPE_TR = {
    "empty_result": "sorgu çalıştı ama koşullara uyan kayıt yok",
    "ambiguous": "soru birden fazla şekilde yorumlanabilir",
    "unsupported": "istek desteklenmiyor (bilgi veri modelinde yok veya izin verilmeyen bir işlem)",
    "parse_error": "SQL ayrıştırılamadı",
    "multiple_statements": "birden fazla SQL ifadesi (yalnızca tek SELECT kabul edilir)",
    "not_select": "SELECT olmayan ifade (veri değiştiren komutlar kabul edilmez)",
    "forbidden_statement": "sorgunun içinde yasaklı ifade var",
    "table_not_allowed": "izinli olmayan tablo (yalnızca Customers, Products, Orders, OrderItems)",
    "security_rejected": "veritabanı motoru erişimi reddetti (authorizer)",
    "unknown_field": "sorguda veri modelinde olmayan bir sütun var",
    "timeout": "sorgu süre sınırını aştı",
    "database_error": "veritabanı sorguyu çalıştıramadı",
    "model_unavailable": "dil modeline ulaşılamadı (Ollama çalışıyor mu?)",
    "invalid_model_response": "dil modelinin cevabı okunamadı",
}

# Demo için örnek sorular (ödev Bölüm 07: başarılı soru, belirsiz/hatalı durum, zararlı sorgu)
EXAMPLES = [
    "Son 6 ayın aylık ciro trendi nedir?",
    "En iyi müşteri kimdir?",
    "Müşterilerin doğum tarihi nedir?",
    "SELECT * FROM Customers; DELETE FROM Customers",
]


SQL_NOTE = {
    "success": "Çalıştırılan SQL: doğrulayıcının yorumları atıp yeniden ürettiği hal (modelin ham metni değil).",
    "rejected": "Bu SQL güvenlik kurallarından geçemedi ve çalıştırılmadı; veri değişmedi.",
    "error": "Bu SQL başarıyla çalıştırılamadı.",
}


def show_result(result: dict) -> None:
    """ask() sonucunu gösterir: durum, mesaj, varsayım, SQL, sonuç tablosu, süre."""
    status = result.get("status", "error")
    label, box = STATUS_VIEW.get(status, (status, st.error))
    error_type = result.get("error_type") or ""
    base_type = error_type.partition(":")[0]
    detail = f" — {ERROR_TYPE_TR.get(base_type, error_type)} (`{error_type}`)" if error_type else ""
    box(f"**{label}**{detail}")

    message = result.get("message") or ""
    if message:
        st.write(message)
    assumption = result.get("assumption") or ""
    if assumption and assumption not in message:     # success'te pipeline varsayımı mesaja zaten ekliyor
        st.info(f"**Varsayım:** {assumption}")
    if assumption:
        # Varsayım metni modelin kendi açıklamasıdır ve doğrulanmaz; esas olan çalışan SQL'dir.
        st.caption("Varsayım, modelin kendi açıklamasıdır; neyin hesaplandığını SQL gösterir.")

    st.subheader("Üretilen SQL")
    if result.get("sql"):
        st.code(result["sql"], language="sql")
        if status in SQL_NOTE:
            st.caption(SQL_NOTE[status])
    else:
        st.caption("SQL üretilmedi; veritabanında hiçbir sorgu çalıştırılmadı.")

    rows = result.get("rows") or []
    if status == "success":
        st.subheader("Sonuç")
        if rows:
            st.dataframe(rows, width="stretch", hide_index=True)
            st.caption(f"{len(rows)} satır")
            if result.get("truncated"):
                st.warning(f"Sonuç {MAX_ROWS} satırla sınırlandı; daha fazla kayıt var.")
        else:
            st.write("Koşullara uyan kayıt bulunamadı.")

    st.caption(f"Süre: {result.get('duration_ms', '?')} ms · Yeniden deneme: {result.get('retry_count', 0)}")


def _use_example(text: str) -> None:
    """Örnek düğmesinin callback'i: soru kutusunu doldurur ve soruyu çalıştırılmak üzere işaretler.
    Callback, betik yeniden çalışmadan ÖNCE çağrıldığı için widget değeri burada güvenle değiştirilir."""
    st.session_state["question"] = text
    st.session_state["run"] = True


st.set_page_config(page_title="NL2SQL Agent", layout="wide")
st.title("NL2SQL Agent")
st.caption(f"Türkçe iş sorunuzu yazın; SQL'e çevrilip salt-okunur bağlantıyla çalıştırılır. "
           f"Model: {MODEL_NAME} · Referans tarih: {REFERENCE_DATE} · En fazla {MAX_ROWS} satır gösterilir.")

with st.form("soru_formu"):
    question = st.text_input("Soru", key="question", placeholder="Örn: İzmir'in toplam cirosu nedir?")
    submitted = st.form_submit_button("Sor", type="primary")

st.write("Örnek sorular:")
for col, example in zip(st.columns(len(EXAMPLES)), EXAMPLES):
    col.button(example, on_click=_use_example, args=(example,), width="stretch")

run = submitted or st.session_state.pop("run", False)
if run:
    if not question.strip():
        st.warning("Lütfen bir soru yazın.")
    else:
        st.divider()
        with st.spinner("Model SQL üretiyor ve sorgu güvenli şekilde çalıştırılıyor…"):
            try:
                result = ask(question)
            except Exception as e:      # ask() hataları kendisi yönetir; bu sadece beklenmeyen durumlar için
                st.error(f"Beklenmeyen hata: {type(e).__name__}: {e}")
                st.stop()
        show_result(result)
