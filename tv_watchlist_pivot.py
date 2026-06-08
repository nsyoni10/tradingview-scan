# -*- coding: utf-8 -*-
# tv_watchlist_pivot.py — reads from _top10_long.json / _top10_short.json
import json, websocket, urllib.request, time, sys
sys.stdout.reconfigure(encoding='utf-8')

# Read symbols from JSON files (NOT from dayscan_results.html)
try:
    with open("C:/Users/nsyon/SCAN/_top10_long.json") as f:
        top_long = [s['symbol'] for s in json.load(f)]
except:
    top_long = []

try:
    with open("C:/Users/nsyon/SCAN/_top10_short.json") as f:
        top_short = [s['symbol'] for s in json.load(f)]
except:
    top_short = []

symbols = top_long + top_short
print(f"Top symbols ({len(symbols)}): {symbols}")

pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
page = next(p for p in pages if 'tradingview.com' in p.get('url',''))
print("Connected to:", page['url'])
ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=20, header={'Origin': 'http://localhost'})

mid = [1]

def run_js(code, await_promise=False):
    m = mid[0]; mid[0] += 1
    ws.send(json.dumps({'id':m,'method':'Runtime.evaluate','params':{'expression':code,'returnByValue':True,'awaitPromise':await_promise}}))
    for _ in range(120):
        r = json.loads(ws.recv())
        if r.get('id') == m:
            return r.get('result',{}).get('result',{}).get('value','')
    return 'timeout'

def send_cmd(method, params={}):
    m = mid[0]; mid[0] += 1
    ws.send(json.dumps({'id':m,'method':method,'params':params}))
    for _ in range(60):
        r = json.loads(ws.recv())
        if r.get('id') == m:
            return r

def press_key(key, code, keycode):
    send_cmd("Input.dispatchKeyEvent", {"type":"keyDown","key":key,"code":code,"windowsVirtualKeyCode":keycode,"nativeVirtualKeyCode":keycode})
    time.sleep(0.05)
    send_cmd("Input.dispatchKeyEvent", {"type":"keyUp","key":key,"code":code,"windowsVirtualKeyCode":keycode})
    time.sleep(0.15)

# Open watchlist panel
print("Opening watchlist panel...")
r = run_js("""
new Promise(function(resolve){
  var btn = document.querySelector('[data-name="base-watchlist-widget-button"]')
         || document.querySelector('[aria-label*="Watchlist"]')
         || document.querySelector('[aria-label*="watchlist"]');
  if(!btn){ resolve('no watchlist panel button'); return; }
  var isActive = btn.getAttribute('aria-pressed')==='true'
              || btn.className.includes('Active')
              || btn.className.includes('active');
  if(!isActive){ btn.click(); }
  resolve(isActive ? 'already open' : 'opened');
})
""", await_promise=True)
print("Panel:", r)
time.sleep(1.0)

# Switch to DAYSCAN watchlist
print("Switching to DAYSCAN watchlist...")
r = run_js("""
new Promise(function(resolve){
  var found = false;
  document.querySelectorAll('*').forEach(function(el){
    if(el.children.length===0 && el.textContent.trim()==='DAYSCAN' && el.offsetParent!==null){
      found = true;
      el.click();
      if(el.parentElement) el.parentElement.click();
      if(el.parentElement && el.parentElement.parentElement) el.parentElement.parentElement.click();
    }
  });
  if(found){ resolve('switched'); return; }
  var wlBtn = document.querySelector('[data-name="watchlists-button"]')
           || document.querySelector('[class*="watchlistsButton"]');
  if(wlBtn){ wlBtn.click(); }
  setTimeout(function(){
    var found2 = false;
    document.querySelectorAll('*').forEach(function(el){
      if(el.children.length===0 && el.textContent.trim()==='DAYSCAN' && el.offsetParent!==null){
        found2 = true;
        el.click();
        if(el.parentElement) el.parentElement.click();
        if(el.parentElement && el.parentElement.parentElement) el.parentElement.parentElement.click();
      }
    });
    resolve(found2 ? 'switched' : 'DAYSCAN not found');
  }, 800);
})
""", await_promise=True)
print("Switch:", r)
time.sleep(0.8)

current = run_js("(function(){ var el=document.querySelector(\"[class*='titleRow']\") || document.querySelector(\"[class*='watchlistTitle']\"); return el?el.textContent.trim():'?'; })()")
print("Current watchlist:", current)

if 'DAYSCAN' not in str(current):
    print("ERROR: Could not switch to DAYSCAN watchlist!")
    ws.close()
    exit(1)

# Add symbols
print(f"\nAdding {len(symbols)} symbols...")
for i, sym in enumerate(symbols):
    print(f"  [{i+1}/{len(symbols)}] {sym}...", end=" ")
    r = run_js("""
(function(){
  var btn = document.querySelector('[data-name="add-symbol-button"]');
  if(btn){ btn.click(); return 'ok'; }
  return 'no_btn';
})()
""")
    if r != 'ok':
        print(f"ERROR ({r})")
        continue
    time.sleep(0.5)
    send_cmd("Input.insertText", {"text": sym})
    time.sleep(0.7)
    press_key("Enter", "Enter", 13)
    time.sleep(0.5)
    press_key("Escape", "Escape", 27)
    time.sleep(0.4)
    print("added")

# Verify
print("\nVerifying...")
verify = run_js("""
(function(){
  var syms = [];
  document.querySelectorAll('[data-symbol-full]').forEach(function(el){ syms.push(el.getAttribute('data-symbol-full')); });
  return JSON.stringify(syms);
})()
""")
print("DAYSCAN symbols:", verify)

ws.close()
print("Done.")
