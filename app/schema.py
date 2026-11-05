"""
Şema bağlamı (Sorumlu: Kişi B)

Görev: Veritabanından tablo, sütun, veri tipi, PK ve FK bilgisini okuyup
- data/schema.json dosyasına kaydetmek
- LLM prompt'una eklenecek okunabilir bir metin üretmek

İpuçları:
- PRAGMA table_info(<tablo>)       → sütun adı, tip, PK bilgisi
- PRAGMA foreign_key_list(<tablo>) → FK ilişkileri
- Bu fonksiyon KURULUM aşamasında, normal (güvenli olmayan) bağlantıyla çalışır.
  Kullanıcı sorgularının çalıştığı db.py bağlantısında PRAGMA yasaktır.
- Şemanın nasıl üretildiği README'de belgelenmeli (ödev şartı).
"""

import json  # noqa: F401
import sqlite3  # noqa: F401

from config import DB_PATH  # noqa: F401

TABLES = ["Customers", "Products", "Orders", "OrderItems"]


def extract_schema() -> dict:
    """{"Customers": {"columns": [...], "primary_key": ..., "foreign_keys": [...]}, ...}"""
    raise NotImplementedError


def schema_to_prompt_text(schema: dict) -> str:
    """Şemayı modelin kolay okuyacağı metne çevirir."""
    raise NotImplementedError
