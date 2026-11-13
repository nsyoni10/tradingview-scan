"""
checkup.py — סקיל checkup: דוח לונג יומי לרשימת "Red list" מטריידינגוויו.

ציון כניסה ללונג בתחילת מהלך אחרי תיקון: כיוון (DI/ADX), מרובוזו, ווליום, CCI, SMA150.
הפלט הוא xlsx שמועלה ל-Google Drive ומומר ל-Google Sheet בשם "Summary of <date>".

קלט JSON כמו ב-ticker_report.py, ובנוסף לכל טיקר: "SMA150", "RVOL", "CCI", "CCI1", "ADX1" (ערכי אתמול),
בולינגר: "SMA20", "BBU" (יומי) ו-"SMA20W", "BBUW" (שבועי) — בלעדיהם הסטטוס נופל לחוק ה-ATR הישן,
ו-"bars": 12 נרות יומיים אחרונים [o,h,l,c,v] מהישן לחדש — מהם נגזרים prev/last, RVOL (יום אחרון מול 10 שלפניו) ומרובוזו.
שימוש:  python3 checkup.py checkup_data/data_YYYY-MM-DD.json out.xlsx
"""
import csv
import json
import sys

from openpyxl import Workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from ticker_report import candle, levels, trend

RVOL_MIN = 1.2
MARU_BODY = 0.85      # מרובוזו: גוף ≥ 85% מטווח הנר
MARU_MIN_ATR = 0.5    # ...וגוף ≥ 0.5 ATR (נר עם עוצמה, לא נר קטנטן)
MARU_DAYS = 3         # מחפשים מרובוזו ב-3 ימי המסחר האחרונים
OK, BAD = "✅", "❌"


# ── ווליום: יום אחרון מול ממוצע 10 הימים שלפניו (בלי היום עצמו) ────────
def rvol(d):
    bars = d.get("bars")
    if bars and len(bars) >= 11:
        prior = [b[4] for b in bars[-11:-1]]
        return bars[-1][4] / (sum(prior) / len(prior))
    return d["RVOL"]


# ── מרובוזו ירוק ב-N הימים האחרונים ─────────────────────────────────────
def marubozu(d):
    bars = d.get("bars") or [d["prev"] + [0], d["last"] + [0]]
    for ago, (o, h, l, c, _) in enumerate(reversed(bars[-MARU_DAYS:])):
        rng = h - l
        if rng > 0 and c > o and (c - o) / rng >= MARU_BODY and (c - o) >= MARU_MIN_ATR * d["ATR"]:
            return ago
    return None


# ── ציון כניסה ללונג 0-100 (תחילת מהלך אחרי תיקון, דגש על כיוון) ─────────
def score(d, cd, res, rv, maru):
    pts = {}
    c, o = d["last"][3], d["last"][0]
    adx, dip, dim = d["ADX"], d["DIp"], d["DIm"]

    # כיוון (30): +DI מעל -DI, ADX סביב 20 ומעלה, ADX עולה — נספר רק כשהכיוון ללונג
    if dip > dim:
        pts["כיוון"] = 15 + (10 if adx >= 20 else 5 if adx >= 18 else 0) + (5 if adx > d.get("ADX1", adx) else 0)
    else:
        pts["כיוון"] = 0

    # נר עם עוצמה (25): מרובוזו ירוק ב-3 הימים האחרונים + דפוס הנר האחרון
    pts["נר"] = (15 if maru == 0 else 10 if maru is not None else 0) + cd["pts"] * 0.4

    # ווליום (15): רק על נר ירוק — ווליום גבוה על נר אדום הוא מכירה
    if c > o:
        pts["ווליום"] = 15 if rv >= 1.5 else 10 if rv >= RVOL_MIN else 4 if rv >= 1.0 else 0
    else:
        pts["ווליום"] = 0

    # CCI (15): יציאה מתיקון — חוצה למעלה את -100 או את 0, או עולה מתחת ל-100
    cci, cci1 = d["CCI"], d.get("CCI1", d["CCI"])
    if cci > cci1 and ((cci1 < -100 <= cci) or (cci1 < 0 <= cci)):
        pts["CCI"] = 15
    elif cci > cci1 and cci < 100:
        pts["CCI"] = 10
    elif cci > cci1 and cci < 200:
        pts["CCI"] = 4
    else:
        pts["CCI"] = 0

    # מעל SMA150 (10)
    pts["SMA150"] = 10 if c > d["SMA150"] else 0

    # לא מתוח ביומי (5): בתוך רצועת בולינגר היומית (בנתונים ישנים: עד 1.5 ATR מעל EMA20)
    bd = bb_pos(c, d.get("SMA20"), d.get("BBU"))
    pts["לא מתוח"] = 5 if (bd <= BB_MAX if bd is not None else (c - d["EMA20"]) / d["ATR"] <= 1.5) else 0

    room = (res[0][0] - c) / d["ATR"] if res else 3
    return round(sum(pts.values())), room


