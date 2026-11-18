"""Sorgu sonucunu değiştirmeden uygun grafikler hazırlar."""

import re

import altair as alt
import pandas as pd


def build_charts(rows: list[dict]) -> list[tuple[str, alt.Chart]]:
    if len(rows) < 2:
        return []
    frame = pd.DataFrame(rows)
    numeric = [c for c in frame.select_dtypes(include="number").columns
               if not re.search(r"(^id$|id$|kimlik|yıl|year)", c, re.I)]
    dimensions = [c for c in frame.columns if c not in frame.select_dtypes(include="number").columns]
    dates = []
    for col in frame.columns:
        values = frame[col].dropna().astype(str)
        if len(values) and values.str.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?").all():
            parsed = pd.to_datetime(frame[col], format="mixed", errors="coerce")
            if parsed.notna().sum() == frame[col].notna().sum():
                dates.append(col)
                frame[col] = parsed
    if not numeric or not (dates or dimensions):
        return []
    x = dates[0] if dates else dimensions[0]
    temporal = x in dates
    groups = [c for c in dimensions if c != x and c not in dates]
    # Kimlik/ad gibi yüksek çeşitlilikteki alanlarla yüzlerce seri çizme.
    group = groups[0] if groups and frame[groups[0]].nunique() <= 12 else None
    keys = [x] + ([group] if group else [])
    # Yinelenen eksen değerlerini örtük olarak toplamayız/ortalamasını almayız.
    if frame.duplicated(keys).any() or frame[x].nunique() < 2:
        return []
    if not temporal and frame[x].nunique() > 30:
        return []
    charts = []
    for metric in numeric:
        data = frame[keys + [metric]].dropna(subset=[x, metric]).copy()
        data = data[data[metric].map(lambda value: float('-inf') < value < float('inf'))]
        if len(data) < 2:
            continue
        # Alan adında nokta/köşeli parantez olsa da Altair alan yollarına dönüşmesin.
        data.columns = ['axis'] + (['series'] if group else []) + ['value']
        chart = alt.Chart(data)
        chart = chart.mark_line(point=True, color="#7938DB", strokeWidth=3) if temporal else chart.mark_bar(color="#9670D7", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        encoding = dict(
            x=alt.X('axis:T' if temporal else 'axis:N', title=x, sort='ascending' if temporal else None),
            y=alt.Y('value:Q', title=metric),
            tooltip=[alt.Tooltip('axis:T' if temporal else 'axis:N', title=x),
                     alt.Tooltip('value:Q', title=metric, format=',.2f')],
        )
        if group:
            encoding['color'] = alt.Color('series:N', title=group, scale=alt.Scale(range=['#7133D5','#B393E4','#45AFA0','#D899C4','#6D8FD1','#E6B969']))
            encoding['tooltip'].append(alt.Tooltip('series:N', title=group))
            if not temporal:
                encoding['xOffset'] = alt.XOffset('series:N')
        charts.append((metric, chart.encode(**encoding).properties(height=280).configure_view(strokeWidth=0).configure_axis(gridColor="#F0EBF5", domain=False, labelColor="#8C7B9B", titleColor="#6F5B82", labelFont="Segoe UI", titleFont="Segoe UI").configure(background="#FFFFFF")))
    return charts
