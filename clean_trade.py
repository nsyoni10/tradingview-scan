# -*- coding: utf-8 -*-
# clean_trade.py — מנקה את רשימת CoffeeL.
# הקוד מועתק מ-cleandayscan.py (העובד). השינוי היחיד: DAYSCAN -> CoffeeL.
import json, websocket, urllib.request, time, sys
sys.stdout.reconfigure(encoding='utf-8')

from tv_switch_dayscan import connect_tv, switch_to_dayscan, make_runner

TARGET = 'CoffeeL'

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

# ─── STEP ב — Open watchlist panel + switch to CoffeeL ──────────────────────
print(f"\nSTEP ב — עובר ל-{TARGET}...")
if not switch_to_dayscan(ws, target=TARGET):
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
print(f"מניות ב-{TARGET}: {len(symbols)} — {symbols}")

if not symbols:
    print("הרשימה ריקה — אין מה לנקות!")
    ws.close()
    exit(0)

# ─── Clear CoffeeL watchlist via REST API ────────────────────────────────────
print(f"\nמנקה את רשימת {TARGET} ({len(symbols)} מניות) דרך API...")
clear_result = run_js("""
(async function(){
  try {
    var r = await fetch('/api/v1/symbols_list/custom/', {credentials:'include'});
    var lists = await r.json();
    var target = lists.find(function(l){ return l.name === '""" + TARGET + """'; });
    if(!target) return '""" + TARGET + """_not_found_in_api';
    var r2 = await fetch('/api/v1/symbols_list/custom/'+target.id+'/replace/?unsafe=true', {
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

# ─── Verify via DOM ───────────────────────────────────────────────────────────
verify = run_js("""
(function(){
  var syms = [];
  document.querySelectorAll('[data-symbol-full]').forEach(function(el){ syms.push(el.getAttribute('data-symbol-full')); });
  return JSON.stringify(syms);
})()
""")
print(f"{TARGET} אחרי ניקוי (DOM):", verify)

ws.close()
print("Done.")
