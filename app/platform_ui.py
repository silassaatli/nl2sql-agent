"""Veri kataloğu, profil, keşif, sorgu ve geçmiş ekranları."""
import sqlite3
import uuid
from app import governance as gov
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
from app.workspace import import_csv, use
from app.pipeline import ask, SQL_START
from app.charts import build_charts
from app.chart_view import show_chart
from config import DB_PATH, ALLOWED_TABLES


def render_platform(show_result):
    st.set_page_config(page_title="Ensight Analytics", page_icon="◈", layout="wide")
    from app.design import apply_design, hero, section
    apply_design()
    state=st.session_state
    state.setdefault("governance_session",uuid.uuid4().hex)
    for old in list(state.get("datasets",{}).values()):
        if "storage" in old: gov.persist(old,0,state.governance_session)
    state.datasets=gov.datasets()
    state.setdefault("history",[])
    with st.sidebar:
        st.markdown('<div class="brand">ensight<span>analytics</span></div><div class="workspace-label">VERİ ÇALIŞMA ALANI</div>',unsafe_allow_html=True)
        choices=["builtin"]+list(state.datasets)
        choices.sort(key=lambda k:gov.metadata(k).get("last_used") or gov.metadata(k).get("uploaded",""),reverse=True)
        selected=st.selectbox("Veri seti",choices,format_func=lambda k:gov.metadata(k)["name"],key="active_dataset")
        if state.get("last_selected")!=selected:
            gov.touch(selected)
            state.last_selected=selected
        st.caption("Son kullanılanlar üstte • Yazarak arayabilirsiniz")
        st.markdown('<div class="nav-label">KEŞFET & ANALİZ ET</div>',unsafe_allow_html=True)
        icons={"Genel bakış":"◫", "Veri keşfi":"▤", "Sorgu stüdyosu":"✦", "Sorgu geçmişi":"◷", "Veri yükle":"⊕", "Yönetişim":"◇"}
        page=st.radio("Çalışma alanı",list(icons),format_func=lambda x: icons[x]+"   "+x,label_visibility="collapsed")
        st.divider()
        st.markdown('<div class="sidebar-note"><span class="status-dot"></span> Yerel çalışma alanı<br><small>Verinizi keşfedin. Sorulara dönüştürün.</small></div>',unsafe_allow_html=True)
    dataset=state.datasets.get(selected)
    identity=dataset["id"] if dataset else "builtin"
    history=[h for h in state.history if h["dataset"]==identity]
    hero(page,gov.metadata(selected)["name"])
    if page=="Veri yükle":
        st.write("CSV dosyanızı yükleyin, önizlemeyi kontrol edin ve çalışma alanına ekleyin.")
        upload=st.file_uploader("CSV dosyası",type=["csv"])
        a,b=st.columns(2)
        sep=a.selectbox("Ayırıcı",[",",";","\t","|"])
        encoding=b.selectbox("Kodlama",["utf-8-sig","cp1254","latin1"])
        if upload:
            if upload.size>20*1024*1024:
                st.error("Dosya en fazla 20 MB olabilir.");return
            try:
                preview=pd.read_csv(upload,sep=sep,encoding=encoding,nrows=10)
                st.dataframe(preview,hide_index=True)
                st.caption("Yükleme sınırı: 100.000 satır / 100 sütun. Türler otomatik algılanır; keşif ekranından kontrol edin.")
                if st.button("Veri setini ekle",type="primary"):
                    item=import_csv(upload.getvalue(),upload.name,sep,encoding)
                    item=gov.persist(item,upload.size,state.governance_session)
                    name=upload.name
                    if name in state.datasets: name += " · "+datetime.now().strftime("%H:%M:%S")
                    state.datasets[name]=item
                    st.success("Veri seti eklendi. Soldaki listeden seçebilirsiniz.")
            except (ValueError,UnicodeError,pd.errors.ParserError) as exc: st.error(str(exc))
        return
    if dataset:
        frame=dataset["frame"]
        table="dataset"
    else:
        table="customers"
        if page in ["Veri keşfi","Genel bakış","Yönetişim"]:
            table=st.selectbox("İncelenen tablo",sorted(ALLOWED_TABLES))
        with sqlite3.connect(Path(DB_PATH).resolve().as_uri()+"?mode=ro",uri=True) as conn:
            frame=pd.read_sql_query('SELECT * FROM "'+table+'"',conn)
    if page=="Genel bakış":
        a,b,c,d=st.columns(4)
        a.metric("Kayıt",f"{len(frame):,}");b.metric("Sütun",len(frame.columns))
        c.metric("Eksik hücre",int(frame.isna().sum().sum()));d.metric("Tekrarlanan satır",int(frame.duplicated().sum()))
        st.write("")
        main,side=st.columns([2.1,1],gap="large")
        with main:
            with st.container(border=True,key="distribution"):
                section("Verinin görünümü", "Seçili tablodan hesaplanan dağılım")
                candidates=[c for c in frame.select_dtypes(exclude="number").columns if 2<=frame[c].nunique()<=15]
                if candidates:
                    dim=candidates[0]
                    counts=frame[dim].value_counts().rename_axis(dim).reset_index(name="Kayıt sayısı")
                    for _,chart in build_charts(counts.to_dict("records")):
                        show_chart(chart, "Veri dağılımı", "overview_distribution")
                else:
                    section("Sütun doluluk oranları", "Her sütundaki dolu hücrelerin yüzdesi")
                    completeness=(frame.notna().mean()*100).rename_axis("Sütun").reset_index(name="Doluluk (%)")
                    for _,chart in build_charts(completeness.to_dict("records")):
                        show_chart(chart, "Sütun doluluk oranları", "overview_completeness")
        with side:
            with st.container(border=True,key="health"):
                section("Veri sağlığı", "Analiz öncesi kısa kontrol")
                missing=int(frame.isna().sum().sum())
                total=frame.size
                completeness=100*(1-missing/total) if total else 0
                st.metric("Hücre doluluğu",f"%{completeness:.1f}")
                st.progress(completeness/100)
                st.caption(f"{missing:,} eksik hücre · {int(frame.duplicated().sum()):,} tekrarlanan satır")
                st.divider()
                st.markdown("**Bir sonraki adım**")
                st.write("Sorgu stüdyosunda bir soru sorun; sonuçları tablo ve grafiklerle inceleyin.")
        with st.container(border=True,key="preview"):
            section("Veri önizlemesi", "İlk 20 kayıt • Kaynak veriye hızlı bir bakış")
            st.dataframe(frame.head(20),hide_index=True,use_container_width=True)
    elif page=="Veri keşfi":
        st.subheader("Sütun profili")
        profile=pd.DataFrame({"Sütun":frame.columns,"Tür":frame.dtypes.astype(str).values,
            "Eksik":frame.isna().sum().values,"Benzersiz":frame.nunique().values})
        st.dataframe(profile,hide_index=True)
        nums=list(frame.select_dtypes(include="number").columns)
        if nums:
            st.subheader("Sayısal özet")
            st.dataframe(frame[nums].describe().T)
            st.subheader("Karşılaştırma oluştur")
            a,b,c=st.columns(3)
            dimension=a.selectbox("Gruplama",list(frame.columns))
            metric=b.selectbox("Ölçüt",nums)
            operation=c.selectbox("Hesaplama",["Toplam","Ortalama","En küçük","En büyük","Kayıt sayısı"])
            if dimension!=metric:
                grouped=frame.groupby(dimension,dropna=False)[metric].agg({"Toplam":"sum","Ortalama":"mean","En küçük":"min","En büyük":"max","Kayıt sayısı":"count"}[operation]).reset_index()
                st.dataframe(grouped,hide_index=True)
                for title,chart in build_charts(grouped.to_dict("records")): show_chart(chart, title, "explore_"+title)
        st.subheader("Veri tablosu")
        st.dataframe(frame.head(1000),hide_index=True)
        st.caption("Önizleme en fazla 1.000 satır gösterir. Profil ve karşılaştırmalar tüm seçili tabloyu kullanır.")
    elif page=="Sorgu stüdyosu":
        previous=next((h for h in reversed(history) if h["result"]["status"]=="success"),None)
        pending=state.pop("pending_question",None)
        if pending: state["studio_question"]=pending
        suggestions=(["Son 6 ayın aylık ciro trendi nedir?","Şehir bazında toplam ciroyu göster","Segmentlere göre aktif müşteri sayısı nedir?"]
                     if not dataset else ["Kaç kayıt var?", "Sütunlardaki eksik değer sayılarını göster", "İlk 10 kaydı göster"])
        st.markdown('<div class="section-label">BİR SORUYLA BAŞLAYIN</div>',unsafe_allow_html=True)
        for col,suggestion in zip(st.columns(3),suggestions):
            if col.button(suggestion,use_container_width=True): state["studio_question"]=suggestion
        with st.form("studio"):
            st.markdown("### Veriniz size ne anlatsın?")
            st.caption("Sorunuzu doğal dilde yazın veya bir SELECT sorgusu girin.")
            question=st.text_area("Sorunuz",key="studio_question",height=120,placeholder="Örneğin: Son altı ayın aylık cirosunu karşılaştır…",label_visibility="collapsed")
            follow=st.checkbox("Önceki başarılı soruya bağlı sor",disabled=previous is None)
            consent=st.checkbox("Sorunun ve sütun bilgilerinin Gemini API'ye gönderilmesine izin ver",value=False) if dataset else True
            submitted=st.form_submit_button("Analizi başlat  →",type="primary")
        if previous: st.caption("Bağlanılabilecek son soru: "+previous["question"])
        if submitted and question.strip():
            if dataset and not consent and not SQL_START.match(question):
                st.warning("Doğal dil analizi için API paylaşım seçeneğini işaretleyin. Doğrudan SELECT sorgusu yerel çalışır.")
            else:
                effective=question
                if follow and previous and not SQL_START.match(question):
                    effective=("Önceki soru bağlamındaki açık ölçüt ve filtreleri yeni soruda koru. Belirsizlik sürerse clarify döndür.\n"
                        +"Önceki soru: "+previous["effective"]+"\nÖnceki SQL: "+previous["result"]["sql"]+"\nYeni soru: "+question)
                policy=gov.metadata(identity)
                blocked=not policy.get("ai_enabled",False) or any(c.get("sensitive") for c in policy.get("columns",{}).values())
                if blocked and not SQL_START.match(question):
                    gov.event(identity,"ai_blocked",session=state.governance_session)
                    st.warning("Bu veri setinin gizlilik ayarları AI çağrısına izin vermiyor.")
                    return
                with st.spinner("Veri analiz ediliyor…"),use(dataset): result=ask(effective)
                gov.touch(identity)
                gov.event(identity,"query",result["status"],state.governance_session)
                state.history.append({"dataset":identity,"question":question,"effective":effective[-16000:],"result":result,"time":datetime.now().isoformat(timespec="seconds")})
                state.history=state.history[-100:]
                history=[h for h in state.history if h["dataset"]==identity]
        if history:
            result=history[-1]["result"]
            show_result(result,direct_sql=bool(SQL_START.match(history[-1]["question"])))
            if result["rows"]:
                # Formül olarak yorumlanabilecek metinler elektronik tablo dışa aktarımında nötrlenir.
                export=pd.DataFrame(result["rows"])
                for col in export.select_dtypes(include="object"):
                    export[col]=export[col].map(lambda v: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v)
                st.download_button("Sonucu CSV indir",export.to_csv(index=False).encode("utf-8-sig"),"analiz.csv","text/csv")
    elif page=="Sorgu geçmişi":
        st.caption("Bu oturumdaki son 100 sorgu saklanır. Yalnızca aktif veri setinin sorguları gösterilir.")
        for i,h in reversed(list(enumerate(history))):
            with st.expander(h["time"]+" · "+h["question"]):
                st.write(h["result"]["status"])
                st.code(h["result"]["sql"],language="sql")
                if st.button("Stüdyoya taşı",key=f"reuse_{i}"):
                    state.pending_question=h["question"]
                    st.info("Sorgu stüdyosuna geçip Analiz et düğmesine basın.")
        if not history:
            st.markdown('<div class="empty-state"><div class="empty-icon">◷</div><h3>Her analiz bir iz bırakır.</h3><p>İlk sorgunuzdan sonra sorularınız ve sonuçlarınız burada görünecek.</p></div>',unsafe_allow_html=True)
    else:
        gov.render(identity,frame,state.governance_session)
