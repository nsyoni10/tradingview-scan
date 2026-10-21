"""
ticker_report.py — דוח אקסל לרשימת טיקרים (לונג בלבד): ציון, ATR, ADX, זיהוי נר אחרון, תמיכה/התנגדות.

קלט: קובץ JSON עם נתוני TradingView לכל טיקר (נמשך דרך TradingView MCP):
  {"date": "YYYY-MM-DD", "tickers": {"NASDAQ:XXX": {
      "prev": [o,h,l,c], "last": [o,h,l,c],          # שני הנרות היומיים האחרונים
      "ATR","ADX","DIp","DIm","RSI","EMA20","EMA50",  # יומי
      "PP","R1","R2","S1","S2",                       # Pivot חודשי קלאסי
      "H1M","L1M","H3M","L3M","vol10"}}}

שימוש:  python3 ticker_report.py data.json out.xlsx
"""
import json
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

BODY_RATIO_STRONG = 2 / 3   # גוף ≥ 2/3 מטווח הנר
LEVEL_MERGE_ATR = 0.25      # רמות קרובות מ-0.25 ATR מאוחדות


# ── מגמה ──────────────────────────────────────────────────────────────
def trend(d):
    c, e20, e50 = d["last"][3], d["EMA20"], d["EMA50"]
    if c > e20 > e50 and d["DIp"] > d["DIm"]:
        return "UP"
    if c < e20 < e50 and d["DIm"] > d["DIp"]:
        return "DOWN"
    return "MIXED"


# ── זיהוי נר (מנקודת מבט של לונג) ─────────────────────────────────────
def candle(d, tr):
    o, h, l, c = d["last"]
    po, ph, pl, pc = d["prev"]
    rng = max(h - l, 1e-9)
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l
    green = c > o
    red = c < o
    prev_green = pc > po
    prev_red = pc < po

    tags = []
    pts = 10  # בסיס; טווח סופי 0-25

    # פטיש / איש תלוי: צל תחתון ≥ 2×גוף, צל עליון קטן
    if lower >= 2 * body and upper <= 0.3 * rng and body > 0:
        if tr == "UP":
            tags.append("איש תלוי (Hanging Man)")
            pts -= 8
        else:
            tags.append("פטיש (Hammer)")
            pts += 10
    # פטיש הפוך / כוכב נופל: צל עליון ≥ 2×גוף
    elif upper >= 2 * body and lower <= 0.3 * rng and body > 0:
        if tr == "UP":
            tags.append("כוכב נופל (Shooting Star)")
            pts -= 8
        else:
            tags.append("פטיש הפוך (Inverted Hammer)")
            pts += 4

    # נר ירוק 2/3 אחרי נר אדום (חזרה ללונג)
    strong = body / rng >= BODY_RATIO_STRONG
    if strong and green and prev_red:
        tags.append("נר 2/3 ירוק אחרי אדום ▲")
        pts += 15 if tr == "UP" else 8
    elif strong:
        tags.append("נר גוף מלא " + ("ירוק" if green else "אדום"))
        pts += 3 if green else -5

    # בולעני
    if green and prev_red and o <= pc and c >= po:
        tags.append("בולעני עולה")
        pts += 10
    if red and prev_green and o >= pc and c <= po:
        tags.append("בולעני יורד")
        pts -= 10

    if body / rng < 0.1:
        tags.append("דוג'י")
    elif red and not any("פטיש" in t for t in tags):
        if not tags:
            tags.append("נר אדום")
        pts -= 5
    elif green:
        pts += 3

    color = "ירוק" if green else ("אדום" if red else "ניטרלי")
    return {
        "color": color,
        "tags": ", ".join(tags) if tags else "—",
        "body_pct": body / rng,
        "pts": max(min(pts, 25), 0),
    }


