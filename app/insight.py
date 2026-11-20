"""
Sonuçtan içgörü (config.INSIGHTS; app/ui.py gösterir). KURAL TABANLI: model çağrısı yok.

Her cümledeki her sayı yalnızca dönen satırlardan hesaplanır; bu yüzden uydurma rakam üretilemez.
İki durum:
- Zaman serisi (etiket sütunu 'YYYY-MM' veya 'YYYY-MM-DD'): ilk → son dönem değişimi, en yüksek / en düşük
  dönem, en büyük dönemden döneme değişim.
- Kategorik (etiket + sayı): en yüksek ve en düşük grup, en yüksek grubun toplam içindeki payı.
Tek hücrelik sonuçta veya sayı sütunu yoksa yorum üretilmez ([] döner).
"""

import re

DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
ID_RE = re.compile(r"(^id$|id$|kimlik)", re.IGNORECASE)
# Metrik zaten bir oran/yüzde ise "yüzdenin yüzde değişimi" veya "payların payı" anlamsızdır: yalnızca en yüksek/düşük.
RATIO_RE = re.compile(r"(yuzde|yüzde|pay|oran|degisim|değişim|percent|ratio|share|%)", re.IGNORECASE)
MAX_SENTENCES = 3
MAX_GROUPS_FOR_SHARE = 20   # 200 müşterilik listede "birincinin payı %1,5" bilgi vermez


def fmt(value: float) -> str:
    """Türkçe sayı biçimi: 1234567.891 → '1.234.567,89'; tam sayı → '1.234'."""
    if float(value).is_integer():
        return f"{int(value):,}".replace(",", ".")
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float) -> str:
    return f"%{value:.1f}".replace(".", ",")


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _columns(rows: list[dict]) -> tuple[str | None, str | None]:
    """(etiket sütunu, metrik sütunu). Metrik: kimlik olmayan ilk sayısal sütun; etiket: ilk sayısal olmayan."""
    cols = list(rows[0])
    numeric = [c for c in cols if all(_is_number(r[c]) or r[c] is None for r in rows)
               and any(_is_number(r[c]) for r in rows) and not ID_RE.search(c)]
    labels = [c for c in cols if c not in numeric and not ID_RE.search(c)]
    return (labels[0] if labels else None), (numeric[-1] if numeric else None)


def generate_insights(rows: list[dict]) -> list[str]:
    if not rows or len(rows) < 2:
        return []
    label, metric = _columns(rows)
    if not label or not metric:
        return []
    data = [(str(r[label]), float(r[metric])) for r in rows if _is_number(r[metric])]
    if len(data) < 2:
        return []

    if RATIO_RE.search(metric):
        high, low = max(data, key=lambda x: x[1]), min(data, key=lambda x: x[1])
        return [f"{metric} en yüksek {high[0]} ({fmt(high[1])}), en düşük {low[0]} ({fmt(low[1])})."]
    if all(DATE_RE.match(name) for name, _ in data):
        return _time_series(sorted(data), metric)[:MAX_SENTENCES]
    return _categorical(data, metric)[:MAX_SENTENCES]


def _time_series(data: list[tuple[str, float]], metric: str) -> list[str]:
    out = []
    (first_name, first), (last_name, last) = data[0], data[-1]
    if first:
        change = (last - first) / abs(first) * 100
        direction = "arttı" if change > 0 else "azaldı" if change < 0 else "değişmedi"
        out.append(f"{metric}, {first_name} döneminden {last_name} dönemine {pct(abs(change))} {direction} "
                   f"({fmt(first)} → {fmt(last)}).")
    high, low = max(data, key=lambda x: x[1]), min(data, key=lambda x: x[1])
    out.append(f"En yüksek değer {high[0]} ({fmt(high[1])}), en düşük değer {low[0]} ({fmt(low[1])}).")
    steps = [(data[i][0], data[i - 1][1], data[i][1]) for i in range(1, len(data)) if data[i - 1][1]]
    if steps:
        name, prev, cur = max(steps, key=lambda s: abs(s[2] - s[1]) / abs(s[1]))
        change = (cur - prev) / abs(prev) * 100
        word = "artış" if change > 0 else "düşüş"
        out.append(f"Dönemden döneme en büyük değişim {name} döneminde: {pct(abs(change))} {word}.")
    return out


def _categorical(data: list[tuple[str, float]], metric: str) -> list[str]:
    ranked = sorted(data, key=lambda x: x[1], reverse=True)
    (top_name, top), (bottom_name, bottom) = ranked[0], ranked[-1]
    out = [f"{metric} en yüksek {top_name} ({fmt(top)}), en düşük {bottom_name} ({fmt(bottom)})."]
    total = sum(v for _, v in data)
    if all(v >= 0 for _, v in data) and total > 0 and 2 < len(data) <= MAX_GROUPS_FOR_SHARE:
        out.append(f"{top_name} grubunun toplam içindeki payı {pct(top / total * 100)} ({len(data)} grup).")
    if bottom > 0 and top / bottom >= 2:
        ratio = f"{top / bottom:.1f}".replace(".", ",")
        out.append(f"En yüksek değer, en düşük değerin yaklaşık {ratio} katı.")
    return out
