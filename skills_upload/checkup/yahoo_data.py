"""Yahoo Finance data for checkup.

  python3 yahoo_data.py build  OUT.json DATE [SYM ...]   fallback when TradingView is unreachable:
                                                        builds the full checkup JSON (same fields as TV)
  python3 yahoo_data.py levels JSON                     adds correction / discount fields and 3 daily supports + 3 resistances (pivots 10/10, >=2 touches, 6 months)
  python3 yahoo_data.py news   JSON                     prints headlines since the last bar's close (16:00 ET)

Without SYM, build reads checkup_data/red_list.txt (the last Red list read from TradingView).
Requests go out in groups of at most 7.
"""
import json, sys, time, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd

LIST_FILE = "checkup_data/red_list.txt"
UA = {"User-Agent": "Mozilla/5.0"}


def _get_json(url):
    for i in range(2):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20))
        except Exception:
            if i:
                raise
            time.sleep(2)


def bars(t, rng, iv):
    j = _get_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?range={rng}&interval={iv}")["chart"]["result"][0]
    q = j["indicators"]["quote"][0]
    idx = pd.to_datetime(j["timestamp"], unit="s", utc=True).tz_convert("America/New_York").date
    df = pd.DataFrame({"o": q["open"], "h": q["high"], "l": q["low"], "c": q["close"], "v": q["volume"]}, index=idx).dropna()
    return df[~df.index.duplicated(keep="last")]


def groups(fn, items, n=7):
    out = []
    for i in range(0, len(items), n):
        with ThreadPoolExecutor(n) as ex:
            out += list(ex.map(fn, items[i:i + n]))
    return out


def ticker(sym):
    return sym.split(":")[1].replace(".", "-")


def daily_weekly(sym, upto):
    """Daily and weekly bars (5y), only bars that closed before `upto` (date of the run)."""
    t = ticker(sym)
    d = bars(t, "5y", "1d")
    d = d[[x < upto for x in d.index]]
    # weekly candles built from the daily ones, so a week never contains days after the bar date
    di = d.copy()
    di.index = pd.to_datetime(di.index)
    w = di.resample("W-FRI").agg({"o": "first", "h": "max", "l": "min", "c": "last", "v": "sum"}).dropna()
    w.index = w.index.date
    return d, w


def wilder(s, n):
    return s.ewm(alpha=1 / n, adjust=False).mean()


def indicators(d, w):
    h, l, c = d.h, d.l, d.c
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    atr = wilder(tr, 14)
    up, dn = h.diff(), -l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=d.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=d.index)
    pdi = 100 * wilder(pdm, 14) / atr
    mdi = 100 * wilder(mdm, 14) / atr
    adx = wilder(100 * (pdi - mdi).abs() / (pdi + mdi), 14)
    tp = (h + l + c) / 3
    md = tp.rolling(20).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    cci = (tp - tp.rolling(20).mean()) / (0.015 * md)
    sma20 = c.rolling(20).mean()
    bbu = sma20 + 2 * c.rolling(20).std(ddof=0)
    s20w = w.c.rolling(20).mean()
    bbuw = s20w + 2 * w.c.rolling(20).std(ddof=0)
    last = d.index[-1]
    pm = (last.year, last.month - 1) if last.month > 1 else (last.year - 1, 12)
    mm = d[[(x.year, x.month) == pm for x in d.index]]
    H, L, C = mm.h.max(), mm.l.min(), mm.c.iloc[-1]
    pp = (H + L + C) / 3
    f = lambda s: float(s.iloc[-1])
    return {
        "bars": [[float(x.o), float(x.h), float(x.l), float(x.c), int(x.v)] for x in d.tail(12).itertuples()],
        "ATR": f(atr), "ADX": f(adx), "ADX1": float(adx.iloc[-2]), "DIp": f(pdi), "DIm": f(mdi),
        "CCI": f(cci), "CCI1": float(cci.iloc[-2]),
        "EMA20": f(c.ewm(span=20, adjust=False).mean()), "EMA50": f(c.ewm(span=50, adjust=False).mean()),
        "SMA150": f(c.rolling(150).mean()), "RVOL": 0, "SMA20": f(sma20), "BBU": f(bbu),
        "SMA20W": f(s20w), "BBUW": f(bbuw),
        "PP": pp, "R1": 2 * pp - L, "R2": pp + H - L, "S1": 2 * pp - H, "S2": pp - (H - L),
        "H1M": float(h.tail(21).max()), "L1M": float(l.tail(21).min()),
        "H3M": float(h.tail(63).max()), "L3M": float(l.tail(63).min()),
        "vol10": float(d.v.tail(10).mean()),
    }