# ── תמיכה / התנגדות ───────────────────────────────────────────────────
def levels(d):
    _, h, l, c = d["last"]
    _, ph, pl, _ = d["prev"]
    raw = [
        (d["PP"], "Pivot M"), (d["R1"], "R1 M"), (d["R2"], "R2 M"),
        (d["S1"], "S1 M"), (d["S2"], "S2 M"),
        (d["H1M"], "שיא חודש"), (d["L1M"], "שפל חודש"),
        (d["H3M"], "שיא 3ח'"), (d["L3M"], "שפל 3ח'"),
        (d["EMA20"], "EMA20"), (d["EMA50"], "EMA50"),
        (h, "גבוה אחרון"), (l, "נמוך אחרון"),
        (ph, "גבוה קודם"), (pl, "נמוך קודם"),
    ]
    raw.sort()
    merged = []
    tol = LEVEL_MERGE_ATR * d["ATR"]
    for price, name in raw:
        if merged and price - merged[-1][0][-1] <= tol:
            merged[-1][0].append(price)
            merged[-1][1].append(name)
        else:
            merged.append(([price], [name]))
    lv = [(sum(p) / len(p), "+".join(n), len(n)) for p, n in merged]
    res = [x for x in lv if x[0] > c * 1.001][:2]
    sup = [x for x in lv if x[0] < c * 0.999][::-1][:2]
    return res, sup


# ── ציון לונג 0-100 ───────────────────────────────────────────────────
def score(d, tr, cd, res, sup):
    pts = {}
    c, e20, e50 = d["last"][3], d["EMA20"], d["EMA50"]
    adx, dip, dim = d["ADX"], d["DIp"], d["DIm"]

    # מבנה מגמה (25)
    pts["EMA"] = (10 if c > e20 else 0) + (10 if e20 > e50 else 0) + (5 if c > e50 else 0)

    # ADX בכיוון הלונג (20)
    if dip > dim:
        pts["ADX"] = 20 if adx >= 25 else 14 if adx >= 20 else 6
    else:
        pts["ADX"] = 0 if adx >= 25 else 4

    # עליונות +DI (10)
    pts["DI"] = max(min((dip - dim) / 20 * 10, 10), 0)

    # נר אחרון (25)
    pts["נר"] = cd["pts"]

    # RSI (10)
    rsi = d["RSI"]
    pts["RSI"] = 10 if 45 <= rsi <= 68 else 5 if 35 <= rsi < 45 or 68 < rsi <= 75 else 0

    # מרחב עד ההתנגדות הקרובה (10)
    room = (res[0][0] - c) / d["ATR"] if res else 3
    pts["מרחב"] = 10 if room >= 1.5 else 5 if room >= 0.75 else 0

    return round(sum(pts.values())), room


