"""
portfolio.py — builds the "Portfolio – YYYY-MM-DD" sheet that the PROTFOLIO page reads.

The page computes nothing: every value it shows is a column here.

Input:
  TV_BATCH  JSON of mcp-tv-get-symbol-data-batch "data" for every symbol in the list
  ORDER     JSON list: the PROTFOLIO watchlist as TradingView returns it (with ### group rows)
  DATE      the bar date (last closed regular session), YYYY-MM-DD
  TV_BARS   optional JSON {symbol: mcp-tv-get-ohlcv "bars" (columns, 12 daily)} — TradingView candles for symbols
            where Yahoo's last bar does not match the TradingView close; they replace Yahoo's last 12 days

Daily candles (last 12, for candle / marubozu / RVOL) and the Pivot Points Standard levels,
weekly mark and correction come from Yahoo (yahoo_data.py) — checked against the TradingView close.
Status, score, near levels and the trade plan come from checkup.py, unchanged.

Usage:  python3 portfolio.py TV_BATCH ORDER DATE OUT_BASENAME [TV_BARS]
Writes OUT_BASENAME.csv and OUT_BASENAME.xlsx (and OUT_BASENAME.json with the inputs).
"""
import csv
import datetime as dt
import json
import os
import sys
import tempfile

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

import checkup
from yahoo_data import correction, daily_weekly, groups, sr_levels

INDEX_GROUP = "מדדים"

# TradingView column → checkup key
MAP = {"ATR": "ATR", "ADX": "ADX", "ADX[1]": "ADX1", "ADX+DI": "DIp", "ADX-DI": "DIm", "CCI20": "CCI", "CCI20[1]": "CCI1",
       "EMA20": "EMA20", "EMA50": "EMA50", "SMA150": "SMA150", "relative_volume_10d_calc": "RVOL", "SMA20": "SMA20",
       "BB.upper": "BBU", "SMA20|1W": "SMA20W", "BB.upper|1W": "BBUW", "Pivot.M.Classic.Middle": "PP",
       "Pivot.M.Classic.R1": "R1", "Pivot.M.Classic.R2": "R2", "Pivot.M.Classic.S1": "S1", "Pivot.M.Classic.S2": "S2",
       "High.1M": "H1M", "Low.1M": "L1M", "High.3M": "H3M", "Low.3M": "L3M", "average_volume_10d_calc": "vol10"}

INFO = ["קבוצה", "טיקר", "בורסה", "שם", "מחיר", "שינוי %", "נפח", "RVOL 10d", "שווי שוק ($B)", "P/E", "סקטור",
        "RSI 14", "ADX 14", "+DI", "-DI", "ATR 14", "ATR %", "EMA20", "EMA50", "SMA150", "מרחק מ-SMA150 %",
        "SMA200", "מרחק מ-SMA200 %", "מעל SMA200", "מגמה", "דירוג TV", "שיא 52ש", "שפל 52ש",
        "מרחק משיא 52ש %", "מיקום בטווח 52ש %", "דוח הבא", "נר אחרון"]

# columns taken from checkup.py's own output, by header name
FROM_CHECKUP = ["סטטוס", "ציון כניסה", "בולינגר יומי (σ)", "בולינגר שבועי (σ)",
                "תמיכה 1", "תמיכה 2", "תמיכה 3", "התנגדות 1", "התנגדות 2", "התנגדות 3",
                "אזור", "קו 50%", "תחילת התיקון", "שפל התיקון",
                "התנגדות קרובה", "מקור התנגדות קרובה", "תמיכה קרובה", "מקור תמיכה קרובה",
                *checkup.PLAN_HEADERS, "הערות"]


def trend(x):
    if x.get("SMA200") is None:
        return "אין SMA200"
    c, e20, e50, s200 = x["close"], x["EMA20"], x["EMA50"], x["SMA200"]
    if c > e20 > e50 and c > s200:
        return "עולה"
    if c < e20 < e50 and c < s200:
        return "יורדת"
    return "מעורבת"


def rating(v):
    if v is None:
        return ""
    return "Strong Buy" if v >= .5 else "Buy" if v >= .1 else "Neutral" if v > -.1 else "Sell" if v > -.5 else "Strong Sell"


def pct(a, b):
    return None if a is None or not b else (a / b - 1) * 100


