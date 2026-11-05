"""
Semantik katman (Sorumlu: Kişi B) — ödevdeki bonus madde: "semantik katman, metrik sözlüğü"

İş dilindeki ifadeleri (ör. "ciro", "geçen çeyrek", "Haziranda") veritabanı karşılıklarına KODLA çevirir.
Model bu çeviriyi tahmin etmez; hazır sonucu prompt'ta veya soruya eklenen notta görür.

1. METRICS: metrik sözlüğü (ad, eş anlamlılar, SQL ifadesi, not) → prompt'un metrik bölümü buradan üretilir.
2. resolve_dates(): sorudaki tarih ifadelerini (config.DATE_RANGES ifadeleri, ay adları, çeyrekler, "ilk N ay",
   "X'ten Y'ye" aralıkları) bulup tarih aralığına çevirir. date_note() bunu soruya eklenecek nota dönüştürür.
   Hesap yalnızca config.REFERENCE_DATE üzerinden yapılır; sistem saati KULLANILMAZ.
"""

import calendar
import re
from datetime import date

from config import DATE_RANGES, REFERENCE_DATE

REF = date.fromisoformat(REFERENCE_DATE)

# --- 1. Metrik sözlüğü -------------------------------------------------------
_ACTIVE_START, _ACTIVE_END = DATE_RANGES["son 90 gün"]

# "match": soruda bu kökler geçerse metric_note() formülü soruya not olarak ekler (model kuralı atlamasın diye).
METRICS = [
    {
        "name": "Ciro",
        "synonyms": ["gelir", "en çok satan", "en çok satılan"],
        "match": ["en çok sat"],
        "sql": "SUM(oi.Quantity * oi.UnitPrice)",
        "note": "OrderItems üzerinden. Products.Price liste fiyatıdır, ciro için KULLANILMAZ. "
                "\"En çok satan / satılan\" adete (SUM(Quantity)) göre değil ciroya göre sıralanır.",
    },
    {
        "name": "Sipariş adedi",
        "synonyms": ["sipariş sayısı"],
        "match": [],
        "sql": "COUNT(DISTINCT o.OrderID)",
        "note": "OrderItems ile birleştirince satırlar çoğaldığı için COUNT(*) kullanılmaz.",
    },
    {
        "name": "Aktif müşteri",
        "synonyms": [],
        "match": [],
        "sql": "COUNT(DISTINCT o.CustomerID)",
        "note": f"'{_ACTIVE_START}' ile '{_ACTIVE_END}' arasında en az bir siparişi olan müşteri.",
    },
    {
        "name": "Ortalama sipariş kalemi tutarı",
        "synonyms": ["kategori ortalaması", "satır tutarı", "kalem tutarı", "satış kalemi tutarı", "işlem tutarı"],
        "match": ["kalem", "satır tutar", "işlem tutar"],
        "sql": "AVG(oi.Quantity * oi.UnitPrice)",
        "note": "Bir OrderItems satırının tutarının ortalaması. Ortalama birim fiyat (AVG(UnitPrice)) DEĞİLDİR.",
    },
]


def metrics_to_prompt_text() -> str:
    """Metrik sözlüğünü prompt satırlarına çevirir."""
    lines = []
    for m in METRICS:
        syn = f" (eş anlamlılar: {', '.join(repr(s) for s in m['synonyms'])})" if m["synonyms"] else ""
        lines.append(f"- {m['name']}{syn} = {m['sql']}. {m['note']}")
    return "\n".join(lines)


# --- 2. Tarih çözücü ---------------------------------------------------------
MONTHS_TR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
NUMBERS_TR = {"bir": 1, "iki": 2, "üç": 3, "dört": 4, "beş": 5, "altı": 6}


def _tr_lower(text: str) -> str:
    """Türkçe küçük harf: 'İ'.lower() Python'da 'i̇' (noktalı) olur, önce elle çevrilir."""
    return text.replace("İ", "i").replace("I", "ı").lower()


_MONTHS_LOWER = [_tr_lower(m) for m in MONTHS_TR]
_MONTH_RE = re.compile(r"(?<!\w)(" + "|".join(_MONTHS_LOWER) + r")")
_YEAR_RE = re.compile(r"(?<!\d)(20\d\d)(?!\d)")
_RANGE_HINT_RE = re.compile(r"['’]?(?:dan|den|tan|ten)\s|[–—-]|arası|kadar")
_QUARTER_RE = re.compile(
    r"(?<!\w)(ilk|birinci|1\.|[iı]\.|ikinci|2\.|[iı]{2}\.|üçüncü|3\.|[iı]{3}\.|dördüncü|son|4\.|[iı]v\.)\s*çeyre"
)
_QUARTER_WORDS = {"ilk": 1, "birinci": 1, "1.": 1, "ikinci": 2, "2.": 2, "üçüncü": 3, "3.": 3,
                  "dördüncü": 4, "son": 4, "4.": 4}
_FIRST_N_MONTHS_RE = re.compile(r"ilk\s+(\d|" + "|".join(NUMBERS_TR) + r")\s+ay")


def _month_span(year: int, first: int, last: int) -> tuple[str, str]:
    """first..last aylarını kapsayan ('YYYY-MM-01', 'YYYY-MM-son gün')."""
    last_day = calendar.monthrange(year, last)[1]
    return f"{year}-{first:02d}-01", f"{year}-{last:02d}-{last_day:02d}"


