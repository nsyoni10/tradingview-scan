---
name: dayscan
description: "Daily stock watchlist scan on TradingView — reads CoffeeL/CoffeeS screeners, fetches data from Yahoo Finance, marks Entry, Stop Loss and Take Profit levels using EMA20/EMA50 with 2:1 R:R ratio"
---

Step 0 — Launch TradingView with CDP

Run via PowerShell:
taskkill /f /im TradingView.exe
Start-Sleep -Seconds 2
Start-Process 'C:\Program Files\WindowsApps\TradingView.Desktop_3.1.0.7818_x64__n534cwy3pjxzj\TradingView.exe' -ArgumentList '--remote-debugging-port=9222','--remote-allow-origins=*'
Start-Sleep -Seconds 12

Verify CDP: Invoke-RestMethod http://localhost:9222/json | Where-Object { $_.url -like "*tradingview*" }

TradingView stays open after dayscan finishes — RunDayscan will use it.

Step 1 — Read symbols from TradingView Screeners via CDP

Write and run this Python script (C:\Users\nsyon\SCAN\step1_screeners.py):

```python
import requests, json, websocket, sys, time, threading
sys.stdout.reconfigure(encoding='utf-8')

pages = requests.get('http://localhost:9222/json').json()
screener_pages = [p for p in pages if 'tradingview.com/screener' in p.get('url','')]
chart_pages    = [p for p in pages if 'tradingview.com/chart'    in p.get('url','')]

def eval_js(ws, js, timeout=15):
    ws.send(json.dumps({'id':1,'method':'Runtime.evaluate',
                        'params':{'expression':js,'returnByValue':True,'awaitPromise':True}}))
    ws.settimeout(timeout)
    try:
        while True:
            msg = json.loads(ws.recv())
            if msg.get('id')==1 and 'result' in msg:
                return msg.get('result',{}).get('result',{}).get('value')
    except: return None

READ_DOM_JS = """
(function() {
    var syms=[], seen={};
    var sel='[class*="tickerCell"] [class*="ticker"],[class*="symbol-"],[data-field-key="name"] a';
    document.querySelectorAll(sel).forEach(function(el){
        var t=el.textContent.trim();
        if(t && /^[A-Z]{1,5}$/.test(t) && !seen[t]){seen[t]=1;syms.push(t);}
    });
    if(syms.length===0){
        document.querySelectorAll('[class*="apply-overflow-tooltip"]').forEach(function(el){
            var t=el.textContent.trim();
            if(t && /^[A-Z]{1,5}$/.test(t) && !seen[t]){seen[t]=1;syms.push(t);}
        });
    }
    return JSON.stringify({count:syms.length,syms:syms});
})()
"""

COFFEEL_SYMS = []
COFFEES_SYMS = []

# Strategy A: use screener-storage API to get IDs, then navigate + read DOM
# API discovered via network monitoring (version=9, limit=100 required)
screener_page = screener_pages[0] if screener_pages else None
if screener_page:
    ws = websocket.create_connection(screener_page['webSocketDebuggerUrl'])
    
    js_api = """
(async function() {
    var BASE = 'https://screener-storage.tradingview.com/screener-storage/api/v2/screens';
    var r = await fetch(BASE+'/?screener_key=stock&version=9&limit=100', {credentials:'include'});
    var list = await r.json();
    var coffeeL = list.find(function(s){return s.title==='CoffeeL';});
    var coffeeS = list.find(function(s){return s.title==='CoffeeS';});
    return JSON.stringify({
        coffeeL_id: coffeeL ? coffeeL.id : null,
        coffeeS_id: coffeeS ? coffeeS.id : null,
        all_titles: list.map(function(s){return s.title;})
    });
})()
"""
    r = eval_js(ws, js_api, 15)
    ws.close()
    
    if r:
        ids = json.loads(r)
        COFFEEL_ID = ids.get('coffeeL_id') or 'OfYmLUqI'  # fallback to known ID
        COFFEES_ID = ids.get('coffeeS_id') or 'oBqGK3SJ'  # fallback to known ID
        print(f"CoffeeL ID: {COFFEEL_ID}, CoffeeS ID: {COFFEES_ID}")
        
        # Navigate screener page to each screener and read DOM
        ws2 = websocket.create_connection(screener_page['webSocketDebuggerUrl'])
        
        for sid, name in [(COFFEEL_ID,'CoffeeL'), (COFFEES_ID,'CoffeeS')]:
            ws2.send(json.dumps({'id':99,'method':'Page.navigate',
                                 'params':{'url':f'https://www.tradingview.com/screener/{sid}/'}}))
            time.sleep(10)
            raw = eval_js(ws2, READ_DOM_JS, 10)
            syms = json.loads(raw).get('syms',[]) if raw else []
            print(f"{name}: {len(syms)} symbols")
            if name == 'CoffeeL': COFFEEL_SYMS = syms
            else: COFFEES_SYMS = syms
        
        ws2.close()

# Fallback to CSV if screeners not found
if not COFFEEL_SYMS:
    try:
        with open('C:/Users/nsyon/SCAN/LONG.CSV') as f:
            COFFEEL_SYMS = [l.strip() for l in f if l.strip()]
        print(f"CoffeeL FALLBACK from LONG.CSV: {len(COFFEEL_SYMS)} symbols")
    except: pass

if not COFFEES_SYMS:
    try:
        with open('C:/Users/nsyon/SCAN/SHORT.CSV') as f:
            COFFEES_SYMS = [l.strip() for l in f if l.strip()]
        print(f"CoffeeS FALLBACK from SHORT.CSV: {len(COFFEES_SYMS)} symbols")
    except: pass

print(f"\nLONG (CoffeeL): {len(COFFEEL_SYMS)} -> {COFFEEL_SYMS[:5]}...")
print(f"SHORT (CoffeeS): {len(COFFEES_SYMS)} -> {COFFEES_SYMS[:5]}...")

with open('C:/Users/nsyon/SCAN/_long_syms.json','w')  as f: json.dump(COFFEEL_SYMS, f)
with open('C:/Users/nsyon/SCAN/_short_syms.json','w') as f: json.dump(COFFEES_SYMS, f)
print("Saved to _long_syms.json / _short_syms.json")
```

