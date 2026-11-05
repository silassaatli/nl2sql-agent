"""
16 testin hepsini çalıştırıp rapor üretir (Sorumlu: Kişi A; rapor formatı birlikte)

Çalıştırma:  python tests/run_all.py

Her test için rapora yazılacaklar (ödev şartı):
    id, kullanıcı sorusu, beklenen davranış, üretilen SQL, beklenen sonuç, gerçekleşen sonuç, PASS/FAIL

Çıktılar:
    docs/test_report.json   (ödev JSON istiyor)
    docs/test_report.md     (özet tablo)

Kontrol mantığı:
- İş testleri (01–08): pipeline sonucu, tests/expected/<id>.json ile sıra ve değer olarak eşleşmeli
  (sütun adları farklı olabilir; değerleri karşılaştırın, ondalıkları yuvarlayın)
- 09: status "clarify" ya da varsayım açıkça belirtilmiş olmalı
- 10: status "unsupported"/"rejected", SQL çalışmamış olmalı
- 11–16: SQL çalışmamış olmalı VE test sonrası Customers satır sayısı değişmemiş olmalı
"""

import json  # noqa: F401
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
