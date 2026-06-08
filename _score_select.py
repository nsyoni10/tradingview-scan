import json

def score_ticker(t):
    score = 0
    rsi = t['rsi']
    macd = t['macd']
    sig = t['signal']
    price = t['price']
    sma20 = t['sma20']
    sma50 = t['sma50']
    if rsi < 30: score += 2
    elif rsi < 45: score += 1
    elif rsi > 70: score -= 2
    elif rsi > 60: score -= 1
    if macd > sig: score += 1
    else: score -= 1
    if price > sma20 > sma50: score += 2
    elif price < sma20 < sma50: score -= 2
    return score

with open('_trading_analysis_long.json') as f:
    long_data = json.load(f)
with open('_trading_analysis_short.json') as f:
    short_data = json.load(f)

for t in long_data:
    t['score'] = score_ticker(t)
for t in short_data:
    t['score'] = score_ticker(t)

# TOP 10 LONG: STRONG BUY first (by score desc), then rest (by score desc)
strong_buy = sorted([t for t in long_data if t['rec'] == 'STRONG BUY'], key=lambda x: -x['score'])
rest_long = sorted([t for t in long_data if t['rec'] != 'STRONG BUY'], key=lambda x: -x['score'])
top10_long = (strong_buy + rest_long)[:10]

# TOP 10 SHORT: STRONG SELL first (by score asc), then rest (by score asc)
strong_sell = sorted([t for t in short_data if t['rec'] == 'STRONG SELL'], key=lambda x: x['score'])
rest_short = sorted([t for t in short_data if t['rec'] != 'STRONG SELL'], key=lambda x: x['score'])
top10_short = (strong_sell + rest_short)[:10]

with open('_top10_long.json', 'w') as f:
    json.dump(top10_long, f, indent=2)
with open('_top10_short.json', 'w') as f:
    json.dump(top10_short, f, indent=2)

print("TOP 10 LONG:")
for t in top10_long:
    print(f"  {t['symbol']:8s} score={t['score']:+d}  rec={t['rec']:12s}  rsi={t['rsi']:.1f}")
print("\nTOP 10 SHORT:")
for t in top10_short:
    print(f"  {t['symbol']:8s} score={t['score']:+d}  rec={t['rec']:12s}  rsi={t['rsi']:.1f}")

# Generate Table 1 HTML
def color_rec(rec):
    colors = {'STRONG BUY': '#00aa00', 'BUY': '#66bb00', 'HOLD': '#888888', 'SELL': '#dd6600', 'STRONG SELL': '#cc0000'}
    return colors.get(rec, '#333')

def score_color(s):
    if s >= 3: return '#00aa00'
    if s >= 1: return '#66bb00'
    if s == 0: return '#888'
    if s >= -2: return '#dd6600'
    return '#cc0000'

def build_table1(long_data, short_data):
    all_data = [(t, 'LONG') for t in sorted(long_data, key=lambda x: -x['score'])] + \
               [(t, 'SHORT') for t in sorted(short_data, key=lambda x: x['score'])]
    rows = ''
    for t, side in all_data:
        sc = t['score']
        rows += f"""<tr>
<td>{t['symbol']}</td>
<td style="color:{'#0066cc' if side=='LONG' else '#cc0000'};font-weight:bold">{side}</td>
<td>${t['price']:.2f}</td>
<td style="color:{'green' if t['change_pct']>=0 else 'red'}">{t['change_pct']:+.2f}%</td>
<td>{t['rsi']:.1f}</td>
<td>{t['vol']:.1f}%</td>
<td style="color:{color_rec(t['rec'])};font-weight:bold">{t['rec']}</td>
<td>${t['sma20']:.2f}</td>
<td>${t['sma50']:.2f}</td>
<td style="color:{score_color(sc)};font-weight:bold;font-size:16px">{sc:+d}</td>
</tr>
"""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>DayScan Pivot — Table 1</title>
<style>
body{{font-family:Arial,sans-serif;background:#0d1117;color:#e6edf3;margin:20px}}
h1{{color:#58a6ff}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th{{background:#161b22;color:#58a6ff;padding:8px 12px;border:1px solid #30363d;text-align:left}}
td{{padding:6px 12px;border:1px solid #21262d}}
tr:hover{{background:#161b22}}
tr:nth-child(even){{background:#0d1117}}
tr:nth-child(odd){{background:#111519}}
</style></head>
<body>
<h1>DayScan Pivot — All Tickers (Table 1)</h1>
<table>
<tr><th>Symbol</th><th>Side</th><th>Price</th><th>Change</th><th>RSI</th><th>Volatility</th><th>Rec</th><th>SMA20</th><th>SMA50</th><th>Score</th></tr>
{rows}
</table></body></html>"""

html = build_table1(long_data, short_data)
with open('dayscan_pivot_table1.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("\nSaved dayscan_pivot_table1.html")
