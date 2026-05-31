# -*- coding: utf-8 -*-
import json, websocket, urllib.request, time, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')

from tv_switch_dayscan import connect_tv, switch_to_dayscan, make_runner

# ─── STEP א — Connect to TradingView Desktop ────────────────────────────────
print("STEP א — מתחבר ל-TradingView Desktop...")
ws = connect_tv()

msg_id = [1]

def run_js(code, await_promise=False, timeout=20):
    mid = msg_id[0]; msg_id[0] += 1
    ws.send(json.dumps({"id":mid,"method":"Runtime.evaluate","params":{"expression":code,"returnByValue":True,"awaitPromise":await_promise}}))
    ws.settimeout(timeout)
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get('id') == mid:
                return r.get('result',{}).get('result',{}).get('value','')
        except: break
    return 'timeout'

def send_cmd(method, params={}):
    mid = msg_id[0]; msg_id[0] += 1
    ws.send(json.dumps({'id':mid,'method':method,'params':params}))
    ws.settimeout(10)
    for _ in range(60):
        try:
            r = json.loads(ws.recv())
            if r.get('id') == mid: return r
        except: break

# ─── STEP ב — Open watchlist panel + switch to DAYSCAN ──────────────────────
print("\nSTEP ב — עובר ל-DAYSCAN...")
if not switch_to_dayscan(ws):
    ws.close()
    exit(1)

# ─── Read symbols ─────────────────────────────────────────────────────────────
symbols_json = run_js("""
(function(){
  var syms = [], seen = {};
  document.querySelectorAll('[data-symbol-full]').forEach(function(el){
    var s = el.getAttribute('data-symbol-full').split(':').pop();
    if(s && !seen[s]){ seen[s]=1; syms.push(s); }
  });
  return JSON.stringify(syms);
})()
""")
symbols = json.loads(symbols_json) if symbols_json and symbols_json != 'timeout' else []
print(f"מניות ב-DAYSCAN: {len(symbols)} — {symbols}")

if not symbols:
    print("הרשימה ריקה — אין מה לנקות!")
    ws.close()
    exit(0)

# ─── Clear DAYSCAN watchlist via REST API ────────────────────────────────────
print(f"\nמנקה את רשימת DAYSCAN ({len(symbols)} מניות) דרך API...")
clear_result = run_js("""
(async function(){
  try {
    // שלב 1: מצא את ה-ID של DAYSCAN
    var r = await fetch('/api/v1/symbols_list/custom/', {credentials:'include'});
    var lists = await r.json();
    var dayscan = lists.find(function(l){ return l.name === 'DAYSCAN'; });
    if(!dayscan) return 'DAYSCAN_not_found_in_api';
    // שלב 2: נקה את הרשימה עם POST + []
    var r2 = await fetch('/api/v1/symbols_list/custom/'+dayscan.id+'/replace/?unsafe=true', {
      method: 'POST',
      credentials: 'include',
      headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
      body: JSON.stringify([])
    });
    if(r2.status === 200) return 'cleared_via_api';
    return 'api_error_'+r2.status;
  } catch(e) { return 'err:'+e.message; }
})()
""", await_promise=True, timeout=15)
print("Clear list result:", clear_result)
time.sleep(1)

# ─── STEP ג — Clear drawings from each chart ─────────────────────────────────
print(f"\nSTEP ג — מנקה ציורים מ-{len(symbols)} גרפים...")
ws.send(json.dumps({"id":999,"method":"Page.enable","params":{}}))
ws.recv()

cleaned = 0
for i, sym in enumerate(symbols):
    print(f"  [{i+1}/{len(symbols)}] {sym}...", end=" ", flush=True)
    mid = msg_id[0]; msg_id[0] += 1
    ws.send(json.dumps({"id":mid,"method":"Page.navigate","params":{"url":f"https://www.tradingview.com/chart/?symbol={sym}"}}))
    for _ in range(30):
        try:
            r = json.loads(ws.recv())
            if r.get('id') == mid: break
        except: break
    time.sleep(6)

    result = run_js("""
(function(){
  try {
    var w = window, widget = null;
    for(var k in w){
      try{ if(w[k] && typeof w[k].activeChart==='function'){ widget=w[k]; break; } }catch(e){}
    }
    if(!widget) return 'no_widget';
    widget.activeChart().removeAllShapes();
    return 'ok';
  } catch(e){ return 'err:'+e.message; }
})()
""")
    time.sleep(1)

    save = run_js("""
(function(){
  try {
    var w = window, widget = null;
    for(var k in w){
      try{ if(w[k] && typeof w[k].activeChart==='function'){ widget=w[k]; break; } }catch(e){}
    }
    if(!widget) return 'no_widget';
    if(typeof widget.saveChartToServer==='function'){ widget.saveChartToServer(null,null,{}); return 'saved'; }
    if(typeof widget.save==='function'){ widget.save(function(){}); return 'saved'; }
    return 'no_save_fn';
  } catch(e){ return 'err:'+e.message; }
})()
""")
    print(f"draw:{result} save:{save}")
    if result == 'ok': cleaned += 1
    time.sleep(1)

ws.close()
print(f"\n✅ CleanDayScan הושלם!")
print(f"   ניקה ציורים מ-{cleaned}/{len(symbols)} גרפים")
if clear_result == 'cleared_via_api':
    print(f"   ✅ רשימת DAYSCAN נוקתה אוטומטית דרך API")
else:
    print(f"   ⚠️  יש למחוק ידנית את המניות מרשימת DAYSCAN ({clear_result})")
