# -*- coding: utf-8 -*-
# tv_mark_charts_pivot.py — draws colored lines from us-stock-analysis data
import json, websocket, urllib.request, time, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

today = datetime.now().strftime("%d.%m.%Y")

# Read TOP 10 from JSON files
try:
    with open("C:/Users/nsyon/SCAN/_top10_long.json") as f:
        top_long = json.load(f)
except:
    top_long = []

try:
    with open("C:/Users/nsyon/SCAN/_top10_short.json") as f:
        top_short = json.load(f)
except:
    top_short = []

stocks = []
for s in top_long:
    s['dir'] = 'LONG'
    stocks.append(s)
for s in top_short:
    s['dir'] = 'SHORT'
    stocks.append(s)

print(f"Loaded {len(stocks)} stocks: {[s['symbol'] for s in stocks]}")

if not stocks:
    print("No stocks to process.")
    sys.exit(0)

pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
page = next(p for p in pages if 'tradingview.com' in p.get('url',''))
ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=15, header={"Origin": "http://localhost"})

msg_id = [1]

def run_js(code):
    mid = msg_id[0]; msg_id[0] += 1
    ws.send(json.dumps({"id":mid,"method":"Runtime.evaluate","params":{"expression":code,"returnByValue":True,"awaitPromise":True}}))
    for _ in range(60):
        r = json.loads(ws.recv())
        if r.get('id') == mid:
            return r.get('result',{}).get('result',{}).get('value','')
    return 'timeout'

def navigate(url):
    mid = msg_id[0]; msg_id[0] += 1
    ws.send(json.dumps({"id":mid,"method":"Page.navigate","params":{"url":url}}))
    for _ in range(30):
        r = json.loads(ws.recv())
        if r.get('id') == mid:
            return True
    return False

def wait_for_widget(max_wait=20):
    for _ in range(max_wait):
        r = run_js("""
(function(){
  var w = window;
  for(var k in w){
    try{ if(w[k] && typeof w[k].activeChart==='function') return 'ready'; }catch(e){}
  }
  return 'not_ready';
})()
""")
        if r == 'ready':
            return True
        time.sleep(1)
    return False

ws.send(json.dumps({"id":999,"method":"Page.enable","params":{}}))
ws.recv()

for s in stocks:
    sym = s['symbol']
    print(f"Processing {sym}...")
    navigate(f"https://www.tradingview.com/chart/?symbol={sym}")
    time.sleep(8)

    ready = wait_for_widget(max_wait=15)
    if not ready:
        print(f"  SKIP: widget not ready for {sym}")
        continue

    time.sleep(2)

    # Build lines from the stock data
    lines = []

    # Red lines — Support
    if s.get('s_near'):
        lines.append({'price': s['s_near'], 'label': f"Support Near ${s['s_near']}", 'color': '#D85A30'})
    if s.get('s_strong'):
        lines.append({'price': s['s_strong'], 'label': f"Support Strong ${s['s_strong']}", 'color': '#D85A30'})
    if s.get('s_main'):
        lines.append({'price': s['s_main'], 'label': f"Support Main ${s['s_main']}", 'color': '#D85A30'})

    # Green lines — Target/Entry
    if s.get('r_near'):
        lines.append({'price': s['r_near'], 'label': f"R Near ${s['r_near']}", 'color': '#1D9E75'})
    if s.get('entry_long_agg'):
        lines.append({'price': s['entry_long_agg'], 'label': f"Entry Aggressive ${s['entry_long_agg']}", 'color': '#1D9E75'})
    if s.get('entry_long_con'):
        lines.append({'price': s['entry_long_con'], 'label': f"Entry Conservative ${s['entry_long_con']}", 'color': '#1D9E75'})
    if s.get('short_target'):
        lines.append({'price': s['short_target'], 'label': f"Short Target ${s['short_target']}", 'color': '#1D9E75'})
    if s.get('short_opp'):
        lines.append({'price': s['short_opp'], 'label': f"Short Entry ${s['short_opp']}", 'color': '#1D9E75'})

    # Blue lines — Resistance, 52W
    if s.get('r_upper'):
        lines.append({'price': s['r_upper'], 'label': f"R Upper ${s['r_upper']}", 'color': '#185FA5'})
    if s.get('w52_high'):
        lines.append({'price': s['w52_high'], 'label': f"52W High ${s['w52_high']}", 'color': '#185FA5'})
    if s.get('w52_low'):
        lines.append({'price': s['w52_low'], 'label': f"52W Low ${s['w52_low']}", 'color': '#185FA5'})

    if not lines:
        print(f"  SKIP: no levels for {sym}")
        continue

    # Build JS to draw all lines
    js_lines = ""
    for line in lines:
        price = line['price']
        label = line['label']
        color = line['color']
        js_lines += f"""
    chart.createShape({{price:{price}}}, {{shape:'horizontal_line', text:'{label}', overrides:{{linecolor:'{color}',linewidth:2,showLabel:true,textcolor:'{color}'}}}});"""

    result = run_js(f"""
(function(){{
  try {{
    var w = window, widget = null;
    for (var k in w) {{
      try {{ if (w[k] && typeof w[k].activeChart === 'function') {{ widget = w[k]; break; }} }} catch(e) {{}}
    }}
    if (!widget) return 'no_widget';
    var chart = widget.activeChart();
    {js_lines}
    return 'ok';
  }} catch(e) {{ return 'err:'+e.message; }}
}})()
""")
    print(f"  draw : {result} ({len(lines)} lines)")

    time.sleep(3)
    save = run_js("""
(function(){
  try {
    var w = window, widget = null;
    for (var k in w) {
      try { if (w[k] && typeof w[k].activeChart === 'function') { widget = w[k]; break; } } catch(e) {}
    }
    if (!widget) return 'no_widget';
    if (typeof widget.saveChartToServer === 'function') {
      widget.saveChartToServer(null, null, {});
      return 'saved';
    }
    if (typeof widget.save === 'function') { widget.save(function(){}); return 'saved'; }
    return 'no_save_fn';
  } catch(e) { return 'err:'+e.message; }
})()
""")
    print(f"  save : {save}")
    time.sleep(2)

ws.close()
print("\nAll done.")
