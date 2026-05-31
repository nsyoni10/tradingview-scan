# -*- coding: utf-8 -*-
import requests, json, warnings, sys
from datetime import datetime
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

def read_csv(path):
    try:
        with open(path, 'r') as f:
            return [l.strip() for l in f if l.strip()]
    except:
        return []

LONG_SYMS  = read_csv(r"C:\Users\nsyon\SCAN\LONG.CSV")
SHORT_SYMS = read_csv(r"C:\Users\nsyon\SCAN\SHORT.CSV")

def ema(prices, period):
    if len(prices) < period:
        period = len(prices)
    k = 2 / (period + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p * k + e * (1 - k)
    return e

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i] - closes[i-1] for i in range(len(closes)-period, len(closes))]
    gains  = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)

def calc_atr(highs, lows, closes, period=14):
    if len(highs) < period + 1:
        period = len(highs) - 1
    trs = []
    for i in range(len(highs)-period, len(highs)):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i-1])
        lc = abs(lows[i]  - closes[i-1])
        trs.append(max(hl, hc, lc))
    return sum(trs) / len(trs) if trs else 0

def fetch(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=3mo"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        data = r.json()
        result = data['chart']['result'][0]
        q = result['indicators']['quote'][0]
        closes  = [x for x in q['close']  if x is not None]
        highs   = [x for x in q['high']   if x is not None]
        lows    = [x for x in q['low']    if x is not None]
        volumes = [x for x in q['volume'] if x is not None]
        if len(closes) < 10:
            return None, "not enough data"
        return {'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes}, None
    except Exception as e:
        return None, str(e)[:60]

def score_long(volume_ratio, rsi, dist_ema20, atr, last_close):
    volume_score = min(volume_ratio * 30, 40)
    rsi_score    = max(0, min((rsi - 50) / 50 * 25, 25))
    trend_score  = min(dist_ema20 / 10 * 20, 20)
    atr_score    = min(atr / last_close * 100 / 2 * 15, 15)
    return round(volume_score + rsi_score + trend_score + atr_score, 1)

def score_short(volume_ratio, rsi, dist_ema20, atr, last_close):
    volume_score = min(volume_ratio * 30, 40)
    rsi_score    = max(0, min((50 - rsi) / 50 * 25, 25))
    trend_score  = min(abs(dist_ema20) / 10 * 20, 20)
    atr_score    = min(atr / last_close * 100 / 2 * 15, 15)
    return round(volume_score + rsi_score + trend_score + atr_score, 1)

longs, shorts, errors = [], [], []

print(f"Scanning {len(LONG_SYMS)} LONG + {len(SHORT_SYMS)} SHORT symbols...")

for sym in LONG_SYMS:
    data, err = fetch(sym)
    if err:
        errors.append((sym, err)); print(f"  {sym}: ERROR {err}"); continue
    closes, highs, lows, volumes = data['closes'], data['highs'], data['lows'], data['volumes']
    last = closes[-1]
    e20  = ema(closes[-20:], 20)
    e50  = ema(closes, 50)
    if last > e20 and last > e50:
        entry = round(last, 2)
        sl    = round(min(lows[-3:]) * 0.995, 2)
        tp    = round(entry + 2 * (entry - sl), 2)
        rr    = 2.0
        avg_vol = sum(volumes[-20:]) / min(len(volumes), 20)
        vol_ratio = volumes[-1] / avg_vol if avg_vol else 1.0
        rsi   = calc_rsi(closes)
        atr   = calc_atr(highs, lows, closes)
        dist_e20 = (last - e20) / e20 * 100
        dist_e50 = (last - e50) / e50 * 100
        sc    = score_long(vol_ratio, rsi, dist_e20, atr, last)
        reason = f"Volume x{vol_ratio:.1f} | RSI {rsi} | +{dist_e20:.1f}% above EMA20"
        longs.append({'symbol':sym,'dir':'LONG','entry':entry,'sl':sl,'tp':tp,'rr':rr,
                      'score':sc,'reason':reason,'rsi':rsi,'atr':round(atr,2),'vol_ratio':round(vol_ratio,2)})
        print(f"  {sym}: LONG entry={entry} sl={sl} tp={tp} score={sc}")
    else:
        print(f"  {sym}: skip (close={round(last,2)} EMA20={round(e20,2)} EMA50={round(e50,2)})")

for sym in SHORT_SYMS:
    data, err = fetch(sym)
    if err:
        errors.append((sym, err)); print(f"  {sym}: ERROR {err}"); continue
    closes, highs, lows, volumes = data['closes'], data['highs'], data['lows'], data['volumes']
    last = closes[-1]
    e20  = ema(closes[-20:], 20)
    e50  = ema(closes, 50)
    if last < e20 and last < e50:
        entry = round(last, 2)
        sl    = round(max(highs[-3:]) * 1.005, 2)
        tp    = round(entry - 2 * (sl - entry), 2)
        rr    = 2.0
        avg_vol = sum(volumes[-20:]) / min(len(volumes), 20)
        vol_ratio = volumes[-1] / avg_vol if avg_vol else 1.0
        rsi   = calc_rsi(closes)
        atr   = calc_atr(highs, lows, closes)
        dist_e20 = (last - e20) / e20 * 100
        dist_e50 = (last - e50) / e50 * 100
        sc    = score_short(vol_ratio, rsi, dist_e20, atr, last)
        reason = f"Volume x{vol_ratio:.1f} | RSI {rsi} | {dist_e20:.1f}% below EMA20"
        shorts.append({'symbol':sym,'dir':'SHORT','entry':entry,'sl':sl,'tp':tp,'rr':rr,
                       'score':sc,'reason':reason,'rsi':rsi,'atr':round(atr,2),'vol_ratio':round(vol_ratio,2)})
        print(f"  {sym}: SHORT entry={entry} sl={sl} tp={tp} score={sc}")
    else:
        print(f"  {sym}: skip (close={round(last,2)} EMA20={round(e20,2)} EMA50={round(e50,2)})")

# Sort by score and pick TOP 5
longs.sort(key=lambda x: x['score'], reverse=True)
shorts.sort(key=lambda x: x['score'], reverse=True)
top5_long  = longs[:5]
top5_short = shorts[:5]
top5_long_syms  = {s['symbol'] for s in top5_long}
top5_short_syms = {s['symbol'] for s in top5_short}

scan_time = datetime.now().strftime("%Y-%m-%d %H:%M")
total = len(longs) + len(shorts)

def score_bar(score):
    pct = min(int(score), 100)
    color = '#4ec9b0' if pct >= 60 else ('#f0b429' if pct >= 40 else '#f88')
    return f'<div style="background:#333;border-radius:4px;height:8px;width:120px;display:inline-block;vertical-align:middle;margin-left:8px"><div style="background:{color};width:{pct}%;height:100%;border-radius:4px"></div></div>'

def top5_card(picks, dir_label, border_color, text_color):
    rows = ''
    for i, s in enumerate(picks):
        star = '&#9733;'
        rows += f'''<div style="display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #2a2a2a">
          <span style="color:{text_color};font-size:18px;font-weight:bold;min-width:28px">{i+1}</span>
          <span style="font-weight:bold;min-width:70px">{star} {s["symbol"]}</span>
          <span style="color:#aaa;font-size:13px;flex:1">{s["reason"]}</span>
          <span style="color:{text_color};font-weight:bold;min-width:40px;text-align:right">{s["score"]}</span>
          {score_bar(s["score"])}
        </div>'''
    return f'''<div style="background:#1a1a1a;border-radius:10px;padding:18px 22px;flex:1;border-top:3px solid {border_color}">
      <h3 style="color:{text_color};margin:0 0 12px 0">&#127942; TOP 5 {dir_label}</h3>
      {rows}
    </div>'''

def row(s):
    star = ' <span style="color:#f0b429">&#9733;</span>' if (s['symbol'] in top5_long_syms or s['symbol'] in top5_short_syms) else ''
    cls = 'long' if s['dir']=='LONG' else 'short'
    badge = 'badge-long' if s['dir']=='LONG' else 'badge-short'
    return (f'<tr class="{cls}" data-symbol="{s["symbol"]}" data-entry="{s["entry"]}" '
            f'data-sl="{s["sl"]}" data-tp="{s["tp"]}">'
            f'<td><b>{s["symbol"]}</b>{star}</td>'
            f'<td><span class="{badge}">{s["dir"]}</span></td>'
            f'<td>{s["entry"]}</td><td>{s["sl"]}</td><td>{s["tp"]}</td><td>{s["rr"]}</td>'
            f'<td style="color:#aaa;font-size:12px">{s["score"]}</td></tr>')

err_html = ''.join(f'<li>{s}: {e}</li>' for s,e in errors) if errors else '<li>None</li>'

html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>DayScan {scan_time}</title>
<style>
  body {{font-family:Arial;background:#111;color:#eee;padding:20px}}
  h1 {{color:#4ec9b0}} h2 {{margin-top:30px}}
  table {{width:100%;border-collapse:collapse;margin-top:10px}}
  th {{background:#333;padding:10px;text-align:left;color:#ccc}}
  td {{padding:9px;border-bottom:1px solid #222}}
  .long  {{background:#1a3a2a}} .short {{background:#3a1a1a}}
  .badge-long  {{background:#0F6E56;color:#E1F5EE;padding:3px 10px;border-radius:4px;font-weight:bold}}
  .badge-short {{background:#993C1D;color:#FAECE7;padding:3px 10px;border-radius:4px;font-weight:bold}}
  .summary {{display:flex;gap:20px;margin:15px 0;flex-wrap:wrap}}
  .card {{background:#222;border-radius:8px;padding:14px 24px;text-align:center}}
  .card span {{display:block;font-size:26px;font-weight:bold}}
  .errors {{margin-top:20px;color:#f88}}
  .top5-row {{display:flex;gap:20px;margin:20px 0;flex-wrap:wrap}}
</style></head><body>
<h1>DayScan</h1>
<p>Scan date: <b>{scan_time}</b> &nbsp;|&nbsp; Data: Yahoo Finance</p>

<div class="top5-row">
  {top5_card(top5_long,  "LONG",  "#0F6E56", "#4ec9b0")}
  {top5_card(top5_short, "SHORT", "#993C1D", "#f88")}
</div>

<div class="summary">
  <div class="card">Total Setups<span>{total}</span></div>
  <div class="card" style="border-top:3px solid #0F6E56">LONG<span style="color:#4ec9b0">{len(longs)}</span></div>
  <div class="card" style="border-top:3px solid #993C1D">SHORT<span style="color:#f88">{len(shorts)}</span></div>
</div>

<h2 style="color:#4ec9b0">LONG Setups</h2>
<table><tr><th>Symbol</th><th>Direction</th><th>Entry</th><th>Stop Loss</th><th>Take Profit</th><th>R:R</th><th>Score</th></tr>
{''.join(row(s) for s in longs) if longs else '<tr><td colspan=7 style="color:#888">No LONG setups found</td></tr>'}
</table>

<h2 style="color:#f88">SHORT Setups</h2>
<table><tr><th>Symbol</th><th>Direction</th><th>Entry</th><th>Stop Loss</th><th>Take Profit</th><th>R:R</th><th>Score</th></tr>
{''.join(row(s) for s in shorts) if shorts else '<tr><td colspan=7 style="color:#888">No SHORT setups found</td></tr>'}
</table>

<div class="errors"><h3>Errors ({len(errors)})</h3><ul>{err_html}</ul></div>
</body></html>"""

out = r"C:\Users\nsyon\SCAN\dayscan_results.html"
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nDone! {len(longs)} LONG, {len(shorts)} SHORT, {len(errors)} errors")
print(f"TOP 5 LONG:  {[s['symbol'] for s in top5_long]}")
print(f"TOP 5 SHORT: {[s['symbol'] for s in top5_short]}")
print(f"Saved: {out}")
