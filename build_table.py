import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('C:/Users/nsyon/SCAN/_trading_analysis_long.json') as f:
    long_data = json.load(f)
with open('C:/Users/nsyon/SCAN/_trading_analysis_short.json') as f:
    short_data = json.load(f)
data = long_data + short_data

rows = ''
for r in data:
    cls = 'strong-sell' if r['rec'] == 'STRONG SELL' else 'sell' if r['rec'] == 'SELL' else 'hold' if r['rec'] == 'HOLD' else 'buy' if r['rec'] == 'BUY' else 'strong-buy'
    sc_color = '#00ff88' if r['score'] >= 3 else '#00cc66' if r['score'] >= 1 else '#ffcc00' if r['score'] == 0 else '#ff6666' if r['score'] >= -2 else '#ff4444'
    rows += f"""<tr>
<td style="font-weight:bold">{r['symbol']}</td>
<td>${r['price']:.2f}</td>
<td>{'+' if r['change_pct']>0 else ''}{r['change_pct']:.2f}%</td>
<td>{r['rsi']:.1f}</td>
<td>${r['sma20']:.2f}</td>
<td>${r['sma50']:.2f}</td>
<td>{r['macd']:.2f}</td>
<td>{r['signal']:.2f}</td>
<td>${r['bb_upper']:.2f}</td>
<td>${r['bb_lower']:.2f}</td>
<td>{r['vol']:.1f}%</td>
<td class="{cls}">{r['rec']}</td>
<td>{r['sentiment']}</td>
<td style="color:{sc_color};font-weight:bold;text-align:center">{r['score']}</td>
</tr>"""

html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Trading Analysis — CoffeeS</title>
<style>
  body {{ background:#0d0d1a; color:#e0e0e0; font-family:'Segoe UI',Arial,sans-serif; padding:20px; }}
  h1 {{ color:#aaaaff; }}
  table {{ border-collapse:collapse; width:100%; }}
  th {{ background:#1e1e3a; color:#8888cc; padding:8px 10px; text-align:left; font-size:12px; border-bottom:2px solid #444; }}
  td {{ padding:6px 10px; border-bottom:1px solid #1a1a2e; font-size:12px; }}
  tr:hover td {{ background:#13132a; }}
  .strong-sell {{ color:#ff4444; font-weight:bold; }}
  .sell {{ color:#ff6666; }}
  .hold {{ color:#ffcc00; }}
  .buy {{ color:#00cc66; }}
  .strong-buy {{ color:#00ff88; font-weight:bold; }}
  .updated {{ color:#444; font-size:11px; }}
</style>
</head>
<body>
<h1>📊 טבלה 1 — trading-analysis (CoffeeS)</h1>
<p class="updated">{len(data)} מניות | מקור: Yahoo Finance</p>
<table>
<thead>
<tr><th>Symbol</th><th>Price</th><th>Change%</th><th>RSI</th><th>SMA20</th><th>SMA50</th><th>MACD</th><th>Signal</th><th>BB+</th><th>BB-</th><th>Vol%</th><th>Rec</th><th>Sentiment</th><th>Score</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>"""

with open('C:/Users/nsyon/SCAN/trading_analysis_coffeeS.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Saved {len(data)} rows with scores")