# ── סטטוס: בולינגר יומי ושבועי + כיוון + ווליום ──────────────────────
STATUS = ["✅ יש מקום", "🔵 כמעט שם", "👁 מעקב", "🔴 מתוחה בשבועי", "⛔ לא לסחור"]
STATUS_FILL = ["C6EFCE", "BDD7EE", "FFEB9C", "FFC7CE", "D9D9D9"]
BB_MAX = 2.0                    # מעל +2σ (מחוץ לרצועה העליונה) = מתוחה
STRETCH_ATR_FALLBACK = 2.0      # לנתונים ישנים בלי בולינגר: מרחק מ-EMA20 ב-ATR
MIN_AVG_VOL = 500_000           # מתחת לממוצע 10 ימים כזה — מניה לא סחירה, לא לסחור


def bb_pos(close, mid, upper):
    """מיקום ברצועת בולינגר ביחידות σ: 0 = על SMA20, +2 = על הרצועה העליונה."""
    if mid is None or upper is None or upper <= mid:
        return None
    return (close - mid) / ((upper - mid) / 2)


def status(d):
    """מחזיר (אינדקס ב-STATUS, בולינגר יומי σ, בולינגר שבועי σ, סיבה)."""
    c = d["last"][3]
    bd = bb_pos(c, d.get("SMA20"), d.get("BBU"))
    bw = bb_pos(c, d.get("SMA20W"), d.get("BBUW"))
    daily_stretched = bd > BB_MAX if bd is not None else (c - d["EMA20"]) / d["ATR"] > STRETCH_ATR_FALLBACK
    weekly_stretched = bw is not None and bw > BB_MAX
    adx, adx1, up = d["ADX"], d.get("ADX1", d["ADX"]), d["DIp"] > d["DIm"]

    if d["vol10"] < MIN_AVG_VOL:
        return 4, bd, bw, f"ווליום נמוך: {d['vol10']:,.0f} מניות ביום בממוצע (מינימום {MIN_AVG_VOL:,})"
    if d["ATR"] / c < 0.005:
        return 4, bd, bw, "מחיר קפוא"
    if not up and adx >= 20:
        return 4, bd, bw, "מגמת ירידה (-DI מעל +DI, ADX ≥ 20)"
    if not up or (adx < 20 and adx <= adx1):
        return 4, bd, bw, "אין עדיין כיוון ללונג"
    if weekly_stretched:
        return 3, bd, bw, "מתוחה בשבועי (מעל הרצועה העליונה השבועית)"
    if daily_stretched:
        return 2, bd, bw, "מתוחה ביומי, טובה בשבועי — להשאיר ברשימה ולבדוק שוב מחר"
    if adx >= 20:
        return 0, bd, bw, "טובה בשבועי וביומי, +DI מעל -DI, ADX ≥ 20"
    return 1, bd, bw, "טובה בשבועי וביומי, +DI מעל -DI, ADX מתחת ל-20 ועולה"


NEWS_RED, NEWS_YELLOW = "⚠", "ℹ"


def news_cell(d):
    """עמודת החדשות: news_level = red / yellow / none, news = טקסט קצר. בלי news_level = לא נבדק."""
    lvl = d.get("news_level")
    if lvl is None:
        return ""
    txt = d.get("news", "").strip()
    if lvl == "red":
        return f"{NEWS_RED} {txt}"
    if lvl == "yellow":
        return f"{NEWS_YELLOW} {txt}"
    return "—"


WEEKLY = "★ שבועי"


def sr_cells(d, c, sup, res):
    """3 רמות מתחת לסגירה ו-3 מעליה — Pivot Points Standard של טריידינגוויו (Traditional, חודשי).
    רמה שגם רמה שבועית יושבת עליה מסומנת ★ ונצבעת. בלי השדות — הרמות הישנות."""
    def cell(x):
        t = f"{x['name']} {x['p']:.2f} ({(x['p'] / c - 1) * 100:+.1f}%)"
        return t + (f" {WEEKLY} ({x['wname']})" if x.get("weekly") else "")
    if d.get("sr_sup") and "name" in d["sr_sup"][0]:
        s3 = [cell(x) for x in d["sr_sup"]]
        r3 = [cell(x) for x in d.get("sr_res", [])]
    else:
        s3 = [f"{x[0]:.2f}" for x in sup[:3]]
        r3 = [f"{x[0]:.2f}" for x in res[:3]]
    pad = lambda l: (l + ["אין"] * 3)[:3]
    return pad(s3) + pad(r3)