def swing_lows(df, k):
    """Lows that are lower than the k bars on each side."""
    l = df.l.values
    return [(df.index[i], float(l[i])) for i in range(k, len(l) - k)
            if l[i] == min(l[i - k:i + k + 1])]


def swing_highs(df, k):
    h = df.h.values
    return [(df.index[i], float(h[i])) for i in range(k, len(h) - k)
            if h[i] == max(h[i - k:i + k + 1])]


PIVOT_BARS = 10      # pivot = highest high / lowest low of 10 bars on each side (TradingView Pivots High Low style)
TOUCH_BARS = 3       # a touch = a smaller turning point (3 bars on each side) inside the level's zone
MIN_TOUCHES = 2      # a level needs at least 2 touches
LOOKBACK = (126, 252)  # 6 months first; if a side has fewer than 3 levels, extend to 1 year


def sr_levels(d, w, atr, close, n=3, min_touches=MIN_TOUCHES):
    """Daily support/resistance.
    1. Pivots: swing highs/lows with PIVOT_BARS bars on each side, in the last 6 months.
    2. Pivots within 0.25 ATR are one level (span at most 0.5 ATR); price = their average.
    3. Touches: turning points (TOUCH_BARS bars each side, highs and lows) within 0.25 ATR of the level's zone.
       Levels with fewer than MIN_TOUCHES touches are dropped.
    4. If a side has fewer than n levels, the 6-12 month window is added (marked 'old').
    5. Weekly: a weekly swing high/low (3 weeks each side, 3 years) within 0.15 ATR of the level."""
    wk = [v for _, v in swing_lows(w.tail(156), 3) + swing_highs(w.tail(156), 3)]

    def levels(lb):
        part = d.tail(lb)
        piv = sorted(v for _, v in swing_lows(part, PIVOT_BARS) + swing_highs(part, PIVOT_BARS))
        small = [v for _, v in swing_lows(part, TOUCH_BARS) + swing_highs(part, TOUCH_BARS)]
        zones = []
        for v in piv:
            if zones and v - zones[-1][-1] <= 0.25 * atr and v - zones[-1][0] <= 0.5 * atr:
                zones[-1].append(v)
            else:
                zones.append([v])
        out = []
        for z in zones:
            lo, hi = z[0] - 0.25 * atr, z[-1] + 0.25 * atr
            p = sum(z) / len(z)
            out.append({"p": round(p, 2), "touch": sum(lo <= x <= hi for x in small),
                        "weekly": any(abs(p - x) <= 0.15 * atr for x in wk), "old": lb > LOOKBACK[0]})
        return [x for x in out if x["touch"] >= min_touches]

    def side(lv, below):
        f = (lambda x: x["p"] < close) if below else (lambda x: x["p"] > close)
        return sorted(filter(f, lv), key=lambda x: -x["p"] if below else x["p"])

    six = levels(LOOKBACK[0])
    year = [x for x in levels(LOOKBACK[1]) if all(abs(x["p"] - y["p"]) > 0.25 * atr for y in six)]
    res = {}
    for key, below in (("sr_sup", True), ("sr_res", False)):
        got = side(six, below)
        if len(got) < n:
            got = side(got + side(year, below), below)
        res[key] = got[:n]
    return res


