# -*- coding: utf-8 -*-
import json, websocket, urllib.request, time, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')

CDP_URL  = 'http://localhost:9222/json'
TV_EXE   = r'C:\Program Files\WindowsApps\TradingView.Desktop_3.1.0.7818_x64__n534cwy3pjxzj\TradingView.exe'
TV_FLAGS = ['--remote-debugging-port=9222', '--remote-allow-origins=*']

# ─── CDP helpers ─────────────────────────────────────────────────────────────

msg_id = [1]

def connect_to_tv():
    print("STEP א — מתחבר ל-TradingView Desktop...")

    def get_page():
        try:
            pages = json.loads(urllib.request.urlopen(CDP_URL, timeout=5).read())
            return next((p for p in pages if 'tradingview.com/chart' in p.get('url', '')), None)
        except:
            return None

    page = get_page()
    if not page:
        print("TradingView לא פתוח — מפעיל...")
        subprocess.Popen([TV_EXE] + TV_FLAGS)
        for _ in range(15):
            time.sleep(2)
            page = get_page()
            if page: break

    if not page:
        print("ERROR: לא הצלחתי להתחבר. פתח TradingView ידנית ונסה שוב.")
        sys.exit(1)

    print(f"Connected to: {page['url']}")
    ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=20, header={'Origin': 'http://localhost'})
    return ws


def run_js(ws, code, await_promise=False, timeout=20):
    mid = msg_id[0]; msg_id[0] += 1
    ws.send(json.dumps({"id": mid, "method": "Runtime.evaluate", "params": {
        "expression": code, "returnByValue": True, "awaitPromise": await_promise
    }}))
    ws.settimeout(timeout)
    for _ in range(200):
        try:
            r = json.loads(ws.recv())
            if r.get('id') == mid:
                return r.get('result', {}).get('result', {}).get('value', '')
        except:
            break
    return 'timeout'


def navigate(ws, url):
    mid = msg_id[0]; msg_id[0] += 1
    ws.send(json.dumps({"id": mid, "method": "Page.navigate", "params": {"url": url}}))
    ws.settimeout(15)
    for _ in range(30):
        try:
            r = json.loads(ws.recv())
            if r.get('id') == mid: break
        except:
            break

# ─── STEP ב — פתיחת Watchlist panel ─────────────────────────────────────────

def open_watchlist_panel(ws):
    result = run_js(ws, """
(function(){
  var btn = document.querySelector('[data-name="base-watchlist-widget-button"]')
         || document.querySelector('[aria-label="Watchlist"]');
  if (!btn) return 'btn_not_found';
  var rightArea = document.querySelector('[class*="layout__area--right"]');
  var isOpen = btn.getAttribute('aria-pressed') === 'true'
            && rightArea && rightArea.offsetWidth > 50;
  if (!isOpen) { btn.click(); return 'opened'; }
  return 'already_open';
})()
""")
    print(f"Watchlist panel: {result}")
    if result == 'opened':
        time.sleep(0.8)
    return result != 'btn_not_found'

# ─── STEP ג — זיהוי watchlist פעיל + מעבר ל-DAYSCAN ─────────────────────────

def get_active_watchlist(ws):
    return run_js(ws, """
(function(){
  try {
    var widget = window.TradingViewApi._activeChartWidgetWV.value();
    var wl = widget.watchList();
    var activeId = wl.getActiveListId();
    var allLists = wl.getAllLists();
    var name = allLists && allLists[activeId] ? allLists[activeId].name : '?';
    return JSON.stringify({ id: activeId, name: name });
  } catch(e) { return JSON.stringify({ id: null, name: 'error:' + e.message }); }
})()
""")


def switch_to_watchlist(ws, target_name):
    print(f"\nSTEP ג — בודק watchlist פעיל ועובר ל-{target_name}...")

    raw = get_active_watchlist(ws)
    try:
        active = json.loads(raw)
    except:
        active = {'id': None, 'name': '?'}

    print(f"Watchlist פעיל: {active['name']} (id={active['id']})")

    if active['name'] == target_name:
        print(f"כבר על {target_name} — ממשיך.")
        return True

    # מנסה מעבר דרך ה-API הפנימי
    result = run_js(ws, f"""
(function(){{
  try {{
    var widget = window.TradingViewApi._activeChartWidgetWV.value();
    var wl = widget.watchList();
    var allLists = wl.getAllLists();
    var targetId = null;
    for (var id in allLists) {{
      if (allLists[id].name === '{target_name}') {{ targetId = id; break; }}
    }}
    if (!targetId) return 'not_found_in_api';
    wl.setActiveList && wl.setActiveList(targetId);
    return 'switched_via_api:' + targetId;
  }} catch(e) {{ return 'api_err:' + e.message; }}
}})()
""")
    print(f"API switch: {result}")
    time.sleep(0.8)

    # fallback — לחיצה על האלמנט בDOM
    if 'switched_via_api' not in str(result):
        dom_result = run_js(ws, f"""
(function(){{
  var found = false;
  var candidates = document.querySelectorAll('button, a, [role="button"], [role="menuitem"], [role="tab"], span, div');
  for (var i = 0; i < candidates.length; i++) {{
    if (candidates[i].textContent.trim() === '{target_name}' && candidates[i].offsetParent !== null) {{
      candidates[i].click();
      found = true;
      break;
    }}
  }}
  return found ? 'clicked' : 'not_found_in_dom';
}})()
""")
        print(f"DOM click: {dom_result}")
        time.sleep(0.8)

    # ודא שהמעבר הצליח
    raw2 = get_active_watchlist(ws)
    try:
        active2 = json.loads(raw2)
    except:
        active2 = {'id': None, 'name': '?'}

    print(f"Watchlist אחרי מעבר: {active2['name']}")
    if active2['name'] == target_name:
        return True

    print(f"ERROR: לא הצלחתי לעבור ל-{target_name}. בדוק שהרשימה קיימת.")
    return False

