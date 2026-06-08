# -*- coding: utf-8 -*-
# tv_draw_pivot.py — draws level lines from _drawings_data.json on TradingView charts
import json, websocket, urllib.request, time, sys
sys.stdout.reconfigure(encoding="utf-8")

with open("C:/Users/nsyon/SCAN/_drawings_data.json") as f:
    data = json.load(f)

all_stocks = data["long"] + data["short"]
print(f"Drawing levels for {len(all_stocks)} stocks...")

pages = json.loads(urllib.request.urlopen("http://localhost:9222/json").read())
page = next(p for p in pages if "tradingview.com" in p.get("url",""))
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=20, header={"Origin":"http://localhost"})

mid = [1]

def run_js(code):
    m = mid[0]; mid[0] += 1
    ws.send(json.dumps({"id":m,"method":"Runtime.evaluate","params":{"expression":code,"returnByValue":True,"awaitPromise":True}}))
    for _ in range(60):
        r = json.loads(ws.recv())
        if r.get("id") == m:
            return r.get("result",{}).get("result",{}).get("value","")
    return "timeout"

def navigate(url):
    m = mid[0]; mid[0] += 1
    ws.send(json.dumps({"id":m,"method":"Page.navigate","params":{"url":url}}))
    for _ in range(30):
        r = json.loads(ws.recv())
        if r.get("id") == m:
            return True
    return False

def wait_widget(maxwait=20):
    for _ in range(maxwait):
        r = run_js("""(function(){var w=window;for(var k in w){try{if(w[k]&&typeof w[k].activeChart==='function')return 'ready';}catch(e){}}return 'not_ready';})()""")
        if r == "ready":
            return True
        time.sleep(1)
    return False

COLOR_MAP = {"red":"#D85A30","green":"#1D9E75","blue":"#185FA5"}

ws.send(json.dumps({"id":999,"method":"Page.enable","params":{}}))
ws.recv()

for stock in all_stocks:
    sym = stock["symbol"]
    levels = stock["levels"]
    print(f"\n[{sym}] Navigating...")
    navigate(f"https://www.tradingview.com/chart/?symbol={sym}")
    time.sleep(8)
    if not wait_widget(maxwait=15):
        print(f"  SKIP: widget not ready")
        continue
    time.sleep(2)

    js_lines = ""
    for lv in levels:
        p = lv["price"]
        label = lv["label"].replace("'","\\'")
        color = COLOR_MAP.get(lv["color"], "#888888")
        js_lines += f"\n    chart.createShape({{price:{p}}},{{shape:'horizontal_line',text:'{label}',overrides:{{linecolor:'{color}',linewidth:2,showLabel:true,textcolor:'{color}'}}}});"

    result = run_js(f"""(function(){{
  try{{
    var w=window,widget=null;
    for(var k in w){{try{{if(w[k]&&typeof w[k].activeChart==='function'){{widget=w[k];break;}}}}catch(e){{}}}}
    if(!widget)return 'no_widget';
    var chart=widget.activeChart();
    {js_lines}
    return 'ok:{len(levels)}lines';
  }}catch(e){{return 'err:'+e.message;}}
}})()""")
    print(f"  draw: {result}")

    time.sleep(3)
    save = run_js("""(function(){try{var w=window,widget=null;for(var k in w){try{if(w[k]&&typeof w[k].activeChart==='function'){widget=w[k];break;}}catch(e){}}if(!widget)return 'no_widget';if(typeof widget.saveChartToServer==='function'){widget.saveChartToServer(null,null,{});return 'saved';}if(typeof widget.save==='function'){widget.save(function(){});return 'saved';}return 'no_save_fn';}catch(e){return 'err:'+e.message;}})()""")
    print(f"  save: {save}")
    time.sleep(2)

ws.close()
print("\nAll drawings complete.")