def _nearest_year(month: int) -> int:
    """Yılsız ay: referans tarihten geriye en yakın o ay (REF 2026-06 → Ocak..Haziran 2026, Temmuz..Aralık 2025)."""
    return REF.year if month <= REF.month else REF.year - 1


def month_rules_text() -> str:
    """Prompt için: yılsız her ay adının aralığı (ör. '  - Ocak: '2026-01-01' – '2026-01-31'')."""
    lines = []
    for month, name in enumerate(MONTHS_TR, start=1):
        start, end = _month_span(_nearest_year(month), month, month)
        lines.append(f"  - {name}: '{start}' – '{end}'")
    return "\n".join(lines)


def _quarter_number(word: str) -> int:
    word = word.replace("ı", "i")
    if word in _QUARTER_WORDS:
        return _QUARTER_WORDS[word]
    return {"i.": 1, "ii.": 2, "iii.": 3, "iv.": 4}[word]   # Roma rakamı (I. çeyrek)


def resolve_dates(question: str) -> list[dict]:
    """
    Sorudaki tarih ifadelerini aralığa çevirir: [{"phrase", "start", "end"}, ...]
    Hiçbiri yoksa boş liste. Sadece REFERENCE_DATE kullanılır.
    """
    q = _tr_lower(question)
    years = set(_YEAR_RE.findall(q))
    explicit_year = int(years.pop()) if len(years) == 1 else None
    spans = []      # geniş aralıklar (config ifadeleri, çeyrek, ilk N ay, ay aralığı)

    for name, (start, end) in DATE_RANGES.items():
        if _tr_lower(name) in q:
            spans.append({"phrase": name, "start": start, "end": end})

    if "aktif" in q:    # "aktif müşteri" metriği tanımı gereği son 90 günü içerir
        start, end = DATE_RANGES["son 90 gün"]
        if not any(s["start"] == start and s["end"] == end for s in spans):
            spans.append({"phrase": "aktif müşteri (son 90 gün)", "start": start, "end": end})

    for m in _QUARTER_RE.finditer(q):
        word = m.group(1)
        if word == "son" and explicit_year is None:
            continue        # "son çeyrek" yılsız → belirsiz; "geçen çeyrek" config'den gelir
        n = _quarter_number(word)
        first = 3 * (n - 1) + 1
        year = explicit_year or _nearest_year(first)
        start, end = _month_span(year, first, first + 2)
        spans.append({"phrase": f"{year} {n}. çeyrek", "start": start, "end": end})

    for m in _FIRST_N_MONTHS_RE.finditer(q):
        raw = m.group(1)
        n = int(raw) if raw.isdigit() else NUMBERS_TR[raw]
        year = explicit_year or _nearest_year(n)
        start, end = _month_span(year, 1, n)
        spans.append({"phrase": f"{year} ilk {n} ay", "start": start, "end": end})

    months = sorted({_MONTHS_LOWER.index(m) + 1 for m in _MONTH_RE.findall(q)})
    month_spans = []
    for month in months:
        year = explicit_year or _nearest_year(month)
        start, end = _month_span(year, month, month)
        month_spans.append({"phrase": f"{MONTHS_TR[month - 1]} {year}", "start": start, "end": end})

    if len(month_spans) >= 2 and _RANGE_HINT_RE.search(q):
        # "Ocak'tan Haziran'a", "Ocak–Mart": en erken ayın başından en geç ayın sonuna tek aralık
        first, last = min(month_spans, key=lambda s: s["start"]), max(month_spans, key=lambda s: s["end"])
        spans.append({"phrase": f"{first['phrase']} – {last['phrase']}", "start": first["start"], "end": last["end"]})
        month_spans = []

    # Geniş bir aralığın içinde kalan tek ayı at ("Mart sonuna kadarki ilk üç ay" → sadece Ocak–Mart)
    month_spans = [m for m in month_spans
                   if not any(s["start"] <= m["start"] and m["end"] <= s["end"] for s in spans)]
    return spans + month_spans


def date_note(question: str) -> str:
    """resolve_dates() sonucunu soruya eklenecek nota çevirir. Tarih ifadesi yoksa bunu da açıkça söyler
    (yoksa model olmayan bir notu uydurup örneklerdeki tarihleri ekleyebiliyor; ölçüm 09/10, test 06)."""
    spans = resolve_dates(question)
    if not spans:
        return "Tarih notu: soruda tarih ifadesi yok; tarih filtresi (OrderDate) EKLEME, tüm veriyi kullan."
    lines = [f"  - {s['phrase']}: o.OrderDate BETWEEN '{s['start']}' AND '{s['end']}'" for s in spans]
    return ("Tarih notu (sistem tarafından referans tarih " + REFERENCE_DATE
            + " üzerinden hesaplandı; bu aralıkları aynen kullan):\n" + "\n".join(lines))


def metric_note(question: str) -> str:
    """Soruda riskli bir eş anlamlı geçiyorsa (METRICS[*]["match"]) formülü not olarak döndürür; yoksa ""."""
    q = _tr_lower(question)
    lines = [f"  - {m['name']} = {m['sql']}. {m['note']}"
             for m in METRICS if any(stem in q for stem in m["match"])]
    return ("Metrik notu (sistem tarafından eşleştirildi; bu formülü kullan):\n" + "\n".join(lines)) if lines else ""
