# -*- coding: utf-8 -*-
import json, websocket, urllib.request, time, sys
sys.stdout.reconfigure(encoding='utf-8')

pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
page = next(p for p in pages if 'tradingview.com' in p.get('url', ''))
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

# Click watchlists-button to open dropdown
r = run_js('(function(){ var btn=document.querySelector("[data-name=\'watchlists-button\']"); if(btn){btn.click();return "clicked";} return "not_found"; })()')
print('Click result:', r)
time.sleep(1.5)

# Get all visible text elements in dropdowns/menus/lists
r2 = run_js('''(function(){
    // Look for any dropdown, popup, menu-like elements that appeared
    var selectors = [
        '[data-name*="watchlist"]',
        '[class*="watchlist"]',
        '[class*="Watchlist"]',
        '[class*="dropdown"]',
        '[class*="popup"]',
        '[class*="menu"]',
        '[role="listbox"]',
        '[role="menu"]',
        '[role="option"]'
    ];
    var found = {};
    selectors.forEach(function(sel){
        try {
            var els = document.querySelectorAll(sel);
            if(els.length > 0) {
                found[sel] = [];
                els.forEach(function(el){
                    if(el.offsetParent !== null) {
                        found[sel].push(el.textContent.trim().substring(0,60));
                    }
                });
            }
        } catch(e){}
    });
    return JSON.stringify(found);
})()''')
print('Dropdown/menu elements:', r2)

ws.close()
