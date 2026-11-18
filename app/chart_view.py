"""Grafik görüntüleme ve yerel PNG/SVG dışa aktarma."""
import re
from io import BytesIO, StringIO
import streamlit as st


def export_chart(chart, title, fmt):
    output=BytesIO() if fmt=="png" else StringIO()
    chart.properties(width=1000, height=420, title=title).save(output, format=fmt, engine="vl-convert", scale_factor=2 if fmt=="png" else 1)
    return output.getvalue() if fmt=="png" else output.getvalue().encode("utf-8")


def show_chart(chart, title, key):
    st.altair_chart(chart, use_container_width=True)
    # Dışa aktarımı yalnızca istendiğinde hazırla; sayfa açılışını yavaşlatma.
    with st.expander("Grafiği indir"):
        fmt=st.selectbox("Dosya biçimi",["PNG", "SVG"],key=key+"_format",help="PNG: sunum ve belgeler. SVG: büyütüldüğünde netliğini korur.")
        if st.button("İndirme dosyasını hazırla",key=key+"_prepare"):
            try:
                content=export_chart(chart,title,fmt.lower())
            except Exception:
                st.error("Grafik dosyası hazırlanamadı. vl-convert-python bağımlılığının kurulu olduğunu kontrol edin.")
            else:
                name=re.sub(r"[^\w-]+","_",title).strip("_") or "grafik"
                st.download_button(fmt+" indir",content,name+"."+fmt.lower(),"image/png" if fmt=="PNG" else "image/svg+xml",key=key+"_download",on_click="ignore")
