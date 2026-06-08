# -*- coding: utf-8 -*-
"""
learn5_screeners.py
משחזר את הלוגיקה של 5 הסורקים שלמדנו, ומריץ אותה על נתוני Yahoo Finance אמיתיים.
מקור נתונים: query1.finance.yahoo.com (אותו endpoint שכבר עובד בפרויקט SCAN, עם verify=False).

5 המתודולוגיות:
  1) shashankvemuri  -> Relative Strength מול SPY (returns multiple) + תנאי MA50/150/200
  2) asafravid/sss   -> סינון בסיסי (מחיר/נפח) + ציון נפח+מומנטום (גרסה מפושטת)
  3) ShauryaKohli01  -> ma50_score + rsi_score + vol_score, ממוצע ל-final_score
  4) Screeni-py      -> RelVol = volume_today / MA20(volume)   <-- הנוסחה המדויקת
  5) xang1234        -> Volume Breakthrough = קפיצת נפח מול ממוצע היסטורי
"""
import requests, json, warnings
warnings.filterwarnings('ignore')

H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ── משיכת היקום: most_actives + day_gainers ────────────────────────────────────
def fetch_universe():
    syms = []
    for scr in ['most_actives', 'day_gainers']:
        url = f'https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds={scr}&count=25'
        try:
            r = requests.get(url, headers=H, verify=False, timeout=15)
            rows = r.json()['finance']['result'][0]['quotes']
            syms += [q['symbol'] for q in rows]
        except Exception as e:
            print(f'  [universe] {scr} ERR: {str(e)[:60]}')
    # dedupe, שמירת סדר
    seen = set(); out = []
    for s in syms:
        if s not in seen:
            seen.add(s); out.append(s)
    return out

# ── משיכת OHLCV יומי (3 חודשים) ────────────────────────────────────────────────
def fetch_ohlcv(symbol):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=6mo'
    try:
        r = requests.get(url, headers=H, verify=False, timeout=15)
        res = r.json()['chart']['result'][0]
        q = res['indicators']['quote'][0]
        closes = [x for x in q.get('close', [])  if x is not None]
        highs  = [x for x in q.get('high', [])   if x is not None]
        lows   = [x for x in q.get('low', [])    if x is not None]
        vols   = [x for x in q.get('volume', []) if x is not None]
        if len(closes) < 60:
            return None
        return {'closes': closes, 'highs': highs, 'lows': lows, 'vols': vols}
    except Exception:
        return None

# ── אינדיקטורים ────────────────────────────────────────────────────────────────
def sma(xs, n):
    if len(xs) < n: n = len(xs)
    return sum(xs[-n:]) / n

def rsi(closes, period=14):
    if len(closes) < period + 1: return 50.0
    deltas = [closes[i]-closes[i-1] for i in range(1, len(closes))]
    gains  = [max(d, 0)  for d in deltas[-period:]]
    losses = [max(-d, 0) for d in deltas[-period:]]
    ag, al = sum(gains)/period, sum(losses)/period
    if al == 0: return 100.0
    return 100 - 100/(1 + ag/al)

def clamp(x, lo=-1, hi=1):
    return max(lo, min(hi, x))

# ════════════════════════════════════════════════════════════════════════════════
#  5 המתודולוגיות — כל אחת מקבלת dict נתונים ומחזירה מטריקות
# ════════════════════════════════════════════════════════════════════════════════

# 1) shashankvemuri — Relative Strength מול SPY (returns multiple) + תנאי MA
def m1_shashank(d, spy_ret):
    c = d['closes']
    stock_ret = c[-1] / c[0]                       # תשואת ~6 חודשים
    rs = stock_ret / spy_ret if spy_ret else 0     # returns multiple
    ma50, ma150, ma200 = sma(c,50), sma(c,150), sma(c,200)
    cond = (c[-1] > ma50 > ma150 > ma200)          # תנאי Minervini trend template
    return {'RS_mult': round(rs, 3), 'trend_ok': cond}

# 2) asafravid — סינון מחיר/נפח + ציון נפח*מומנטום (מפושט)
def m2_asafravid(d):
    c, v = d['closes'], d['vols']
    price = c[-1]
    avgvol = sma(v, 20)
    mom = c[-1] / c[-21] - 1 if len(c) > 21 else 0  # מומנטום חודש
    score = (mom * 100) * (avgvol / 1e6)            # מומנטום משוקלל בנזילות
    passes = price > 10 and avgvol > 1_000_000
    return {'avgvol_M': round(avgvol/1e6,2), 'mom1m_%': round(mom*100,1),
            'score': round(score,1), 'pass': passes}

