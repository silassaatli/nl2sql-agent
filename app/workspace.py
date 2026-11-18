"""Oturuma özel veri bağlamı; paylaşılan global ayarlar değiştirilmez."""
from contextvars import ContextVar
from contextlib import contextmanager
from pathlib import Path
import tempfile
import sqlite3
import hashlib
import io
import pandas as pd
from config import DB_PATH, ALLOWED_TABLES

active = ContextVar("dataset", default=None)
def current():
    return active.get()
def db_path():
    return current()["path"] if current() else DB_PATH
def allowed_tables():
    return {"dataset"} if current() else ALLOWED_TABLES
@contextmanager
def use(dataset):
    token=active.set(dataset)
    try: yield
    finally: active.reset(token)
def import_csv(raw, name, separator, encoding):
    if len(raw)>20*1024*1024: raise ValueError("En fazla 20 MB CSV yükleyin.")
    frame=pd.read_csv(io.BytesIO(raw), sep=separator, encoding=encoding, nrows=100001)
    if len(frame)>100000 or len(frame.columns)>100: raise ValueError("En fazla 100.000 satır ve 100 sütun destekleniyor.")
    if frame.empty: raise ValueError("CSV boş.")
    if any(not str(c).strip() for c in frame.columns): raise ValueError("Sütun adları boş olamaz.")
    folder=tempfile.TemporaryDirectory(prefix="analytics_")
    path=str(Path(folder.name)/"data.db")
    with sqlite3.connect(path) as conn: frame.to_sql("dataset",conn,index=False)
    conn.close()
    return {"name":name,"path":path,"frame":frame,"storage":folder,"id":hashlib.sha256(raw).hexdigest(),
            "schema": {str(c):str(t) for c,t in frame.dtypes.items()}}
