import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('C:/Users/nsyon/SCAN/_scan_results.json') as f:
    data = json.load(f)

long_results  = data['long']
short_results = data['short']
top5_long     = data['top5_long']
top5_short    = data['top5_short']
errors        = data['errors']
skipped       = data['skipped']
scan_time     = data['scan_time']

top5_long_syms  = {r['symbol'] for r in top5_long}
top5_short_syms = {r['symbol'] for r in top5_short}

def score_bar(score):
    color = '#22c55e' if score >= 65 else '#f59e0b' if score >= 45 else '#ef4444'
    return f'''<div style="background:#1e293b;border-radius:4px;height:8px;width:100%;margin-top:4px">
        <div style="background:{color};border-radius:4px;height:8px;width:{min(score,100):.0f}%"></div></div>'''

def reason_line(r):
    d = r['direction']
    vol = f"Vol ×{r['vol_ratio']:.1f}"
    rsi = f"RSI {r['rsi']:.0f}"
    dist = f"{'+'if r['dist_ema20']>0 else ''}{r['dist_ema20']:.1f}% vs EMA20"
    return f"{vol} | {rsi} | {dist}"

def top5_card(items, title, border_color, text_color):
    rows = ''
    for i, r in enumerate(items, 1):
        medal = ['🥇','🥈','🥉','4️⃣','5️⃣'][i-1]
        rows += f'''
        <div style="display:flex;justify-content:space-between;align-items:flex-start;padding:10px 0;border-bottom:1px solid #1e293b">
            <div>
                <span style="font-size:1.1em">{medal}</span>
                <strong style="color:#f1f5f9;margin-left:6px;font-size:1.05em">{r['symbol']}</strong>
                <div style="color:#94a3b8;font-size:0.78em;margin-top:3px">{reason_line(r)}</div>
                {score_bar(r['score'])}
            </div>
            <span style="color:{text_color};font-weight:700;font-size:1.1em;margin-left:12px">{r['score']:.0f}</span>
        </div>'''
    return f'''
    <div style="background:#0f172a;border:2px solid {border_color};border-radius:12px;padding:20px;flex:1;min-width:300px">
        <h3 style="color:{text_color};margin:0 0 12px 0;font-size:1.15em">{title}</h3>
        {rows}
    </div>'''

def table_rows(items, top_syms, direction):
    color = '#22c55e' if direction == 'LONG' else '#ef4444'
    rows = ''
    for r in items:
        star = ' ⭐' if r['symbol'] in top_syms else ''
        rows += f'''<tr>
            <td data-symbol="{r['symbol']}" style="font-weight:600;color:{color}">{r['symbol']}{star}</td>
            <td style="color:{color}">{direction}</td>
            <td data-entry="{r['entry']}">{r['entry']}</td>
            <td data-sl="{r['sl']}" style="color:#ef4444">{r['sl']}</td>
            <td data-tp="{r['tp']}" style="color:#22c55e">{r['tp']}</td>
            <td>{r['rr']:.1f}:1</td>
            <td>
                <div style="display:flex;align-items:center;gap:6px">
                    <span style="color:#f1f5f9;font-weight:600">{r['score']:.0f}</span>
                    <div style="background:#1e293b;border-radius:3px;height:6px;width:60px">
                        <div style="background:{'#22c55e' if r['score']>=65 else '#f59e0b' if r['score']>=45 else '#ef4444'};border-radius:3px;height:6px;width:{min(r['score'],100):.0f}%"></div>
                    </div>
                </div>
            </td>
        </tr>'''
    return rows

html = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DayScan — {scan_time}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #020617; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 20px; }}
  h2 {{ color: #f1f5f9; }}
  .header {{ background: #0f172a; border-radius: 12px; padding: 16px 24px; margin-bottom: 20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
  .header h1 {{ font-size: 1.4em; color: #38bdf8; }}
  .header small {{ color: #64748b; font-size: 0.85em; }}
  .summary {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .card {{ background: #0f172a; border-radius: 10px; padding: 14px 20px; flex: 1; min-width: 120px; text-align: center; }}
  .card .num {{ font-size: 2em; font-weight: 700; }}
  .card .lbl {{ color: #64748b; font-size: 0.85em; margin-top: 4px; }}
  .top-cards {{ display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }}
  table {{ width: 100%; border-collapse: collapse; background: #0f172a; border-radius: 10px; overflow: hidden; margin-bottom: 28px; }}
  th {{ background: #1e293b; color: #94a3b8; font-size: 0.8em; padding: 10px 14px; text-align: right; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }}
  td {{ padding: 10px 14px; border-bottom: 1px solid #1e293b; font-size: 0.9em; text-align: right; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #1a2438; }}
  h2 {{ font-size: 1.1em; color: #94a3b8; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #1e293b; }}
  .section {{ margin-bottom: 28px; }}
  .errors {{ background: #0f172a; border-radius: 10px; padding: 16px; font-size: 0.85em; color: #64748b; }}
  .errors div {{ padding: 3px 0; }}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>📊 DayScan</h1>
    <small>סרוק בתאריך: {scan_time} &nbsp;|&nbsp; מקור: TradingView Screeners (CoffeeL / CoffeeS) &nbsp;|&nbsp; נתונים: Yahoo Finance</small>
  </div>
  <div style="text-align:left">
    <small style="color:#64748b">LONG: CoffeeL &nbsp;|&nbsp; SHORT: CoffeeS</small>
  </div>
</div>

<!-- SECTION B: Summary -->
<div class="summary">
  <div class="card">
    <div class="num" style="color:#38bdf8">{len(long_results)+len(short_results)}</div>
    <div class="lbl">סה"כ סטאפים</div>
  </div>
  <div class="card">
    <div class="num" style="color:#22c55e">{len(long_results)}</div>
    <div class="lbl">LONG</div>
  </div>
  <div class="card">
    <div class="num" style="color:#ef4444">{len(short_results)}</div>
    <div class="lbl">SHORT</div>
  </div>
  <div class="card">
    <div class="num" style="color:#94a3b8">{len(errors)}</div>
    <div class="lbl">שגיאות</div>
  </div>
</div>

<!-- SECTION A: Top Picks -->
<div class="section">
  <h2>🏆 TOP PICKS</h2>
  <div class="top-cards">
    {top5_card(top5_long, '🏆 TOP 5 LONG', '#22c55e', '#22c55e')}
    {top5_card(top5_short, '🏆 TOP 5 SHORT', '#ef4444', '#ef4444')}
  </div>
</div>

<!-- SECTION C: Full Tables -->
<div class="section">
  <h2>📈 LONG Setups ({len(long_results)})</h2>
  <table>
    <thead><tr>
      <th>סמל</th><th>כיוון</th><th>Entry</th><th>Stop Loss</th><th>Take Profit</th><th>R:R</th><th>Score</th>
    </tr></thead>
    <tbody>
      {table_rows(long_results, top5_long_syms, 'LONG')}
    </tbody>
  </table>
</div>

<div class="section">
  <h2>📉 SHORT Setups ({len(short_results)})</h2>
  <table>
    <thead><tr>
      <th>סמל</th><th>כיוון</th><th>Entry</th><th>Stop Loss</th><th>Take Profit</th><th>R:R</th><th>Score</th>
    </tr></thead>
    <tbody>
      {table_rows(short_results, top5_short_syms, 'SHORT')}
    </tbody>
  </table>
</div>

<!-- SECTION D: Errors -->
<div class="section">
  <h2>⚠️ שגיאות ודילוגים ({len(errors)} שגיאות, {len(skipped)} דילוגים)</h2>
  <div class="errors">
    {''.join(f'<div>❌ {e["symbol"]}: {e["error"]}</div>' for e in errors)}
    {''.join(f'<div>⏭ {s["symbol"]}: {s["reason"]}</div>' for s in skipped[:10])}
  </div>
</div>

<div style="color:#334155;font-size:0.75em;text-align:center;padding:20px 0">
  C:\\Users\\nsyon\\SCAN\\dayscan_results.html &nbsp;|&nbsp; DayScan Auto-Generated
</div>

</body></html>'''

out_path = 'C:/Users/nsyon/SCAN/dayscan_results.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ HTML saved: {out_path}")
print(f"   LONG: {len(long_results)} setups | SHORT: {len(short_results)} setups")
print(f"   TOP 5 LONG:  {[r['symbol'] for r in top5_long]}")
print(f"   TOP 5 SHORT: {[r['symbol'] for r in top5_short]}")