# ─── STEP ד — קריאת סמבולים ──────────────────────────────────────────────────

def get_symbols(ws):
    raw = run_js(ws, """
(function(){
  var syms = [], seen = {};
  var container = document.querySelector('[class*="layout__area--right"]');
  if (!container) return JSON.stringify([]);
  container.querySelectorAll('[data-symbol-full]').forEach(function(el){
    var s = el.getAttribute('data-symbol-full').split(':').pop();
    if (s && !seen[s]) { seen[s] = 1; syms.push(s); }
  });
  return JSON.stringify(syms);
})()
""")
    try:
        return json.loads(raw)
    except:
        return []

# ─── STEP ה — ניקוי רשימה דרך API ───────────────────────────────────────────

def clear_watchlist_api(ws):
    result = run_js(ws, """
(async function(){
  try {
    var r = await fetch('/api/v1/symbols_list/custom/', {credentials:'include'});
    var lists = await r.json();
    var dayscan = lists.find(function(l){ return l.name === 'DAYSCAN'; });
    if (!dayscan) return 'DAYSCAN_not_found';
    var r2 = await fetch('/api/v1/symbols_list/custom/'+dayscan.id+'/replace/?unsafe=true', {
      method: 'POST', credentials: 'include',
      headers: {'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
      body: JSON.stringify([])
    });
    return r2.status === 200 ? 'cleared' : 'error_' + r2.status;
  } catch(e) { return 'err:' + e.message; }
})()
""", await_promise=True, timeout=15)
    print(f"Clear watchlist: {result}")
    return result

# ─── STEP ו — ניקוי ציורים מגרף ─────────────────────────────────────────────

def clean_chart(ws, symbol):
    navigate(ws, f'https://www.tradingview.com/chart/?symbol={symbol}')
    time.sleep(6)

    draw = run_js(ws, """
(function(){
  try {
    var chart = window.TradingViewApi._activeChartWidgetWV.value();
    chart.removeAllShapes();
    return 'ok';
  } catch(e) { return 'err:' + e.message; }
})()
""")
    time.sleep(0.5)

    save = run_js(ws, """
(function(){
  try {
    var widget = window.TradingViewApi._activeChartWidgetWV.value();
    if (typeof widget.saveChartToServer === 'function') { widget.saveChartToServer(null, null, {}); return 'saved'; }
    if (typeof widget.save === 'function') { widget.save(function(){}); return 'saved'; }
    return 'no_save_fn';
  } catch(e) { return 'err:' + e.message; }
})()
""")
    return draw, save

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    ws = connect_to_tv()

    if not open_watchlist_panel(ws):
        print("ERROR: כפתור Watchlist לא נמצא.")
        ws.close(); sys.exit(1)

    if not switch_to_watchlist(ws, 'DAYSCAN'):
        ws.close(); sys.exit(1)

    symbols = get_symbols(ws)
    print(f"\nמניות ב-DAYSCAN: {len(symbols)} — {symbols}")

    if not symbols:
        print("הרשימה ריקה — אין מה לנקות!")
        ws.close(); sys.exit(0)

    clear_result = clear_watchlist_api(ws)

    print(f"\nSTEP ו — מנקה ציורים מ-{len(symbols)} גרפים...")
    ws.send(json.dumps({"id": 999, "method": "Page.enable", "params": {}}))
    ws.recv()

    cleaned = 0
    for i, sym in enumerate(symbols):
        print(f"  [{i+1}/{len(symbols)}] {sym}...", end=" ", flush=True)
        draw, save = clean_chart(ws, sym)
        print(f"draw:{draw} save:{save}")
        if draw == 'ok': cleaned += 1
        time.sleep(0.5)

    ws.close()

    print(f"\n✅ CleanDayScan הושלם!")
    print(f"   ניקה ציורים מ-{cleaned}/{len(symbols)} גרפים")
    if clear_result == 'cleared':
        print(f"   ✅ רשימת DAYSCAN נוקתה אוטומטית")
    else:
        print(f"   ⚠️  יש למחוק ידנית את המניות ({clear_result})")


if __name__ == '__main__':
    main()
