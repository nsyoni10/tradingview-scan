# -*- coding: utf-8 -*-
import json, websocket, urllib.request, time, sys
sys.stdout.reconfigure(encoding='utf-8')

def connect_tv():
    pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    page = next(p for p in pages if 'tradingview.com' in p.get('url', ''))
    print("Connected to:", page['url'])
    ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=20, header={'Origin': 'http://localhost'})
    return ws

def make_runner(ws):
    mid = [1]
    def run_js(code, await_promise=False):
        m = mid[0]; mid[0] += 1
        ws.send(json.dumps({'id': m, 'method': 'Runtime.evaluate', 'params': {
            'expression': code, 'returnByValue': True, 'awaitPromise': await_promise
        }}))
        for _ in range(120):
            r = json.loads(ws.recv())
            if r.get('id') == m:
                return r.get('result', {}).get('result', {}).get('value', '')
        return 'timeout'
    return run_js

def switch_to_dayscan(ws, target='DAYSCAN'):
    run_js = make_runner(ws)

    # STEP 1 — פתיחת watchlist panel
    r = run_js("""
new Promise(function(resolve){
  var btn = document.querySelector('[data-name="base-watchlist-widget-button"]')
         || document.querySelector('[aria-label*="Watchlist"]')
         || document.querySelector('[aria-label*="watchlist"]');
  if(!btn){ resolve('no_btn'); return; }
  var isActive = btn.getAttribute('aria-pressed')==='true'
              || btn.className.includes('Active')
              || btn.className.includes('active');
  if(!isActive) btn.click();
  resolve(isActive ? 'already_open' : 'opened');
})
""", await_promise=True)
    print("Panel:", r)
    time.sleep(1.0)

    # STEP 2 — חיפוש DAYSCAN ישיר ב-DOM
    r = run_js("""
new Promise(function(resolve){
  var target = '""" + target + """';
  var found = false;
  document.querySelectorAll('*').forEach(function(el){
    if(el.children.length===0 && el.textContent.trim()===target && el.offsetParent!==null){
      found = true;
      el.click();
      if(el.parentElement) el.parentElement.click();
      if(el.parentElement && el.parentElement.parentElement) el.parentElement.parentElement.click();
    }
  });
  if(found){ resolve('switched'); return; }

  // STEP 3 — פתיחת dropdown ע"י watchlists-button
  var wlBtn = document.querySelector('[data-name="watchlists-button"]')
           || document.querySelector('[class*="watchlistsButton"]');
  if(wlBtn) wlBtn.click();

  setTimeout(function(){
    var found2 = false;
    document.querySelectorAll('*').forEach(function(el){
      if(el.children.length===0 && el.textContent.trim()===target && el.offsetParent!==null){
        found2 = true;
        el.click();
        if(el.parentElement) el.parentElement.click();
        if(el.parentElement && el.parentElement.parentElement) el.parentElement.parentElement.click();
      }
    });
    resolve(found2 ? 'switched' : 'not_found');
  }, 800);
})
""", await_promise=True)
    print("Switch:", r)
    time.sleep(0.8)

    # STEP 4 — וידוא
    current = run_js("(function(){ var el=document.querySelector(\"[class*='titleRow']\") || document.querySelector(\"[class*='watchlistTitle']\"); return el?el.textContent.trim():'?'; })()")
    print("Current watchlist:", current)

    if target in str(current):
        print(f"OK — על {target}")
        return True
    else:
        print(f"ERROR — לא הצלחתי לעבור ל-{target}")
        return False


if __name__ == '__main__':
    ws = connect_tv()
    success = switch_to_dayscan(ws)
    ws.close()
    sys.exit(0 if success else 1)