def build(data, out):
    wb = Workbook()
    ws = wb.active
    ws.title = "דוח"
    ws.sheet_view.rightToLeft = True

    headers = [
        "טיקר", "ציון לונג", "מגמה", "סגירה", "שינוי %", "ATR", "ATR %", "ADX", "+DI", "-DI",
        "RSI", "EMA20", "EMA50", "צבע נר", "גוף/טווח", "דפוס נר",
        "התנגדות 1", "מקור R1", "מרחק R1 (ATR)", "התנגדות 2", "מקור R2",
        "תמיכה 1", "מקור S1", "מרחק S1 (ATR)", "תמיכה 2", "מקור S2",
        "מרחב להתנגדות (ATR)", "נפח ממוצע 10י", "הערות",
    ]
    ws.append(headers)

    rows = []
    for sym, d in data["tickers"].items():
        tr = trend(d)
        cd = candle(d, tr)
        res, sup = levels(d)
        sc, room = score(d, tr, cd, res, sup)
        c = d["last"][3]
        pc = d["prev"][3]
        notes = []
        if d["ATR"] / c < 0.005:
            notes.append("תנודתיות כמעט אפסית — מחיר 'קפוא' (ייתכן מיזוג/רכישה). לא לסחור טכנית")
            sc = 0
        if tr == "DOWN":
            notes.append("מגמת ירידה — לונג נגד המגמה")
        if d["RSI"] < 30:
            notes.append("RSI מכור-יתר — פוטנציאל לתיקון כלפי מעלה")
        if d["RSI"] > 70 and tr == "UP":
            notes.append("RSI קנוי-יתר")

        def lvl(lst, i):
            return (lst[i][0], lst[i][1]) if len(lst) > i else (None, "")

        r1, r1n = lvl(res, 0)
        r2, r2n = lvl(res, 1)
        s1, s1n = lvl(sup, 0)
        s2, s2n = lvl(sup, 1)
        rows.append([
            sym.split(":")[1], sc,
            {"UP": "עולה ▲", "DOWN": "יורדת ▼", "MIXED": "מעורבת"}[tr],
            c, (c / pc - 1) * 100, d["ATR"], d["ATR"] / c * 100,
            d["ADX"], d["DIp"], d["DIm"], d["RSI"], d["EMA20"], d["EMA50"],
            cd["color"], cd["body_pct"], cd["tags"],
            r1, r1n, (r1 - c) / d["ATR"] if r1 else None, r2, r2n,
            s1, s1n, (c - s1) / d["ATR"] if s1 else None, s2, s2n,
            room, d["vol10"], "; ".join(notes),
        ])

    rows.sort(key=lambda r: -r[1])
    for r in rows:
        ws.append(r)

    # עיצוב
    hdr_fill = PatternFill("solid", fgColor="1F3864")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = hdr_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "C2"

    fmt = {
        4: "0.00", 5: "+0.00;-0.00", 6: "0.00", 7: "0.0", 8: "0.0", 9: "0.0", 10: "0.0",
        11: "0.0", 12: "0.00", 13: "0.00", 15: "0%", 17: "0.00", 19: "0.0", 20: "0.00",
        22: "0.00", 24: "0.0", 25: "0.00", 27: "0.0", 28: "#,##0",
    }
    green, red = PatternFill("solid", fgColor="C6EFCE"), PatternFill("solid", fgColor="FFC7CE")
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if cell.column in fmt:
                cell.number_format = fmt[cell.column]
        row[0].font = Font(bold=True)
        row[1].font = Font(bold=True, size=12)
        row[2].fill = green if "עולה" in row[2].value else red if "יורדת" in row[2].value else PatternFill()
        row[13].fill = green if row[13].value == "ירוק" else red if row[13].value == "אדום" else PatternFill()
        row[15].alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
        row[28].alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)

    last = ws.max_row
    ws.conditional_formatting.add(
        f"B2:B{last}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))
    ws.conditional_formatting.add(
        f"H2:H{last}",
        ColorScaleRule(start_type="num", start_value=15, start_color="FFFFFF",
                       end_type="num", end_value=40, end_color="5B9BD5"))

    widths = {1: 8, 2: 7, 3: 9, 16: 30, 18: 16, 21: 16, 23: 16, 26: 16, 29: 45}
    for i in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(i, 11)

    # גיליון הסבר
    ex = wb.create_sheet("הסבר")
    ex.sheet_view.rightToLeft = True
    lines = [
        ("נתונים", f"TradingView, גרף יומי. נר אחרון שנסגר: {data['date']}"),
        ("ATR / ADX", "ATR(14) ו-ADX(14) יומיים. ADX ≥ 25 = מגמה חזקה, 20-25 = מתפתחת, < 20 = אין מגמה"),
        ("מגמה", "עולה: סגירה > EMA20 > EMA50 ו-+DI > -DI. יורדת: ההפך. אחרת: מעורבת"),
        ("פטיש / איש תלוי", "צל תחתון ≥ 2× גוף, צל עליון ≤ 30% מהטווח. אחרי עלייה = איש תלוי, אחרת = פטיש"),
        ("נר 2/3", "נר ירוק שגופו ≥ 2/3 מטווח הנר, אחרי נר אדום. בונוס מלא במגמה עולה"),
        ("תמיכה/התנגדות", "Pivot חודשי (PP/R1/R2/S1/S2), שיא/שפל חודש ו-3 חודשים, EMA20/50, גבוה/נמוך 2 נרות אחרונים. "
                          "רמות במרחק < 0.25 ATR מאוחדות (המקור מראה כמה רמות חופפות — יותר = רמה חזקה יותר)"),
        ("ציון 0-100", "ציון ללונג בלבד: מבנה EMA עד 25 (סגירה>EMA20, EMA20>EMA50, סגירה>EMA50) | ADX עם +DI>-DI עד 20 | "
                       "עליונות +DI עד 10 | נר עד 25 | RSI 45-68 עד 10 | מרחב להתנגדות ≥1.5 ATR עד 10"),
        ("שים לב", "הציון הוא כלי מיון, לא המלצת השקעה"),
    ]
    for k, v in lines:
        ex.append([k, v])
    ex.column_dimensions["A"].width = 20
    ex.column_dimensions["B"].width = 110
    for row in ex.iter_rows():
        row[0].font = Font(bold=True)
        row[1].alignment = Alignment(wrap_text=True, horizontal="right")

    wb.save(out)
    return rows


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        rows = build(json.load(f), dst)
    for r in rows:
        print(f"{r[0]:6} {r[1]:3} {r[2]:8} ADX={r[7]:5.1f} RSI={r[10]:5.1f} | {r[15]} | R1={r[16]} S1={r[21]}")
