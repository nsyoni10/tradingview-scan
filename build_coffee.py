import json, sys, requests, warnings
from datetime import datetime
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding='utf-8')

now = datetime.now().strftime("%Y-%m-%d %H:%M")
H = {"User-Agent": "Mozilla/5.0"}

def fetch(sym):
    try:
        u = "https://query1.finance.yahoo.com/v8/finance/chart/"+sym+"?interval=1d&range=5d"
        m = requests.get(u,headers=H,verify=False,timeout=15).json()["chart"]["result"][0]["meta"]
        p = m.get("regularMarketPrice") or m.get("previousClose",0)
        c = m.get("chartPreviousClose") or m.get("regularMarketPreviousClose") or m.get("previousClose",p)
        if not p or p==0: return {"p":0,"chg":0,"ok":False}
        chg = round((p-c)/c*100,2) if c and c!=0 else 0
        return {"p":round(p,2),"chg":chg,"ok":True}
    except:
        return {"p":0,"chg":0,"ok":False}

def pct_color(v, inv=False):
    if inv: return "#ff4444" if v>=0 else "#00cc66"
    return "#00cc66" if v>=0 else "#ff4444"

def ic(v, inv=False):
    if inv: return "✅" if v<18 else ("⚠️" if v<25 else "❌")
    return "✅" if v>=0.3 else ("⚠️" if v>=-0.3 else "❌")

# Fetch market data
print("מביא נתוני שוק...")
sp   = fetch("^GSPC")
qq   = fetch("QQQ")
vx   = fetch("^VIX")
ol   = fetch("CL=F")
gold = fetch("GC=F")
bond = fetch("^TNX")
es   = fetch("ES=F")
nq   = fetch("NQ=F")
ym   = fetch("YM=F")
rty  = fetch("RTY=F")
print(f"S&P:{sp['p']} | QQQ:{qq['p']} | VIX:{vx['p']} | נפט:{ol['p']} | זהב:{gold['p']} | אגח:{bond['p']}%")
print(f"ES:{es['p']}({es['chg']:+.2f}%) | NQ:{nq['p']}({nq['chg']:+.2f}%) | YM:{ym['p']}({ym['chg']:+.2f}%) | RTY:{rty['p']}({rty['chg']:+.2f}%)")

# Read data - generic
try:
    with open('C:/Users/nsyon/SCAN/_trading_analysis_long.json') as f:
        long_data = json.load(f)
except:
    long_data = []

try:
    with open('C:/Users/nsyon/SCAN/_trading_analysis_short.json') as f:
        short_data = json.load(f)
except:
    short_data = []

# Read TOP 10 symbols for highlighting
try:
    with open('C:/Users/nsyon/SCAN/_top10_long.json') as f:
        top10_long_syms = [r['symbol'] for r in json.load(f)]
except:
    top10_long_syms = []

try:
    with open('C:/Users/nsyon/SCAN/_top10_short.json') as f:
        top10_short_syms = [r['symbol'] for r in json.load(f)]
except:
    top10_short_syms = []

# Hebrew field names map
field_he = {
    'symbol': 'טיקר', 'score': 'ציון', 'sentiment': 'סנטימנט', 'rec': 'המלצה',
    'price': 'מחיר', 'change_pct': 'שינוי%', 'rsi': 'RSI', 'vol': 'תנודתיות%',
    'sma20': 'ממוצע 20', 'sma50': 'ממוצע 50', 'bb_upper': 'בולינגר+', 'bb_lower': 'בולינגר-',
    'macd': 'MACD', 'signal': 'סיגנל'
}