# 3) ShauryaKohli — ma50_score + rsi_score + vol_score -> ממוצע
def m3_shaurya(d):
    c, v = d['closes'], d['vols']
    ma50 = sma(c, 50)
    ma50_score = clamp((c[-1]/ma50 - 1) * 10)                 # מרחק מעל/מתחת MA50
    r = rsi(c)
    rsi_score = clamp((r - 50) / 30)                          # מומנטום סביב 50
    vma20 = sma(v, 20)
    rising = c[-1] > c[-2]
    vol_score = clamp((v[-1]/vma20 - 1)) * (1 if rising else 0.3)
    final = (ma50_score + rsi_score + vol_score) / 3
    return {'ma50_s': round(ma50_score,2), 'rsi_s': round(rsi_score,2),
            'vol_s': round(vol_score,2), 'final': round(final,3)}

# 4) Screeni-py — RelVol = volume_today / MA20(volume)
def m4_screenipy(d):
    v = d['vols']
    vma20 = sma(v[:-1], 20) if len(v) > 21 else sma(v, 20)   # ממוצע ללא היום עצמו
    relvol = v[-1] / vma20 if vma20 else 0
    return {'RelVol': round(relvol, 2)}

# 5) xang1234 — Volume Breakthrough: קפיצת נפח מול ממוצע היסטורי (50 יום)
def m5_xang(d):
    c, v = d['closes'], d['vols']
    vma50 = sma(v[:-1], 50) if len(v) > 51 else sma(v, 50)
    breakthrough = v[-1] / vma50 if vma50 else 0
    up = c[-1] > c[-2]
    flag = breakthrough > 1.5 and up                        # קפיצת נפח + מחיר עולה
    return {'VolBT': round(breakthrough,2), 'up': up, 'flag': flag}

# ════════════════════════════════════════════════════════════════════════════════
def main():
    print('משיכת יקום (most_actives + day_gainers)...')
    universe = fetch_universe()
    print(f'  {len(universe)} מניות ביקום\n')

    spy = fetch_ohlcv('SPY')
    spy_ret = spy['closes'][-1] / spy['closes'][0] if spy else 1.0

    rows = []
    for s in universe:
        d = fetch_ohlcv(s)
        if not d: continue
        rows.append({
            'sym': s, 'price': round(d['closes'][-1], 2),
            'm1': m1_shashank(d, spy_ret),
            'm2': m2_asafravid(d),
            'm3': m3_shaurya(d),
            'm4': m4_screenipy(d),
            'm5': m5_xang(d),
        })

    def show(title, key, fmt, top=10, rev=True):
        print('\n' + '='*70)
        print(title)
        print('='*70)
        s = sorted(rows, key=key, reverse=rev)[:top]
        for i, r in enumerate(s, 1):
            print(f'{i:2}. {r["sym"]:6} ${r["price"]:>8}  {fmt(r)}')

    show('1) shashankvemuri — RS multiple מול SPY (trend_ok=טרנד תקין)',
         lambda r: r['m1']['RS_mult'],
         lambda r: f'RS={r["m1"]["RS_mult"]:>5}  trend_ok={r["m1"]["trend_ok"]}')

    show('2) asafravid — score = מומנטום×נזילות (pass=עבר סינון מחיר>10 ונפח>1M)',
         lambda r: r['m2']['score'],
         lambda r: f'score={r["m2"]["score"]:>7}  avgVol={r["m2"]["avgvol_M"]}M  mom1m={r["m2"]["mom1m_%"]}%  pass={r["m2"]["pass"]}')

    show('3) ShauryaKohli — final_score (ממוצע ma50/rsi/vol)',
         lambda r: r['m3']['final'],
         lambda r: f'final={r["m3"]["final"]:>6}  (ma50={r["m3"]["ma50_s"]} rsi={r["m3"]["rsi_s"]} vol={r["m3"]["vol_s"]})')

    show('4) Screeni-py — RelVol = נפח היום / MA20(נפח)  <<< הנוסחה שלך',
         lambda r: r['m4']['RelVol'],
         lambda r: f'RelVol={r["m4"]["RelVol"]}x')

    show('5) xang1234 — Volume Breakthrough מול ממוצע 50 יום (flag=קפיצה+עלייה)',
         lambda r: r['m5']['VolBT'],
         lambda r: f'VolBT={r["m5"]["VolBT"]}x  up={r["m5"]["up"]}  flag={r["m5"]["flag"]}')

if __name__ == '__main__':
    main()