def correction(d, w, atr, close):
    """Correction = from the highest high of the last 3 months (the start of the correction)
    to the lowest low after it. 50% = middle of that range: below = discount, above = premium.
    Nearest support = highest support level below min(close, 50% line)."""
    last63 = d.tail(63)
    hi_date = last63.h.idxmax()
    hi = float(last63.h.max())
    after = d[[x >= hi_date for x in d.index]]
    lo_date = after.l.idxmin()
    lo = float(after.l.min())
    mid = (hi + lo) / 2
    ref = min(close, mid)

    year = d.tail(252)
    cands = []
    for dte, v in swing_lows(w.tail(156), 2):
        cands.append((v, f"שפל שבועי {dte:%d/%m/%y}", 2))
    for dte, v in swing_lows(year, 3):
        cands.append((v, f"שפל יומי {dte:%d/%m/%y}", 1))
    cands.append((float(year.l.min()), "שפל 52 שבועות", 2))
    cands.append((float(d.c.rolling(150).mean().iloc[-1]), "SMA150", 1))
    cands.append((float(d.c.rolling(200).mean().iloc[-1]), "SMA200", 1))
    below = sorted([c for c in cands if c[0] < ref and not np.isnan(c[0])], key=lambda c: -c[0])
    sup = None
    if below:
        top = below[0][0]
        cluster = [c for c in below if top - c[0] <= 0.25 * atr]   # levels within 0.25 ATR = one zone
        best = max(cluster, key=lambda c: (c[2], c[0]))
        sup = {"price": top, "src": " + ".join(dict.fromkeys(c[1] for c in cluster)), "weekly": best[2] == 2}
    return {
        "corr_hi": hi, "corr_hi_date": str(hi_date), "corr_lo": lo, "corr_lo_date": str(lo_date),
        "corr_mid": mid, "zone": "discount" if close <= mid else "premium",
        "sup": sup["price"] if sup else None, "sup_src": sup["src"] if sup else "",
        "sup_from": "סגירה" if close <= mid else "קו 50%",
    }


def cmd_build(out, date, syms):
    upto = dt.date.fromisoformat(date)
    if not syms:
        syms = [s.strip() for s in open(LIST_FILE) if ":" in s and not s.startswith("#")]

    def one(s):
        try:
            d, w = daily_weekly(s, upto)
            v = indicators(d, w)
            v.update(correction(d, w, v["ATR"], v["bars"][-1][3]))
            v.update(sr_levels(d, w, v["ATR"], v["bars"][-1][3]))
            return s, v, str(d.index[-1])
        except Exception as e:
            return s, None, repr(e)

    res, dates, errs = {}, set(), []
    for s, v, x in groups(one, syms):
        if v is None:
            errs.append((s, x))
        else:
            res[s], _ = v, dates.add(x)
    print("bar dates:", dates, "| errors:", errs, "| tickers:", len(res))
    json.dump({"date": date, "bar_date": max(dates) if dates else "",
               "watchlist": "Red list (נתוני Yahoo)", "source": "yahoo", "tickers": res},
              open(out, "w"), indent=1, ensure_ascii=False)


def cmd_levels(path):
    data = json.load(open(path))
    upto = dt.date.fromisoformat(data["bar_date"]) + dt.timedelta(days=1)

    def one(s):
        try:
            d, w = daily_weekly(s, upto)
            v = data["tickers"][s]
            c = v["bars"][-1][3]
            return s, {**correction(d, w, v["ATR"], c), **sr_levels(d, w, v["ATR"], c)}, None
        except Exception as e:
            return s, None, repr(e)

    errs = []
    for s, c, e in groups(one, list(data["tickers"])):
        if c:
            data["tickers"][s].update(c)
        else:
            errs.append((s, e))
    print("levels added | errors:", errs)
    json.dump(data, open(path, "w"), indent=1, ensure_ascii=False)


def cmd_news(path):
    data = json.load(open(path))
    bd = dt.date.fromisoformat(data["bar_date"])
    et = dt.timezone(dt.timedelta(hours=-5 if bd.month in (11, 12, 1, 2) or (bd.month == 3 and bd.day < 8) else -4))
    since = dt.datetime(bd.year, bd.month, bd.day, 16, 0, tzinfo=et)

    def one(t):
        j = _get_json(f"https://query1.finance.yahoo.com/v1/finance/search?q={t}&newsCount=10&quotesCount=0")
        out = []
        for n in j.get("news", []):
            ts = dt.datetime.fromtimestamp(n["providerPublishTime"], dt.timezone.utc)
            if ts >= since:
                out.append(f"  {ts.astimezone(et):%d/%m %H:%M} ET | {n.get('publisher')} | {n['title']} | {n.get('relatedTickers')}")
        return t, out

    extra = sys.argv[3:]   # competitors to check as well
    for t, out in groups(one, [ticker(s) for s in data["tickers"]] + extra):
        print("==", t, *(["  (אין כותרות)"] if not out else out), sep="\n")


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "build":
        cmd_build(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif c == "levels":
        cmd_levels(sys.argv[2])
    elif c == "news":
        cmd_news(sys.argv[2])