def build_table(data, title, color, border, top_syms=None):
    if not data:
        return f'<div style="color:#666">אין נתונים</div>'

    if top_syms is None:
        top_syms = []

    # Sort: TOP selected first (in selection order), then rest
    top_map = {r['symbol']: r for r in data if r.get('symbol') in top_syms}
    top_rows = [top_map[s] for s in top_syms if s in top_map]
    other_rows = [r for r in data if r.get('symbol') not in top_syms]
    sorted_data = top_rows + other_rows

    all_f = list(data[0].keys())
    priority = ['symbol', 'score', 'sentiment', 'rec']
    fields = [f for f in priority if f in all_f] + [f for f in all_f if f not in priority]

    headers = ''.join(f'<th>{field_he.get(f, f)}</th>' for f in fields)
    en_fields = {'symbol','price','change_pct','rsi','sma20','sma50','bb_upper','bb_lower','macd','signal','vol','score','rec'}

    rows = ''
    for r in sorted_data:
        is_top = r.get('symbol') in top_syms
        row_style = 'background:#1a1a10;' if is_top else ''
        cells = ''
        for f in fields:
            val = r.get(f, '')
            style = ''
            if f == 'symbol':
                sym_color = '#ffff00' if is_top else color
                style = f'font-weight:bold;color:{sym_color}'
            elif f == 'score':
                sc = val
                sc_color = '#00ff88' if sc >= 3 else '#00cc66' if sc >= 1 else '#ffcc00' if sc == 0 else '#ff6666' if sc >= -2 else '#ff4444'
                style = f'color:{sc_color};font-weight:bold;text-align:center'
                if is_top:
                    style += ';background:#1a1a10'
            elif f == 'rec':
                cls = 'strong-sell' if val == 'STRONG SELL' else 'sell' if val == 'SELL' else 'hold' if val == 'HOLD' else 'buy' if val == 'BUY' else 'strong-buy'
                style = f'class-placeholder:{cls}'
            elif f == 'price':
                val = f'${val}'
            elif f == 'change_pct':
                val = f'{val:+}%' if isinstance(val, (int, float)) else val
            elif f in ('sma20', 'sma50', 'bb_upper', 'bb_lower'):
                val = f'${val}' if isinstance(val, (int, float)) else val
            elif f == 'vol':
                val = f'{val}%' if isinstance(val, (int, float)) else val

            top_td_style = f'color:#ffff00;' if is_top and f != 'symbol' and f != 'score' and 'class-placeholder' not in style else ''
            dir_attr = ' dir="ltr" lang="en"' if f in en_fields else ' dir="auto"'
            if 'class-placeholder' in style:
                cls = style.split(':')[1]
                td_style = f' style="{top_td_style}"' if top_td_style else ''
                cells += f'<td class="{cls}"{dir_attr}{td_style}>{val}</td>'
            elif style:
                cells += f'<td style="{top_td_style}{style}"{dir_attr}>{val}</td>'
            else:
                cells += f'<td style="{top_td_style}"{dir_attr}>{val}</td>'

        sep = '<td colspan="99" style="height:1px;background:#444;padding:0"></td>' if is_top and r == top_rows[-1] else ''
        rows += f'<tr style="{row_style}">{cells}</tr>\n'
        if sep and r == top_rows[-1]:
            rows += f'<tr>{sep}</tr>\n'

    return f'''
    <div class="C">
      <div class="ST">{title}</div>
      <div class="table-wrap">
        <table>
          <thead><tr>{headers}</tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>'''

# Read morning note if exists
morning_note = ''
try:
    with open('C:/Users/nsyon/SCAN/dayscan_pivot_notes.html', encoding='utf-8') as f:
        notes_content = f.read()
    morning_note = '<div class="C"><div class="ST">📝 הערות ריצה</div><iframe src="dayscan_pivot_notes.html" style="width:100%;height:400px;border:1px solid #333;border-radius:8px;background:#0d0d1a"></iframe></div>'
except:
    pass

# Morning note content
morning_note_text = f'''
<div class="C">
  <div class="ST">📰 סיכום בוקר</div>
  <p><b>🔴 כותרת ראשית: שבבים נחתכים — Broadcom ‏-15%, CrowdStrike ‏-9%</b></p>
  <p>Broadcom החמיצה צפיות הכנסות למרות beat ב-EPS.‏ CrowdStrike ירדה 9% למרות beat + פיצול 4:1.</p>
  <p><b>התפתחויות לילה / פרה-מרקט:</b></p>
  <p>• AVGO:‏ ‏-15% — החמצת הכנסות, הכנסות AI צפויות +200%<br>
  • CRWD:‏ ‏-9% — beat + פיצול 4:1<br>
  • WOOF:‏ ‏-12% — דוחות תואמי ציפיות, אכזבה<br>
  • מאקרו: פרודוקטיביות Q1 תוקנה ל-0.3% (צפי 0.8%)</p>
  <p><b>אירועים מרכזיים היום:</b></p>
  <p>• 08:30 ET: דוח תעסוקה מאי — צפי 85,000 משרות<br>
  • 08:30 ET: שיעור אבטלה + שכר</p>
  <p><b>רעיונות מסחר:</b></p>
  <p>• שורט שבבים — סנטימנט שלילי אחרי AVGO<br>
  • סיכון: דוח תעסוקה חזק מהצפי יכול להפוך כיוון</p>
</div>'''

# Futures table
FUTURES = [
    ("ES=F", es, "S&P 500 עתידי", "כיוון כללי — פתיחת שוק"),
    ("NQ=F", nq, 'נאסד"ק עתידי', "כיוון מניות הטכנולוגיה"),
    ("YM=F", ym, "דאו ג'ונס עתידי", "שוק מסורתי — בנקים ותעשייה"),
    ("RTY=F", rty, "ראסל 2000 עתידי", "מד סיכון — מניות קטנות"),
]
fut_rows = ""
for sym_, d_, name_, desc_ in FUTURES:
    clr = pct_color(d_["chg"])
    p_s = f"${d_['p']:,}" if d_["ok"] else "N/A"
    c_s = f"{d_['chg']:+.2f}%" if d_["ok"] else "N/A"
    fut_rows += f"<tr><td style='font-weight:bold;color:#aaaaff;font-size:16px'>{sym_}</td><td>{name_}</td><td style='font-weight:bold'>{p_s}</td><td style='font-weight:bold;color:{clr}'>{c_s}</td><td style='font-size:12px;color:#888'>{desc_}</td></tr>"

html = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>☕ Coffee — {now}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Segoe UI,Arial,sans-serif;background:#0d0d1a;color:#e0e0e0;padding:24px;direction:rtl}}
.C{{background:#12122a;border-radius:14px;padding:20px 24px;margin-bottom:20px}}
.ST{{font-size:16px;color:#8888cc;font-weight:bold;margin-bottom:14px;border-bottom:1px solid #333;padding-bottom:6px}}
.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.metric{{background:#1a1a2e;border-radius:10px;padding:14px;text-align:center}}
.mp{{font-size:26px;font-weight:bold;margin-bottom:4px}}
.mc{{font-size:16px;font-weight:bold;margin-bottom:4px}}
.ml{{font-size:14px;color:#e0e0e0;margin-top:2px;font-weight:bold}}
.table-wrap{{overflow-x:auto;max-width:100%}}
table{{width:100%;border-collapse:collapse}}
th{{background:#1e1e3a;color:#8888cc;padding:10px 14px;text-align:right;font-size:12px;border-bottom:1px solid #333}}
td{{padding:10px 14px;border-bottom:1px solid #1a1a2a;font-size:13px;text-align:right}}
tr:hover td{{background:#1a1a2a}}
.strong-sell{{color:#ff4444;font-weight:bold}}
.sell{{color:#ff6666}}
.hold{{color:#ffcc00}}
.buy{{color:#00cc66}}
.strong-buy{{color:#00ff88;font-weight:bold}}
p{{color:#ccc;font-size:13px;line-height:1.8;margin-bottom:8px}}
</style>
</head>
<body>

<!-- כותרת -->
<div class="C">
  <div style="font-size:30px;font-weight:bold;color:#aaaaff">☕ Coffee — סריקת בוקר</div>
  <div style="font-size:13px;color:#555;margin-top:6px">{now} | מקורות: trading-analysis · us-stock-analysis · dayscan_pivot · Yahoo Finance</div>
</div>

<!-- מדדים -->
<div class="C">
  <div class="ST">📊 מדדים מרכזיים</div>
  <div class="metrics">
    <div class="metric">
      <div class="mp">${sp['p']:,}</div>
      <div class="mc" style="color:{pct_color(sp['chg'])}">{sp['chg']:+.2f}%</div>
      <div class="ml">מדד S&P 500 {ic(sp['chg'])}</div>
    </div>
    <div class="metric">
      <div class="mp">${qq['p']:,}</div>
      <div class="mc" style="color:{pct_color(qq['chg'])}">{qq['chg']:+.2f}%</div>
      <div class="ml">נאסד"ק QQQ {ic(qq['chg'])}</div>
    </div>
    <div class="metric">
      <div class="mp">{vx['p']}</div>
      <div class="mc" style="color:{pct_color(vx['chg'], inv=True)}">{vx['chg']:+.2f}%</div>
      <div class="ml">VIX — מדד פחד {ic(vx['p'], inv=True)}</div>
    </div>
    <div class="metric">
      <div class="mp">${ol['p']:,}</div>
      <div class="mc" style="color:{pct_color(ol['chg'])}">{ol['chg']:+.2f}%</div>
      <div class="ml">🛢️ נפט גולמי</div>
    </div>
    <div class="metric">
      <div class="mp">${gold['p']:,}</div>
      <div class="mc" style="color:{pct_color(gold['chg'])}">{gold['chg']:+.2f}%</div>
      <div class="ml">🥇 זהב</div>
    </div>
    <div class="metric">
      <div class="mp">{bond['p']}%</div>
      <div class="mc" style="color:{pct_color(bond['chg'], inv=True)}">{bond['chg']:+.2f}%</div>
      <div class="ml">📊 אגח 10Y</div>
    </div>
  </div>
</div>

<!-- חוזים עתידיים -->
<div class="C">
  <div class="ST">⚡ חוזים עתידיים</div>
  <table>
    <thead><tr><th>טיקר</th><th>שם</th><th>מחיר</th><th>שינוי</th><th>למה חשוב</th></tr></thead>
    <tbody>{fut_rows}</tbody>
  </table>
</div>

<!-- סיכום בוקר -->
{morning_note_text}

<!-- טבלאות -->
{build_table(long_data, '🟢 לונג — TOP', '#00cc66', '#00cc66', top10_long_syms)}
{build_table(short_data, '🔴 שורט — TOP', '#ff4444', '#ff4444', top10_short_syms)}

<!-- הערות -->
{morning_note}

<div style="text-align:center;color:#333;font-size:11px;margin-top:10px">
  ☕ Coffee | {now} | trading-analysis · us-stock-analysis · Yahoo Finance
</div>
</body>
</html>'''

with open('C:/Users/nsyon/SCAN/coffee_pivot.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Verify
all_fields = list(long_data[0].keys()) if long_data else list(short_data[0].keys()) if short_data else []
print(f"LONG: {len(long_data)} records, {len(long_data[0].keys()) if long_data else 0} fields")
print(f"SHORT: {len(short_data)} records, {len(short_data[0].keys()) if short_data else 0} fields")
print(f"Fields: {all_fields}")
print(f"Saved: coffee_pivot.html")
