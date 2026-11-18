"""Açık mor/beyaz tasarım sistemi."""
from html import escape
from pathlib import Path
import streamlit as st

DESCRIPTIONS={
"Genel bakış": "Verinizin tamamını görün. Bir sonraki içgörünüzü keşfedin.",
"Veri keşfi": "Sütunları tanıyın, dağılımları inceleyin, karşılaştırmalar oluşturun.",
"Sorgu stüdyosu": "Sorularınızı anlamlı sonuçlara dönüştürün.",
"Sorgu geçmişi": "Önceki analizlerinize dönün, keşfetmeye kaldığınız yerden devam edin.",
"Veri yükle": "Yeni bir veri kaynağı, yeni keşifler.",
"Yönetişim": "Verinizin kaynağı, kullanımı ve saklanması hakkında şeffaf bir görünüm.",
}
def apply_design():
    st.markdown("<style>"+Path(__file__).with_name("design.css").read_text(encoding="utf-8")+"</style>",unsafe_allow_html=True)
def hero(page,selected):
    st.markdown(f'<div class="topline"><span>Çalışma alanı <b>/ {escape(page)}</b></span><span class="source-chip">◈ &nbsp; {escape(selected)}</span></div><div class="page-heading"><div><h1>{escape(page)}</h1><p>{DESCRIPTIONS[page]}</p></div><span class="heading-art" aria-hidden="true">✳</span></div>',unsafe_allow_html=True)
def section(title,description):
    st.markdown(f'<div class="section-heading"><h3>{escape(title)}</h3><p>{escape(description)}</p></div>',unsafe_allow_html=True)