Parse result: LONG_SYMBOLS from _long_syms.json, SHORT_SYMBOLS from _short_syms.json

Fallback IDs (hardcoded):
  CoffeeL = OfYmLUqI
  CoffeeS = oBqGK3SJ

Step 2 — Fetch real market data from Yahoo Finance:
Use Python requests with verify=False to fetch data for each symbol:

url = https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1d&range=3mo
headers = {'User-Agent': 'Mozilla/5.0'}
verify = False, timeout = 15
Parse the JSON response:

closes = data['chart']['result'][0]['indicators']['quote'][0]['close'] (filter None values)
highs = data['chart']['result'][0]['indicators']['quote'][0]['high'] (filter None values)
lows = data['chart']['result'][0]['indicators']['quote'][0]['low'] (filter None values)
volumes = data['chart']['result'][0]['indicators']['quote'][0]['volume'] (filter None values)
If fetch fails or data is missing — mark as DATA ERROR and skip.

Step 3 — Calculate indicators:

EMA20: multiplier = 2/21, apply iteratively on last 20 closes
EMA50: multiplier = 2/51, apply iteratively on last 50 closes (or all if fewer)
last close = closes[-1]
avg_volume_20 = average of volumes[-20:]
last_volume = volumes[-1]
volume_ratio = last_volume / avg_volume_20

RSI(14):
  gains = [max(closes[i]-closes[i-1],0) for i in last 14]
  losses = [max(closes[i-1]-closes[i],0) for i in last 14]
  RS = avg(gains)/avg(losses)
  RSI = 100 - 100/(1+RS)

ATR(14):
  true_ranges = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])) for last 14]
  ATR = average(true_ranges)

dist_ema20 = (last_close - EMA20) / EMA20 * 100
dist_ema50 = (last_close - EMA50) / EMA50 * 100

Step 4 — Determine direction:

CoffeeL symbols (LONG): include only if last close > EMA20 AND last close > EMA50
CoffeeS symbols (SHORT): include only if last close < EMA20 AND last close < EMA50
Otherwise → skip

Step 5 — Calculate setup levels:
LONG:

Entry = last close
Stop Loss = min(lows[-3:]) × 0.995
Take Profit = Entry + 2 × (Entry - Stop Loss)
SHORT:

Entry = last close
Stop Loss = max(highs[-3:]) × 1.005
Take Profit = Entry - 2 × (Stop Loss - Entry)
Round all prices to 2 decimal places.
If abs(Entry - SL) < 0.001 → skip (SL too close).

Step 5b — Score each setup (0-100):

LONG score:
  volume_score = min(volume_ratio * 30, 40)
  rsi_score = max(0, min((RSI-50)/50*25, 25))
  trend_score = min(dist_ema20/10*20, 20)
  atr_score = min(ATR/last_close*100/2*15, 15)
  total = volume_score + rsi_score + trend_score + atr_score

SHORT score:
  volume_score = min(volume_ratio * 30, 40)
  rsi_score = max(0, min((50-RSI)/50*25, 25))
  trend_score = min(abs(dist_ema20)/10*20, 20)
  atr_score = min(ATR/last_close*100/2*15, 15)
  total = volume_score + rsi_score + trend_score + atr_score

Select TOP 5 LONG and TOP 5 SHORT by score.

Step 6 — Save results as HTML:
Save to C:\Users\nsyon\SCAN\dayscan_results.html with:

SECTION A — TOP PICKS (appears first, above all tables):
  Two side-by-side cards: "🏆 TOP 5 LONG" and "🏆 TOP 5 SHORT"
  Each card shows ranked list (1-5) with:
    - Rank + Symbol (bold)
    - Score out of 100 (colored bar)
    - One-line reason: e.g. "Volume ×2.3 | RSI 67 | +4.2% above EMA20"
  Style: dark card, green border for LONG, red border for SHORT

SECTION B — Summary cards:
  Total / LONG count / SHORT count

SECTION C — Full tables:
  Two separate tables: LONG Setups and SHORT Setups
  Columns: Symbol, Direction, Entry, Stop Loss, Take Profit, R:R
  Each row must include: data-symbol, data-entry, data-sl, data-tp
  TOP 5 rows get a ⭐ star badge next to symbol name

SECTION D — Errors:
  List failed symbols at bottom

Show scan date/time and "Data: Yahoo Finance | Source: TradingView Screeners (CoffeeL/CoffeeS)" at the top.
Display the file path when done.
