import requests, json, time, sys, warnings
from datetime import datetime
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ── Load symbols ──────────────────────────────────────────────────────────────
with open('C:/Users/nsyon/SCAN/_long_syms.json')  as f: LONG_SYMS  = json.load(f)
with open('C:/Users/nsyon/SCAN/_short_syms.json') as f: SHORT_SYMS = json.load(f)

print(f"LONG:  {len(LONG_SYMS)} symbols")
print(f"SHORT: {len(SHORT_SYMS)} symbols")
print(f"Total: {len(LONG_SYMS)+len(SHORT_SYMS)} symbols to scan\n")

# ── Fetch Yahoo Finance ───────────────────────────────────────────────────────
def fetch_yahoo(symbol):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=3mo'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        data = r.json()
        result = data['chart']['result'][0]
        q = result['indicators']['quote'][0]
        closes  = [x for x in q.get('close',[])  if x is not None]
        highs   = [x for x in q.get('high',[])   if x is not None]
        lows    = [x for x in q.get('low',[])    if x is not None]
        volumes = [x for x in q.get('volume',[]) if x is not None]
        if len(closes) < 20:
            return None, f"Insufficient data ({len(closes)} bars)"
        return {'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes}, None
    except Exception as e:
        return None, str(e)[:60]

# ── Indicators ────────────────────────────────────────────────────────────────
def calc_ema(closes, period):
    if len(closes) < period:
        period = len(closes)
    k = 2 / (period + 1)
    ema = closes[0]
    for c in closes[1:]:
        ema = c * k + ema * (1 - k)
    return ema

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains  = [max(d, 0) for d in deltas[-period:]]
    losses = [max(-d, 0) for d in deltas[-period:]]
    avg_g = sum(gains) / period
    avg_l = sum(losses) / period
    if avg_l == 0:
        return 100.0
    return 100 - 100 / (1 + avg_g / avg_l)

def calc_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        period = len(closes) - 1
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return sum(trs[-period:]) / min(period, len(trs))

# ── Pivot Points (Standard Floor) ─────────────────────────────────────────────
def calc_pivot(highs, lows, closes):
    prev_high  = highs[-2]
    prev_low   = lows[-2]
    prev_close = closes[-2]
    P  = (prev_high + prev_low + prev_close) / 3
    R1 = 2 * P - prev_low
    S1 = 2 * P - prev_high
    R2 = P + (prev_high - prev_low)
    S2 = P - (prev_high - prev_low)
    return {
        'P':  round(P,  2),
        'R1': round(R1, 2),
        'S1': round(S1, 2),
        'R2': round(R2, 2),
        'S2': round(S2, 2),
    }

# ── Analyze ───────────────────────────────────────────────────────────────────
def analyze(symbol, direction, data):
    closes  = data['closes']
    highs   = data['highs']
    lows    = data['lows']
    volumes = data['volumes']

    last_close = closes[-1]
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    rsi   = calc_rsi(closes, 14)
    atr   = calc_atr(highs, lows, closes, 14)

    avg_vol   = sum(volumes[-20:]) / min(20, len(volumes)) if volumes else 1
    last_vol  = volumes[-1] if volumes else 0
    vol_ratio = last_vol / avg_vol if avg_vol > 0 else 0

    dist_ema20 = (last_close - ema20) / ema20 * 100

    # Pivot Points
    pivot = calc_pivot(highs, lows, closes)
    P, R1, S1 = pivot['P'], pivot['R1'], pivot['S1']

    # Direction filter — price must be on the correct side of P
    if direction == 'LONG':
        if last_close <= P:
            return None, f"Price below Pivot (close={last_close:.2f} P={P:.2f})"
        entry = P
        sl    = S1
        tp    = R1
    else:
        if last_close >= P:
            return None, f"Price above Pivot (close={last_close:.2f} P={P:.2f})"
        entry = P
        sl    = R1
        tp    = S1

    entry = round(entry, 2)
    sl    = round(sl,    2)
    tp    = round(tp,    2)

    risk   = abs(entry - sl)
    reward = abs(tp - entry)

    if risk < 0.001:
        return None, f"SL too close to entry (risk={risk:.4f})"

    rr       = round(reward / risk, 2)
    days_est = round(reward / atr, 1) if atr > 0 else 99
    shares = 0

    # Filter: only setups reachable within 3 days with decent R:R
    if days_est > 3:
        return None, f"Days Est. too long ({days_est} days)"
    if rr < 2.0:
        return None, f"R:R too low ({rr})"

    # Score
    if direction == 'LONG':
        volume_score = min(vol_ratio * 30, 40)
        rsi_score    = max(0, min((rsi - 50) / 50 * 25, 25))
        trend_score  = min(dist_ema20 / 10 * 20, 20)
        atr_score    = min(atr / last_close * 100 / 2 * 15, 15)
    else:
        volume_score = min(vol_ratio * 30, 40)
        rsi_score    = max(0, min((50 - rsi) / 50 * 25, 25))
        trend_score  = min(abs(dist_ema20) / 10 * 20, 20)
        atr_score    = min(atr / last_close * 100 / 2 * 15, 15)

    score = round(volume_score + rsi_score + trend_score + atr_score, 1)

    return {
        'symbol': symbol, 'direction': direction,
        'entry': entry, 'sl': sl, 'tp': tp,
        'rr': rr, 'days_est': days_est, 'shares': shares, 'score': score,
        'rsi': round(rsi, 1), 'vol_ratio': round(vol_ratio, 2),
        'dist_ema20': round(dist_ema20, 2),
        'atr': round(atr, 3),
        'P': P, 'R1': R1, 'S1': S1,
        'R2': pivot['R2'], 'S2': pivot['S2'],
        'ema20': round(ema20, 2), 'ema50': round(ema50, 2)
    }, None

# ── Run scan ──────────────────────────────────────────────────────────────────
results = []
errors  = []
skipped = []

all_tasks = [(s, 'LONG') for s in LONG_SYMS] + [(s, 'SHORT') for s in SHORT_SYMS]
total = len(all_tasks)

for i, (sym, direction) in enumerate(all_tasks):
    print(f"[{i+1}/{total}] {sym} ({direction})...", end=' ')
    data, err = fetch_yahoo(sym)
    if err:
        errors.append({'symbol': sym, 'error': err})
        print(f"ERROR: {err}")
        continue
    result, skip_reason = analyze(sym, direction, data)
    if skip_reason:
        skipped.append({'symbol': sym, 'reason': skip_reason})
        print(f"skip: {skip_reason}")
    else:
        results.append(result)
        print(f"✓ score={result['score']} entry={result['entry']} SL={result['sl']} TP={result['tp']} Days={result['days_est']}")
    time.sleep(0.15)

# Sort by score
long_results  = sorted([r for r in results if r['direction']=='LONG'],  key=lambda x: -x['score'])
short_results = sorted([r for r in results if r['direction']=='SHORT'], key=lambda x: -x['score'])

top5_long  = long_results[:5]
top5_short = short_results[:5]

print(f"\n{'='*60}")
print(f"LONG setups:  {len(long_results)} | SHORT setups: {len(short_results)}")
print(f"TOP 5 LONG:   {[r['symbol'] for r in top5_long]}")
print(f"TOP 5 SHORT:  {[r['symbol'] for r in top5_short]}")

# Save JSON
with open('C:/Users/nsyon/SCAN/_pivot_scan_results.json', 'w') as f:
    json.dump({
        'long': long_results, 'short': short_results,
        'top5_long': top5_long, 'top5_short': top5_short,
        'errors': errors, 'skipped': skipped,
        'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, f, indent=2)
print("Saved to _pivot_scan_results.json")

# ── Generate HTML ─────────────────────────────────────────────────────────────
scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def score_bar(score):
    color = '#00cc66' if score >= 60 else '#ffaa00' if score >= 40 else '#ff4444'
    return f'<div style="background:#222;border-radius:4px;height:8px;width:100%;margin-top:4px"><div style="background:{color};width:{min(score,100)}%;height:8px;border-radius:4px"></div></div>'

def top5_card(title, stocks, border_color, dir_label):
    rows = ''
    for i, s in enumerate(stocks, 1):
        rows += f'''
        <div style="padding:8px 0;border-bottom:1px solid #333">
          <b style="color:#fff">#{i} {s["symbol"]}</b>
          <span style="float:right;color:#aaa">{s["score"]}/100</span>
          {score_bar(s["score"])}
          <small style="color:#888">Volume ×{s["vol_ratio"]} | RSI {s["rsi"]} | Days Est: {s["days_est"]} | R:R {s["rr"]}</small>
        </div>'''
    return f'''
    <div style="background:#1a1a1a;border:2px solid {border_color};border-radius:8px;padding:16px;flex:1">
      <h3 style="color:{border_color};margin:0 0 12px">🏆 TOP 5 {dir_label}</h3>
      {rows}
    </div>'''

def table_rows(stocks, top5_symbols, color):
    rows = ''
    for s in stocks:
        star = '⭐ ' if s['symbol'] in top5_symbols else ''
        rows += f'''
        <tr data-symbol="{s["symbol"]}" data-entry="{s["entry"]}" data-sl="{s["sl"]}" data-tp="{s["tp"]}" data-p="{s["P"]}" data-r1="{s["R1"]}" data-s1="{s["S1"]}" data-r2="{s["R2"]}" data-s2="{s["S2"]}">
          <td style="color:{color}">{star}{s["symbol"]}</td>
          <td>{s["direction"]}</td>
          <td style="color:#fff">${s["P"]}</td>
          <td style="color:#ff6600">${s["R1"]}</td>
          <td style="color:#00cc66">${s["S1"]}</td>
          <td style="color:#ff4444">${s["R2"]}</td>
          <td style="color:#44aaff">${s["S2"]}</td>
          <td>{s["rr"]}</td>
          <td>{s["days_est"]}d</td>
          <td>{s["score"]}</td>
        </tr>'''
    return rows

top5_long_syms  = [r['symbol'] for r in top5_long]
top5_short_syms = [r['symbol'] for r in top5_short]

avg_days = round(sum(r['days_est'] for r in results) / len(results), 1) if results else 0

html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>DayScan Pivot — {scan_time}</title>
<style>
  body {{ background:#111; color:#eee; font-family:Arial,sans-serif; padding:20px; }}
  h2 {{ color:#fff; }} h3 {{ color:#aaa; }}
  table {{ width:100%; border-collapse:collapse; margin-top:16px; }}
  th {{ background:#222; color:#aaa; padding:8px; text-align:left; }}
  td {{ padding:8px; border-bottom:1px solid #222; }}
  tr:hover {{ background:#1e1e1e; }}
  .metric {{ background:#1a1a1a; border-radius:8px; padding:16px; text-align:center; flex:1; }}
  .metric-val {{ font-size:2em; font-weight:bold; color:#fff; }}
  .metric-label {{ color:#888; font-size:0.85em; }}
</style></head>
<body>
<h2>📊 DayScan Pivot</h2>
<p style="color:#666">Data: Yahoo Finance | Pivot Points: Standard Floor | Source: TradingView Screeners (CoffeeL/CoffeeS)<br>
Scan time: {scan_time}</p>

<!-- SECTION A: TOP PICKS -->
<div style="display:flex;gap:16px;margin-bottom:24px">
  {top5_card("TOP 5 LONG", top5_long, "#00cc66", "LONG")}
  {top5_card("TOP 5 SHORT", top5_short, "#ff4444", "SHORT")}
</div>

<!-- SECTION B: Summary -->
<div style="display:flex;gap:12px;margin-bottom:24px">
  <div class="metric"><div class="metric-val">{len(results)}</div><div class="metric-label">Total Setups</div></div>
  <div class="metric"><div class="metric-val" style="color:#00cc66">{len(long_results)}</div><div class="metric-label">LONG</div></div>
  <div class="metric"><div class="metric-val" style="color:#ff4444">{len(short_results)}</div><div class="metric-label">SHORT</div></div>
  <div class="metric"><div class="metric-val" style="color:#185FA5">{avg_days}d</div><div class="metric-label">Avg Days Est.</div></div>
</div>

<!-- SECTION C: Tables -->
<h3>🟢 LONG Setups</h3>
<table>
  <tr><th>Symbol</th><th>Dir</th><th>P</th><th>R1</th><th>S1</th><th>R2</th><th>S2</th><th>R:R</th><th>Days Est.</th><th>Score</th></tr>
  {table_rows(long_results, top5_long_syms, "#00cc66")}
</table>

<h3 style="margin-top:32px">🔴 SHORT Setups</h3>
<table>
  <tr><th>Symbol</th><th>Dir</th><th>Entry (P)</th><th>Stop Loss (R1)</th><th>Take Profit (S1)</th><th>R:R</th><th>Days Est.</th><th>Score</th></tr>
  {table_rows(short_results, top5_short_syms, "#ff4444")}
</table>

<!-- SECTION D: Errors -->
<h3 style="margin-top:32px;color:#666">⚠️ Errors ({len(errors)})</h3>
{"".join(f'<p style="color:#555">{e["symbol"]}: {e["error"]}</p>' for e in errors)}

<p style="color:#444;margin-top:32px">File: C:\\Users\\nsyon\\SCAN\\dayscan_pivot_results.html</p>
</body></html>'''

with open('C:/Users/nsyon/SCAN/dayscan_pivot_results.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"HTML saved to: C:/Users/nsyon/SCAN/dayscan_pivot_results.html")
