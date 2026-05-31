"""
Navigate to CoffeeL screener page via CDP, capture scanner POST request, read symbols.
Then do the same for CoffeeS (already known).
"""
import requests, json, websocket, sys, time, threading
sys.stdout.reconfigure(encoding='utf-8')

pages = requests.get('http://localhost:9222/json').json()
screener_page = next((p for p in pages if 'tradingview.com/screener' in p.get('url','')), None)
print("Navigating from:", screener_page['url'])

ws = websocket.create_connection(screener_page['webSocketDebuggerUrl'])

def send(method, params={}):
    ws.send(json.dumps({'id':99,'method':method,'params':params}))

def eval_js(js, timeout=12):
    ws.send(json.dumps({'id':1,'method':'Runtime.evaluate',
                        'params':{'expression':js,'returnByValue':True,'awaitPromise':True}}))
    ws.settimeout(timeout)
    try:
        while True:
            msg = json.loads(ws.recv())
            if msg.get('id') == 1 and 'result' in msg:
                return msg.get('result',{}).get('result',{}).get('value')
    except:
        return None

# Enable network monitoring
send('Network.enable')
send('Page.enable')
time.sleep(0.3)

COFFEEL_SYMS = []
COFFEES_SYMS = []
scan_bodies = {}
done_event = threading.Event()

def listener():
    ws.settimeout(20)
    try:
        while not done_event.is_set():
            try:
                msg = json.loads(ws.recv())
                m = msg.get('method','')
                if m == 'Network.requestWillBeSent':
                    req = msg['params']
                    url = req.get('request',{}).get('url','')
                    body = req.get('request',{}).get('postData','')
                    if 'scanner.tradingview.com' in url and 'scan' in url and body:
                        rid = req.get('requestId')
                        scan_bodies[rid] = {'url': url, 'body': body}
                        print(f"  SCAN POST: {url[:80]}")
                elif m == 'Network.responseReceived':
                    url = msg['params'].get('response',{}).get('url','')
                    rid = msg['params'].get('requestId')
                    status = msg['params'].get('response',{}).get('status')
                    if 'scanner.tradingview.com' in url and 'scan' in url and rid in scan_bodies:
                        # Get response body
                        ws.send(json.dumps({'id':200,'method':'Network.getResponseBody','params':{'requestId':rid}}))
                elif msg.get('id') == 200:
                    body = msg.get('result',{}).get('body','')
                    if body:
                        try:
                            data = json.loads(body)
                            syms = [(item['s'] if isinstance(item['s'],str) else item['d'][0] if item.get('d') else '')
                                    for item in data.get('data',[])]
                            syms = [s.replace('NASDAQ:','').replace('NYSE:','').replace('AMEX:','')
                                    .replace('OTC:','').replace('CBOE:','')
                                    for s in syms if s]
                            # filter clean symbols
                            syms = [s.split(':')[-1] for s in syms if s]
                            print(f"  -> {len(syms)} symbols: {syms[:5]}...")
                            if syms:
                                scan_bodies[f'result_{len(scan_bodies)}'] = syms
                        except Exception as e:
                            print(f"  parse err: {e}")
            except websocket.WebSocketTimeoutException:
                break
            except Exception as e:
                if not done_event.is_set():
                    pass
    except:
        pass

t = threading.Thread(target=listener, daemon=True)
t.start()

# Navigate to CoffeeL screener page
COFFEEL_ID = 'OfYmLUqI'
COFFEES_ID = 'oBqGK3SJ'

print(f"\nNavigating to CoffeeL: {COFFEEL_ID}")
ws.send(json.dumps({'id':2,'method':'Page.navigate',
                    'params':{'url': f'https://www.tradingview.com/screener/{COFFEEL_ID}/'}}))
time.sleep(12)

# Read CoffeeL symbols from DOM
READ_JS = """
(function() {
    var syms = [], seen = {};
    var sel = '[class*="tickerCell"] [class*="ticker"], [class*="symbol-"], [data-field-key="name"] a';
    document.querySelectorAll(sel).forEach(function(el) {
        var t = el.textContent.trim();
        if (t && /^[A-Z]{1,5}$/.test(t) && !seen[t]) { seen[t]=1; syms.push(t); }
    });
    if (syms.length === 0) {
        document.querySelectorAll('[class*="apply-overflow-tooltip"]').forEach(function(el) {
            var t = el.textContent.trim();
            if (t && /^[A-Z]{1,5}$/.test(t) && !seen[t]) { seen[t]=1; syms.push(t); }
        });
    }
    return JSON.stringify({count: syms.length, syms: syms});
})()
"""

r_coffeel = eval_js(READ_JS, 10)
if r_coffeel:
    data = json.loads(r_coffeel)
    COFFEEL_SYMS = data.get('syms', [])
    print(f"CoffeeL from DOM: {len(COFFEEL_SYMS)} symbols: {COFFEEL_SYMS[:5]}")

# Also check captured scan results
for k, v in scan_bodies.items():
    if isinstance(v, list) and len(v) > 0:
        if not COFFEEL_SYMS:
            COFFEEL_SYMS = v
        print(f"Scan capture result: {v[:5]}...")

# Navigate back to CoffeeS to get its symbols too
print(f"\nNavigating to CoffeeS: {COFFEES_ID}")
ws.send(json.dumps({'id':3,'method':'Page.navigate',
                    'params':{'url': f'https://www.tradingview.com/screener/{COFFEES_ID}/'}}))
time.sleep(10)

r_coffees = eval_js(READ_JS, 10)
if r_coffees:
    data = json.loads(r_coffees)
    COFFEES_SYMS = data.get('syms', [])
    print(f"CoffeeS from DOM: {len(COFFEES_SYMS)} symbols: {COFFEES_SYMS[:5]}")

done_event.set()
t.join(timeout=2)
ws.close()

print(f"\n=== FINAL SYMBOLS ===")
print(f"LONG  (CoffeeL): {len(COFFEEL_SYMS)} -> {COFFEEL_SYMS}")
print(f"SHORT (CoffeeS): {len(COFFEES_SYMS)} -> {COFFEES_SYMS}")

# Save
with open('C:/Users/nsyon/SCAN/_long_syms.json','w')  as f: json.dump(COFFEEL_SYMS, f)
with open('C:/Users/nsyon/SCAN/_short_syms.json','w') as f: json.dump(COFFEES_SYMS, f)
print("Saved to _long_syms.json / _short_syms.json")
