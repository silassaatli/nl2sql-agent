"""Uygulamanın tüm sabit ayarları. Sistem saatine bağlı hiçbir değer burada (veya başka yerde) kullanılmaz."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Veritabanı
DB_PATH = os.path.join(BASE_DIR, "data", "nl2sql.db")
ALLOWED_TABLES = {"customers", "products", "orders", "orderitems"}

# Güvenlik ve limitler
MAX_ROWS = 500        # sonuç satır limiti
TIMEOUT_S = 5         # sorgu süre sınırı (saniye)
MAX_RETRIES = 1       # hata olursa en fazla 1 kez yeniden deneme

# DENEYSEL self-correction (varsayılan KAPALI). Kapalıyken yukarıdaki MAX_RETRIES (ödev kuralı: en fazla 1)
# ve bugünkü davranış geçerlidir. Açıkken (app/pipeline.py):
#   - en fazla SELF_CORRECTION_MAX_RETRIES düzeltme denemesi (ödevdeki 1 sınırını aşar, bu yüzden deneysel),
#   - parse_error / unknown_field'a ek olarak database_error ve BOŞ SONUÇ da düzeltme tetikler,
#   - her deneme log kaydına ve ask() sonucuna "attempts" listesi olarak yazılır.
# Güvenlik reddi ve zaman aşımı hiçbir durumda yeniden denenmez.
SELF_CORRECTION = False
SELF_CORRECTION_MAX_RETRIES = 2

# Referans tarih: tüm göreli tarih ifadeleri buna göre yorumlanır
REFERENCE_DATE = "2026-06-30"
DATE_RANGES = {
    "son 6 ay":       ("2026-01-01", "2026-06-30"),
    "geçen çeyrek":   ("2026-01-01", "2026-03-31"),
    "son 30 gün":     ("2026-06-01", "2026-06-30"),
    "son 90 gün":     ("2026-04-02", "2026-06-30"),   # aktif müşteri tanımı
}

# LLM
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite").strip() or "gemini-3.5-flash-lite"

# Log
LOG_PATH = os.path.join(BASE_DIR, "logs", "queries.jsonl")
