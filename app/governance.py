"""Yerel kalıcı katalog ve denetim kaydı."""
import json, sqlite3, shutil, uuid
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from config import BASE_DIR
ROOT=Path(BASE_DIR)/"data"/"workspace"
class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try: return super().__exit__(*args)
        finally: self.close()
def connect():
    ROOT.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(ROOT/"catalog.db",factory=ClosingConnection)
    c.execute("CREATE TABLE IF NOT EXISTS catalog (id TEXT PRIMARY KEY, metadata TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS events (time TEXT, dataset TEXT, session TEXT, action TEXT, detail TEXT)")
    return c
def metadata(identity):
    with connect() as c:
        row=c.execute("SELECT metadata FROM catalog WHERE id=?",(identity,)).fetchone()
    return json.loads(row[0]) if row else {"name":"Örnek satış verisi","description":"","ai_enabled":True,"columns":{},"last_used":""}
def save(identity,m):
    with connect() as c: c.execute("INSERT OR REPLACE INTO catalog VALUES (?,?)",(identity,json.dumps(m,ensure_ascii=False)))
def event(identity,action,detail="",session="local"):
    with connect() as c: c.execute("INSERT INTO events VALUES (?,?,?,?,?)",(datetime.now(timezone.utc).isoformat(),identity,session,action,detail))
def persist(item,size,session):
    identity=uuid.uuid4().hex
    target=ROOT/(identity+".db")
    connect().close()
    shutil.copyfile(item["path"],target)
    item["storage"].cleanup()
    item.update(id=identity,path=str(target))
    del item["storage"]
    m={"name":item["name"],"source":item["name"],"description":"","ai_enabled":False,"columns":{},"uploaded":datetime.now(timezone.utc).isoformat(),"last_used":"","bytes":size,"schema":item["schema"],"rows":len(item["frame"])}
    save(identity,m);event(identity,"upload",session=session)
    return item
def datasets():
    with connect() as c: rows=c.execute("SELECT id,metadata FROM catalog WHERE id!='builtin'").fetchall()
    result={}
    for identity,raw in rows:
        m=json.loads(raw);path=ROOT/(identity+".db")
        if m.get("archived") or not path.exists(): continue
        with sqlite3.connect(path.as_uri()+"?mode=ro",uri=True,factory=ClosingConnection) as c: frame=pd.read_sql_query("SELECT * FROM dataset",c)
        result[identity]={"name":m["name"],"id":identity,"path":str(path),"frame":frame,"schema":m["schema"]}
    return result
def touch(identity):
    m=metadata(identity);m["last_used"]=datetime.now(timezone.utc).isoformat();save(identity,m)
def render(identity,frame,session):
    m=metadata(identity)
    catalog,quality,privacy,audit=st.tabs(["Katalog","Kalite","Gizlilik","İşlem geçmişi"])
    with catalog:
        st.caption("Yerel kalıcı çalışma alanı • Veriler uygulama kapandığında korunur.")
        st.write({"Kaynak":m.get("source","Örnek satış CSV dosyaları"),"Yüklenme":m.get("uploaded","Proje verisi"),"Dosya boyutu (bayt)":m.get("bytes"),"Satır":m.get("rows",len(frame))})
        with st.form("catalog_metadata_"+identity):
            name=st.text_input("Veri seti adı",m["name"])
            desc=st.text_area("Açıklama",m.get("description",""))
            entries=[{"Sütun":col,"Açıklama":m.get("columns",{}).get(col,{}).get("description",""),"Birim":m.get("columns",{}).get(col,{}).get("unit",""),"Hassas":m.get("columns",{}).get(col,{}).get("sensitive",False),"Zorunlu":m.get("columns",{}).get(col,{}).get("required",False),"Benzersiz":m.get("columns",{}).get(col,{}).get("unique",False)} for col in frame.columns]
            edited=st.data_editor(pd.DataFrame(entries),disabled=["Sütun"],hide_index=True,use_container_width=True)
            if st.form_submit_button("Katalog ve kuralları kaydet"):
                if not name.strip(): st.error("Ad boş olamaz.")
                else:
                    m.update(name=name.strip(),description=desc)
                    m.setdefault("columns",{})
                    for row in edited.to_dict("records"):
                        m["columns"][row["Sütun"]]={"description":row["Açıklama"],"unit":row["Birim"],"sensitive":bool(row["Hassas"]),"required":bool(row["Zorunlu"]),"unique":bool(row["Benzersiz"])}
                    save(identity,m);event(identity,"metadata_updated",session=session);st.rerun()
        st.info("Saklama: siz arşivleyene kadar yerelde tutulur. Arşivleme dosyaları ve denetim kayıtlarını silmez; veri setini seçim listesinden kaldırır.")
        if identity!="builtin" and st.checkbox("Bu veri setini aktif listeden kaldırmak istiyorum"):
            if st.button("Veri setini arşivle"):
                m["archived"]=True;save(identity,m);event(identity,"archived",session=session);st.rerun()
    with quality:
        issues=frame.isna().any(axis=1)|frame.duplicated(keep=False)
        rows=[]
        for col in frame.columns:
            rule=m.get("columns",{}).get(col,{})
            invalid=pd.Series(False,index=frame.index)
            if rule.get("required"): invalid |= frame[col].isna() | frame[col].astype(str).str.strip().eq("")
            if rule.get("unique"): invalid |= frame[col].notna() & frame[col].duplicated(keep=False)
            issues |= invalid
            rows.append({"Sütun":col,"Eksik":int(frame[col].isna().sum()),"Benzersiz değer":int(frame[col].nunique()),"Kural ihlali":int(invalid.sum())})
        st.dataframe(rows,hide_index=True)
        st.caption("Eksik hücre ve tekrarlı satırlar bulgudur; kural ihlalleri katalogdaki zorunlu/benzersiz tercihlerine göre hesaplanır.")
        st.dataframe(frame[issues].head(500),hide_index=True)
        out=frame[issues].copy()
        for col in out.select_dtypes(include="object"):
            out[col]=out[col].map(lambda v:"'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v)
        st.download_button("Sorunlu satırları indir",out.to_csv(index=False).encode("utf-8-sig"),"kalite_bulgulari.csv","text/csv")
    with privacy:
        st.write("AI kapalı olduğunda doğal dil sorguları API'ye gönderilmez. Doğrudan SQL yerelde çalışmaya devam eder.")
        st.write("Hassas sütunlar tanımlanmışsa bu veri setinde AI çağrısı tamamen engellenir; soru veya önceki bağlam üzerinden sızıntı önlenir. Yerel görüntüleme yetkisi değişmez.")
        enabled=st.checkbox("Gemini ile analize izin ver",value=m.get("ai_enabled",False),key="ai_"+identity)
        if st.button("Gizlilik ayarını kaydet"):
            m["ai_enabled"]=enabled;save(identity,m);event(identity,"ai_enabled" if enabled else "ai_disabled",session=session);st.rerun()
    with audit:
        with connect() as c: records=pd.read_sql_query("SELECT time AS Tarih,session AS Oturum,action AS İşlem,detail AS Ayrıntı FROM events WHERE dataset=? ORDER BY time DESC LIMIT 500",c,params=(identity,))
        st.dataframe(records,hide_index=True)
        st.caption("Son 500 olay. Kullanıcı hesabı yerine oturum kimliği tutulur. Yerel kayıtlar değiştirilemez bir denetim sistemi değildir.")
