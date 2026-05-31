import requests, datetime, json, warnings
warnings.filterwarnings('ignore')

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def fetch_yahoo(symbol):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=3mo'
    r = requests.get(url, verify=False, headers=HEADERS, timeout=15)
    data = r.json()
    q = data['chart']['result'][0]['indicators']['quote'][0]
    closes = [x for x in q['close'] if x is not None]
    highs  = [x for x in q['high']  if x is not None]
    lows   = [x for x in q['low']   if x is not None]
    return closes, highs, lows

def ema(prices, n):
    k = 2 / (n + 1)
    e = prices[0]
    for p in prices[1:]:
        e = p * k + e * (1 - k)
    return round(e, 2)

long_syms  = [s.strip() for s in open('C:/Users/nsyon/SCAN/LONG.CSV').readlines() if s.strip()]
short_syms = [s.strip() for s in open('C:/Users/nsyon/SCAN/SHORT.CSV').readlines() if s.strip()]

rows, errors = [], []

for sym, side in [(s, 'LONG') for s in long_syms] + [(s, 'SHORT') for s in short_syms]:
    try:
        closes, highs, lows = fetch_yahoo(sym)
        if len(closes) < 20:
            errors.append(f'{sym}: not enough data')
            continue
        last  = round(closes[-1], 2)
        e20   = ema(closes[-20:], 20)
        e50   = ema(closes[-50:] if len(closes) >= 50 else closes, min(len(closes), 50))
        if side == 'LONG'  and not (last > e20 and last > e50): continue
        if side == 'SHORT' and not (last < e20 and last < e50): continue
        if side == 'LONG':
            sl = round(min(lows[-3:])  * 0.995, 2)
            tp = round(last + 2 * (last - sl), 2)
        else:
            sl = round(max(highs[-3:]) * 1.005, 2)
            tp = round(last - 2 * (sl - last), 2)
        rr = round(abs(tp - last) / abs(last - sl), 2) if abs(last - sl) > 0 else 0
        rows.append({'sym': sym, 'dir': side, 'entry': last, 'sl': sl, 'tp': tp, 'rr': rr})
        print(f'OK  {sym:6s} {side:5s}  entry={last}  sl={sl}  tp={tp}')
    except Exception as ex:
        errors.append(f'{sym}: {ex}')
        print(f'ERR {sym}: {ex}')

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
long_rows  = [r for r in rows if r['dir'] == 'LONG']
short_rows = [r for r in rows if r['dir'] == 'SHORT']

html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>DayScan {now}</title>
<style>
  body {{font-family:Arial;background:#111;color:#eee;padding:20px}}
  h1 {{color:#4ec9b0}} h2 {{margin-top:30px}}
  table {{width:100%;border-collapse:collapse;margin-top:10px}}
  th {{background:#333;padding:10px;text-align:left;color:#ccc}}
  td {{padding:9px;border-bottom:1px solid #222}}
  .long  {{background:#1a3a2a}} .short {{background:#3a1a1a}}
  .badge-long  {{background:#0F6E56;color:#E1F5EE;padding:3px 10px;border-radius:4px;font-weight:bold}}
  .badge-short {{background:#993C1D;color:#FAECE7;padding:3px 10px;border-radius:4px;font-weight:bold}}
  .summary {{display:flex;gap:20px;margin:15px 0}}
  .card {{background:#222;border-radius:8px;padding:14px 24px;text-align:center}}
  .card span {{display:block;font-size:26px;font-weight:bold}}
  .errors {{margin-top:20px;color:#f88}}
</style></head><body>
<h1>DayScan</h1>
<p>Scan date: <b>{now}</b> &nbsp;|&nbsp; Data: Yahoo Finance</p>
<div class="summary">
  <div class="card">Total Setups<span>{len(rows)}</span></div>
  <div class="card" style="border-top:3px solid #0F6E56">LONG<span style="color:#4ec9b0">{len(long_rows)}</span></div>
  <div class="card" style="border-top:3px solid #993C1D">SHORT<span style="color:#f88">{len(short_rows)}</span></div>
</div>
<h2 style="color:#4ec9b0">LONG Setups</h2>
<table><tr><th>Symbol</th><th>Direction</th><th>Entry</th><th>Stop Loss</th><th>Take Profit</th><th>R:R</th></tr>
'''

for r in long_rows:
    html += f'<tr class="long" data-symbol="{r["sym"]}" data-entry="{r["entry"]}" data-sl="{r["sl"]}" data-tp="{r["tp"]}"><td><b>{r["sym"]}</b></td><td><span class="badge-long">LONG</span></td><td>{r["entry"]}</td><td>{r["sl"]}</td><td>{r["tp"]}</td><td>{r["rr"]}</td></tr>\n'

html += '<tr><td colspan="6" style="color:#555;text-align:center">— no LONG setups —</td></tr>\n' if not long_rows else ''
html += '''</table>
<h2 style="color:#f88">SHORT Setups</h2>
<table><tr><th>Symbol</th><th>Direction</th><th>Entry</th><th>Stop Loss</th><th>Take Profit</th><th>R:R</th></tr>
'''

for r in short_rows:
    html += f'<tr class="short" data-symbol="{r["sym"]}" data-entry="{r["entry"]}" data-sl="{r["sl"]}" data-tp="{r["tp"]}"><td><b>{r["sym"]}</b></td><td><span class="badge-short">SHORT</span></td><td>{r["entry"]}</td><td>{r["sl"]}</td><td>{r["tp"]}</td><td>{r["rr"]}</td></tr>\n'

html += '<tr><td colspan="6" style="color:#555;text-align:center">— no SHORT setups —</td></tr>\n' if not short_rows else ''
html += '</table>'

if errors:
    html += '<div class="errors"><h3>Errors (' + str(len(errors)) + ')</h3><ul>' + ''.join(f'<li>{e}</li>' for e in errors) + '</ul></div>'

html += '</body></html>'

with open('C:/Users/nsyon/SCAN/dayscan_results.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nDONE: {len(rows)} setups ({len(long_rows)} LONG, {len(short_rows)} SHORT) | {len(errors)} errors')
print('File: C:/Users/nsyon/SCAN/dayscan_results.html')
