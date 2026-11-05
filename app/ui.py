"""
Minimum arayüz (Sorumlu: Kişi B)

Çalıştırma:  streamlit run app/ui.py

Ekranda olması gerekenler (ödev şartı):
- Soru giriş kutusu
- Üretilen SQL
- Durum (başarılı / netleştirme gerekli / reddedildi / hata)
- Sonuç tablosu
- Hata veya açıklama mesajı
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="NL2SQL Agent", layout="wide")
st.title("NL2SQL Agent")
st.caption("Türkçe sorunuzu yazın, SQL'e çevirip güvenli şekilde çalıştıralım.")

question = st.text_input("Soru", placeholder="Örn: İzmir'in toplam cirosu nedir?")

if st.button("Sor") and question:
    # TODO: from app.pipeline import ask  →  result = ask(question)
    # TODO: result["sql"], result["status"], result["rows"], result["message"] göster
    st.info("Pipeline henüz bağlanmadı.")