def corr_cells(d, c):
    """תיקון: משיא 3 החודשים (תחילת התיקון) לשפל שאחריו. מתחת ל-50% = דיסקאונט."""
    if d.get("corr_mid") is None:
        return [""] * 4
    return [
        "דיסקאונט" if d["zone"] == "discount" else "פרמיום",
        d["corr_mid"], f"{d['corr_hi']:.2f} ({d['corr_hi_date'][8:10]}/{d['corr_hi_date'][5:7]})",
        f"{d['corr_lo']:.2f} ({d['corr_lo_date'][8:10]}/{d['corr_lo_date'][5:7]})",
    ]


def build(data, out):
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.sheet_view.rightToLeft = True

    headers = [
        "טיקר", "סטטוס", "בולינגר יומי (σ)", "בולינגר שבועי (σ)", "ציון כניסה", "חדשות",
        "תמיכה 1", "תמיכה 2", "תמיכה 3", "התנגדות 1", "התנגדות 2", "התנגדות 3",
        "אזור", "קו 50%", "תחילת התיקון", "שפל התיקון",
        "מעל SMA150", "RVOL ≥ 1.2", "כיוון", "סגירה", "שינוי %",
        "SMA150", "RVOL", "ATR", "ATR %", "ADX", "+DI", "-DI", "CCI", "EMA20", "EMA50",
        "צבע נר", "מרובוזו (3 ימים)", "דפוס נר",
        "נפח ממוצע 10י", "הערות",
    ]
    ws.append(headers)

    rows = []
    for sym, d in data["tickers"].items():
        if d.get("bars"):
            d["prev"], d["last"] = d["bars"][-2][:4], d["bars"][-1][:4]
        d["RVOL"] = rvol(d)
        maru = marubozu(d)
        st, bd, bw, st_why = status(d)
        tr = trend(d)
        cd = candle(d, tr)
        res, sup = levels(d)
        sc, room = score(d, cd, res, d["RVOL"], maru)
        c, pc = d["last"][3], d["prev"][3]
        above = c > d["SMA150"]
        rvol_ok = d["RVOL"] >= RVOL_MIN

        notes = []
        if d["ATR"] / c < 0.005:
            notes.append("תנודתיות כמעט אפסית — מחיר 'קפוא'. לא לסחור טכנית")
            sc = 0
        if d["DIm"] > d["DIp"]:
            notes.append("-DI מעל +DI — הכיוון עדיין לא ללונג")
        if d["RVOL"] >= RVOL_MIN and d["last"][3] < d["last"][0]:
            notes.append("ווליום גבוה על נר אדום — מכירה")

        rows.append([
            sym.split(":")[1], STATUS[st], bd, bw, sc, news_cell(d),
            *sr_cells(d, c, sup, res), *corr_cells(d, c),
            OK if above else BAD, OK if rvol_ok else BAD,
            ("▲ +DI" if d["DIp"] > d["DIm"] else "▼ -DI") + f" | ADX {d['ADX']:.0f}" + (" עולה" if d["ADX"] > d.get("ADX1", d["ADX"]) else " יורד"),
            c, (c / pc - 1) * 100, d["SMA150"], d["RVOL"],
            d["ATR"], d["ATR"] / c * 100, d["ADX"], d["DIp"], d["DIm"], d["CCI"],
            d["EMA20"], d["EMA50"], cd["color"],
            "—" if maru is None else ("היום" if maru == 0 else f"לפני {maru} ימים" if maru > 1 else "אתמול"),
            cd["tags"],
            d["vol10"], "; ".join([f"סטטוס: {st_why}"] + notes),
        ])

    rows.sort(key=lambda r: (STATUS.index(r[1]), -r[4]))
    for r in rows:
        ws.append(r)

    # עיצוב
    hdr_fill = PatternFill("solid", fgColor="1F3864")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = hdr_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "F2"
    H = {h: i for i, h in enumerate(headers)}

    fmt = {h: "+0.00;-0.00" for h in ("בולינגר יומי (σ)", "בולינגר שבועי (σ)", "שינוי %")}
    fmt.update({h: "0.00" for h in ("סגירה", "SMA150", "RVOL", "ATR", "EMA20", "EMA50", "קו 50%")})
    fmt.update({h: "0.0" for h in ("ATR %", "ADX", "+DI", "-DI", )})
    fmt.update({"CCI": "0", "נפח ממוצע 10י": "#,##0"})
    fmt = {H[h] + 1: f for h, f in fmt.items()}
    green, red = PatternFill("solid", fgColor="C6EFCE"), PatternFill("solid", fgColor="FFC7CE")
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(horizontal="center", vertical="center")
            if cell.column in fmt:
                cell.number_format = fmt[cell.column]
        st_fill = PatternFill("solid", fgColor=STATUS_FILL[STATUS.index(row[H["סטטוס"]].value)])
        for h in ("טיקר", "סטטוס", "בולינגר יומי (σ)", "בולינגר שבועי (σ)"):
            row[H[h]].fill = st_fill
        row[H["טיקר"]].font = Font(bold=True)
        row[H["סטטוס"]].font = Font(bold=True)
        row[H["ציון כניסה"]].font = Font(bold=True, size=12)
        for h in ("מעל SMA150", "RVOL ≥ 1.2"):
            row[H[h]].fill = green if row[H[h]].value == OK else red
        row[H["כיוון"]].fill = green if "▲" in row[H["כיוון"]].value else red
        row[H["מרובוזו (3 ימים)"]].fill = green if row[H["מרובוזו (3 ימים)"]].value != "—" else PatternFill()
        v = row[H["צבע נר"]].value
        row[H["צבע נר"]].fill = green if v == "ירוק" else red if v == "אדום" else PatternFill()
        nv = row[H["חדשות"]].value or ""
        if nv.startswith(NEWS_RED):
            row[H["חדשות"]].fill = red
        elif nv.startswith(NEWS_YELLOW):
            row[H["חדשות"]].fill = PatternFill("solid", fgColor="FFEB9C")
        z = row[H["אזור"]].value
        row[H["אזור"]].fill = green if z == "דיסקאונט" else red if z == "פרמיום" else PatternFill()
        wk_fill = PatternFill("solid", fgColor="BDD7EE")
        for h in ("תמיכה 1", "תמיכה 2", "תמיכה 3", "התנגדות 1", "התנגדות 2", "התנגדות 3"):
            if WEEKLY in str(row[H[h]].value):
                row[H[h]].fill = wk_fill
                row[H[h]].font = Font(bold=True)
        for h in ("דפוס נר", "חדשות", "הערות"):
            row[H[h]].alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)

    last = ws.max_row
    ws.conditional_formatting.add(
        f"{get_column_letter(H['ציון כניסה'] + 1)}2:{get_column_letter(H['ציון כניסה'] + 1)}{last}",
        ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                       mid_type="num", mid_value=50, mid_color="FFEB84",
                       end_type="num", end_value=100, end_color="63BE7B"))

    widths = {"טיקר": 8, "סטטוס": 16, "בולינגר יומי (σ)": 11, "בולינגר שבועי (σ)": 11, "ציון כניסה": 9,
              "חדשות": 45, **{h: 22 for h in ("תמיכה 1", "תמיכה 2", "תמיכה 3", "התנגדות 1", "התנגדות 2", "התנגדות 3")}, "תחילת התיקון": 15, "שפל התיקון": 15, "כיוון": 16, "מרובוזו (3 ימים)": 12, "דפוס נר": 30, "הערות": 50}
    widths = {H[h] + 1: w for h, w in widths.items()}
    for i in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(i, 10)

    # גיליון הסבר
    ex = wb.create_sheet("הסבר")
    ex.sheet_view.rightToLeft = True
    lines = [
        ("מקור", f"רשימת המעקב '{data.get('watchlist', 'Red list')}', נתונים מ-{'Yahoo Finance (אינדיקטורים מחושבים)' if data.get('source') == 'yahoo' else 'טריידינגוויו'}, גרף יומי. נר אחרון: {data.get('bar_date', data['date'])}"),
        ("סטטוס", "✅ יש מקום: טובה בשבועי וביומי (בתוך רצועת בולינגר), +DI מעל -DI, ADX ≥ 20 | "
                   "🔵 כמעט שם: כמו ✅ אבל ADX מתחת ל-20 ועולה | "
                   "👁 מעקב: טובה בשבועי, מתוחה ביומי — להשאיר ב-Red list ולבדוק שוב מחר עד שתבשיל | "
                   "🔴 מתוחה בשבועי: מעל הרצועה העליונה השבועית | "
                   "⛔ לא לסחור: ווליום ממוצע מתחת ל-500,000 מניות ביום, מחיר קפוא, מגמת ירידה, או אין כיוון ללונג"),
        ("בולינגר (σ)", "מיקום המחיר ברצועת בולינגר (SMA20, ±2 סטיות תקן) ביומי ובשבועי: 0 = על הממוצע, "
                        "+2 = על הרצועה העליונה, מעל +2 = מתוחה"),
        ("מעל SMA150", "סגירה מעל הממוצע הנע הפשוט של 150 ימים = ✅"),
        ("RVOL ≥ 1.2", "ווליום יום המסחר האחרון שנסגר חלקי ממוצע 10 הימים שלפניו (בלי היום עצמו), מחושב מהנרות. "
                       "1.2 ומעלה = ✅. בלי פרה/אפטר-מרקט"),
        ("כיוון", "+DI מול -DI, ערך ADX(14), והאם ADX עלה מאתמול. ADX סביב 20 ומעלה עם +DI למעלה = כיוון לונג"),
        ("CCI", "CCI(20) יומי. מחפשים יציאה מתיקון: CCI עולה, חוצה למעלה את -100 או את 0"),
        ("מרובוזו", "נר ירוק עם גוף ≥ 85% מהטווח וגוף ≥ 0.5 ATR, באחד מ-3 ימי המסחר האחרונים"),
        ("פטיש / איש תלוי", "צל תחתון ≥ 2× גוף, צל עליון ≤ 30% מהטווח. במגמה עולה = איש תלוי, אחרת = פטיש"),
        ("נר 2/3", "נר ירוק שגופו ≥ 2/3 מטווח הנר, אחרי נר אדום"),
        ("תמיכה/התנגדות 1-3", "בדיוק האינדיקטור Pivot Points Standard של טריידינגוויו בהגדרות ברירת המחדל: Type = Traditional, "
                              "Pivots Timeframe = Auto (בגרף יומי = חודשי). הרמות של החודש הנוכחי מחושבות מהשיא, השפל והסגירה של החודש הקודם: "
                              "P = (H+L+C)/3, R1 = 2P−L, S1 = 2P−H, R2 = P+(H−L), S2 = P−(H−L), R3 = 2P+(H−2L), S3 = 2P−(2H−L), "
                              "R4 = 3P+(H−3L), S4 = 3P−(3H−L), R5 = 4P+(H−4L), S5 = 4P−(4H−L). "
                              "בגיליון: 3 הרמות הקרובות מתחת לסגירה ו-3 מעליה, לפי הסדר. "
                              "★ שבועי (רקע כחול) = אותו אינדיקטור עם Pivots Timeframe = 1W נותן רמה במרחק עד 0.25 ATR (בסוגריים: איזו רמה שבועית)"),
        ("תיקון ודיסקאונט", "תחילת התיקון = השיא הגבוה ב-3 החודשים האחרונים. שפל התיקון = הנמוך ביותר מאז. "
                            "קו 50% = אמצע הטווח. סגירה מתחת לקו = דיסקאונט (ירוק), מעליו = פרמיום (אדום). "
                            "זה קירוב אוטומטי: אם התיקון האמיתי התחיל לפני יותר מ-3 חודשים, צריך לבדוק בגרף"),
        ("שים לב", "הציון הוא כלי מיון, לא המלצת השקעה"),
    ]
    for k, v in lines:
        ex.append([k, v])
    ex.column_dimensions["A"].width = 18
    ex.column_dimensions["B"].width = 110
    for row in ex.iter_rows():
        row[0].font = Font(bold=True)
        row[1].alignment = Alignment(wrap_text=True, horizontal="right")

    wb.save(out)
    write_csv(headers, rows, out.rsplit(".", 1)[0] + ".csv")
    return rows


def write_csv(headers, rows, path):
    """CSV להעלאה ל-Google Drive (מומר אוטומטית ל-Google Sheet)."""
    def fmt(v):
        if isinstance(v, float):
            return round(v, 2)
        return "" if v is None else v

    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow([fmt(v) for v in r])


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        rows = build(json.load(f), dst)
    for r in rows:
        f = lambda v: "  —  " if v is None else f"{v:+5.2f}"
        print(f"{r[0]:6} {r[1]:16} יומי {f(r[2])} שבועי {f(r[3])} ציון {r[4]:3} | {r[-1]}")