def info_row(group, sym, x, bar_date):
    ex, tk = sym.split(":")
    if not x:
        return [group, tk, ex, "אין נתונים מ-TradingView"] + [None] * (len(INFO) - 4)
    c, hi, lo = x.get("close"), x.get("price_52_week_high"), x.get("price_52_week_low")
    er = x.get("earnings_release_next_date")
    mc = x.get("market_cap_basic")
    return [
        group, tk, ex, x.get("description"), c, x.get("change"), x.get("volume"), x.get("relative_volume_10d_calc"),
        mc / 1e9 if mc else None, x.get("price_earnings_ttm"), x.get("sector"),
        x.get("RSI"), x.get("ADX"), x.get("ADX+DI"), x.get("ADX-DI"), x.get("ATR"),
        x["ATR"] / c * 100 if x.get("ATR") and c else None,
        x.get("EMA20"), x.get("EMA50"), x.get("SMA150"), pct(c, x.get("SMA150")),
        x.get("SMA200"), pct(c, x.get("SMA200")),
        "" if x.get("SMA200") is None else ("כן" if c > x["SMA200"] else "לא"),
        trend(x), rating(x.get("Recommend.All")), hi, lo, pct(c, hi),
        (c - lo) / (hi - lo) * 100 if hi and lo is not None and hi > lo else None,
        dt.datetime.utcfromtimestamp(er).strftime("%Y-%m-%d") if er else "",
        bar_date,
    ]


def main(tv_path, order_path, date, out, bars_path=None):
    tv = json.load(open(tv_path))
    tvbars = json.load(open(bars_path)) if bars_path else {}
    order = json.load(open(order_path))
    upto = dt.date.fromisoformat(date) + dt.timedelta(days=1)

    group, entries = INDEX_GROUP, []
    for s in order:
        if s.startswith("###"):
            group = s[3:]
        elif ":" in s:
            entries.append((group, s))
    stocks = [s for g, s in entries if g != INDEX_GROUP and s in tv]

    # Yahoo: 12 daily candles + levels + correction, checked against the TradingView close
    def one(s):
        try:
            d, w = daily_weekly(s, upto)
            x = tv[s]
            if s in tvbars:
                b = tvbars[s]
                days = [dt.datetime.fromtimestamp(t, dt.timezone.utc).date() for t in b["t"]]
                for i, day in enumerate(days):
                    d.loc[day, ["o", "h", "l", "c", "v"]] = [b[k][i] for k in "ohlcv"]
                d = d.sort_index()
                d = d[[x < upto for x in d.index]]
                di = d.copy()
                di.index = __import__("pandas").to_datetime(di.index)
                w = di.resample("W-FRI").agg({"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum"}).dropna()
                w.index = w.index.date
            last_day, yc = str(d.index[-1]), float(d["c"].iloc[-1])
            if last_day != date:
                return s, None, f"Yahoo last bar {last_day}, expected {date}"
            if abs(yc / x["close"] - 1) > 0.002:
                return s, None, f"close mismatch Yahoo {yc} vs TradingView {x['close']}"
            bars = [[float(v) for v in r] for r in d[["o", "h", "l", "c", "v"]].tail(12).itertuples(index=False)]
            v = {MAP[k]: x.get(k) for k in MAP}
            v["bars"] = bars
            v.update(correction(d, w, x["ATR"], bars[-1][3]))
            v.update(sr_levels(d, w, x["ATR"], bars[-1][3]))
            return s, v, None
        except Exception as e:
            return s, None, repr(e)

    tickers, errs = {}, []
    for s, v, e in groups(one, stocks):
        if v:
            tickers[s] = v
        else:
            errs.append((s, e))
    print("checkup inputs:", len(tickers), "| errors:", errs)

    with tempfile.TemporaryDirectory() as tmp:
        checkup.build({"date": date, "bar_date": date, "watchlist": "PROTFOLIO", "tickers": json.loads(json.dumps(tickers))},
                      os.path.join(tmp, "c.xlsx"))
        rows = list(csv.reader(open(os.path.join(tmp, "c.csv"), encoding="utf-8")))
    H, ck = rows[0], {}
    for r in rows[1:]:
        ck[r[0]] = {h: r[H.index(h)] for h in FROM_CHECKUP}

    headers = INFO + FROM_CHECKUP
    out_rows = []
    for g, s in entries:
        row = info_row(g, s, tv.get(s), date)
        c = ck.get(s.split(":")[1], {})
        row += [c.get(h, "") for h in FROM_CHECKUP]
        if g != INDEX_GROUP and s in tv and not c:
            row[headers.index("הערות")] = "לא חושבו רמות ותוכנית: " + next((e for x, e in errs if x == s), "אין נתונים")
        out_rows.append(row)

    def fmt(v):
        if isinstance(v, float):
            return round(v, 4) if abs(v) < 10 else round(v, 2)
        return "" if v is None else v

    with open(out + ".csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in out_rows:
            w.writerow([fmt(v) for v in r])

    wb = Workbook()
    ws = wb.active
    ws.title = "Portfolio"
    ws.sheet_view.rightToLeft = True
    ws.append(headers)
    for r in out_rows:
        ws.append([fmt(v) for v in r])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F3864")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "C2"
    wb.save(out + ".xlsx")
    json.dump({"date": date, "order": order, "tv": tv, "errors": errs}, open(out + ".json", "w"), ensure_ascii=False, indent=1)
    print("rows:", len(out_rows), "| columns:", len(headers))


if __name__ == "__main__":
    main(*sys.argv[1:6])
