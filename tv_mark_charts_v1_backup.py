# -*- coding: utf-8 -*-
import json, websocket, urllib.request, time, sys, re
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

today = datetime.now().strftime("%d.%m.%Y")

# TOP 10 LONG + TOP 10 SHORT — קורא אוטומטי מ-dayscan_results.html
with open("C:/Users/nsyon/SCAN/dayscan_results.html", encoding="utf-8") as f:
    html = f.read()

top_long = re.findall(
    r'<tr data-symbol="([^"]+)" data-entry="([^"]+)" data-sl="([^"]+)" data-tp="([^"]+)">\s*<td[^>]*color:#00cc66[^>]*>⭐',
    html
)
top_short = re.findall(
    r'<tr data-symbol="([^"]+)" data-entry="([^"]+)" data-sl="([^"]+)" data-tp="([^"]+)">\s*<td[^>]*color:#ff4444[^>]*>⭐',
    html
)

stocks = []
for m in top_long[:10]:
    stocks.append({"symbol": m[0], "dir": "LONG",  "entry": float(m[1]), "sl": float(m[2]), "tp": float(m[3])})
for m in top_short[:10]:
    stocks.append({"symbol": m[0], "dir": "SHORT", "entry": float(m[1]), "sl": float(m[2]), "tp": float(m[3])})

print(f"Loaded {len(stocks)} stocks: {[s['symbol'] for s in stocks]}")

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
    """ממתין עד שה-widget מוכן"""
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
    print(f"Processing {s['symbol']}...")
    navigate(f"https://www.tradingview.com/chart/?symbol={s['symbol']}")
    time.sleep(8)

    # ממתין עד שה-widget מוכן
    ready = wait_for_widget(max_wait=15)
    if not ready:
        print(f"  SKIP: widget not ready for {s['symbol']}")
        continue

    time.sleep(2)  # עוד המתנה לאחר טעינה

    # Draw Entry / Stop Loss / Take Profit lines
    result = run_js(f"""
(function(){{
  try {{
    var w = window, widget = null;
    for (var k in w) {{
      try {{ if (w[k] && typeof w[k].activeChart === 'function') {{ widget = w[k]; break; }} }} catch(e) {{}}
    }}
    if (!widget) return 'no_widget';
    var chart = widget.activeChart();
    chart.removeAllShapes();
    chart.createShape({{price:{s['entry']}}}, {{shape:'horizontal_line', text:'Entry - {s["dir"]} | {today}', overrides:{{linecolor:'#1D9E75',linewidth:2,showLabel:true,textcolor:'#1D9E75'}}}});
    chart.createShape({{price:{s['sl']}}},    {{shape:'horizontal_line', text:'Stop Loss',                    overrides:{{linecolor:'#D85A30',linewidth:2,showLabel:true,textcolor:'#D85A30'}}}});
    chart.createShape({{price:{s['tp']}}},    {{shape:'horizontal_line', text:'Take Profit',                  overrides:{{linecolor:'#185FA5',linewidth:2,showLabel:true,textcolor:'#185FA5'}}}});
    return 'ok';
  }} catch(e) {{ return 'err:'+e.message; }}
}})()
""")
    print(f"  draw : {result}")

    # Save to server before navigating away
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
