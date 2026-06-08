# -*- coding: utf-8 -*-
"""
brew.py — קונטיינר ☕ brew
מפעיל: python brew.py [clean|cleanL|cleanS|demoL|demoS]

  clean  — מנקה CoffeeL + CoffeeS
  cleanL — מנקה CoffeeL בלבד
  cleanS — מנקה CoffeeS בלבד
  demoL  — מוסיף gainers ל-CoffeeL
  demoS  — מוסיף losers  ל-CoffeeS

לוגיקת ניקוי:  מועתקת מ-cleandayscan.py
לוגיקת הוספה: מועתקת מ-tv_watchlist_pivot.py
"""
import json, websocket, urllib.request, time, sys, requests, warnings, subprocess
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

from tv_switch_dayscan import connect_tv, switch_to_dayscan

# נתיב TradingView Desktop (מתוך דרישות המקדם של הסקיל)
TV_EXE = r'C:\Program Files\WindowsApps\TradingView.Desktop_3.2.0.7916_x64__n534cwy3pjxzj\TradingView.exe'


# ══════════════════════════════════════════════════════════════════════════════
# בדיקת/יצירת תקשורת ל-TradingView (CDP port 9222)
# ══════════════════════════════════════════════════════════════════════════════
def _tv_page_ready():
    """True אם יש page target של tradingview.com על CDP 9222."""
    try:
        pages = json.loads(urllib.request.urlopen('http://localhost:9222/json', timeout=3).read())
        return any('tradingview.com' in p.get('url', '') for p in pages)
    except Exception:
        return False


def ensure_tv():
    """בודק אם יש תקשורת ל-TradingView; אם אין — מפעיל אותו עם CDP וממתין."""
    if _tv_page_ready():
        print("✓ תקשורת ל-TradingView קיימת (CDP 9222)")
        return True
    print("אין תקשורת — מפעיל TradingView עם CDP...")
    try:
        subprocess.Popen([TV_EXE, '--remote-debugging-port=9222', '--remote-allow-origins=*'])
    except Exception as e:
        print(f"✗ נכשל בהפעלת TradingView: {e}")
        return False
    for i in range(20):
        time.sleep(2)
        if _tv_page_ready():
            time.sleep(4)  # שהיית בטחון שהדף ייטען לגמרי
            print(f"✓ TradingView עלה (~{i*2+6}s)")
            return True
    print("✗ TradingView לא עלה בזמן")
    return False

# ══════════════════════════════════════════════════════════════════════════════
# ניקוי ליסט — מועתק מ-cleandayscan.py, שינוי יחיד: שם הרשימה כפרמטר
# ══════════════════════════════════════════════════════════════════════════════
def clean_list(target):
    """מנקה ליסט דרך REST טהור (set_list עם []). מוודא תקשורת קודם. ללא החלפת-UI."""
    if not ensure_tv():
        print(f"ERROR: אין תקשורת ל-TradingView — לא ניתן לנקות את {target}.")
        return
    res = set_list(target, [])
    if res.get('err'):
        print(f"⚠️  {target}: {res['err']}")
    else:
        print(f"✅ רשימת {target} נוקתה דרך REST (status {res.get('status')})")


# ══════════════════════════════════════════════════════════════════════════════
# הוספת סמלים — מועתק מ-tv_watchlist_pivot.py, שינוי יחיד: שם הרשימה כפרמטר
# ══════════════════════════════════════════════════════════════════════════════
def add_to_list(target, symbols):
    print(f"Top symbols ({len(symbols)}): {symbols}")

    # ─── Connect (tv_watchlist_pivot.py שורות 22-25) ─────────────────────────
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

    # ─── Open watchlist panel (tv_watchlist_pivot.py שורות 54-68) ────────────
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

    # ─── Switch to target watchlist (tv_watchlist_pivot.py שורות 71-110) ─────
    print(f"Switching to {target} watchlist...")
    r = run_js("""
new Promise(function(resolve){
  var found = false;
  document.querySelectorAll('*').forEach(function(el){
    if(el.children.length===0 && el.textContent.trim()==='""" + target + """' && el.offsetParent!==null){
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
      if(el.children.length===0 && el.textContent.trim()==='""" + target + """' && el.offsetParent!==null){
        found2 = true;
        el.click();
        if(el.parentElement) el.parentElement.click();
        if(el.parentElement && el.parentElement.parentElement) el.parentElement.parentElement.click();
      }
    });
    resolve(found2 ? 'switched' : '""" + target + """ not found');
  }, 800);
})
""", await_promise=True)
    print("Switch:", r)
    time.sleep(0.8)

    current = run_js("(function(){ var el=document.querySelector(\"[class*='titleRow']\") || document.querySelector(\"[class*='watchlistTitle']\"); return el?el.textContent.trim():'?'; })()")
    print("Current watchlist:", current)

    if target not in str(current):
        print(f"ERROR: Could not switch to {target} watchlist!")
        ws.close()
        return

    # ─── Add symbols (tv_watchlist_pivot.py שורות 113-133) ───────────────────
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

    # ─── Verify (tv_watchlist_pivot.py שורות 136-144) ────────────────────────
    print("\nVerifying...")
    verify = run_js("""
(function(){
  var syms = [];
  document.querySelectorAll('[data-symbol-full]').forEach(function(el){ syms.push(el.getAttribute('data-symbol-full')); });
  return JSON.stringify(syms);
})()
""")
    print(f"{target} symbols:", verify)

    ws.close()
    print("Done.")


# ══════════════════════════════════════════════════════════════════════════════
# ניקוי סמלים מושחתים — מסיר מהליסט כל סמל שאינו EXCHANGE:TICKER תקין
# (חתימת השחתה: שני ':' — כמו NYSE:GTN-NYSE:A שנוצר מטיקר מחלקה GTN-A)
# ══════════════════════════════════════════════════════════════════════════════
def set_list(name, symbols):
    """כותב את כל הרשימה לליסט בקריאת REST אחת (מבוסס set_list ב-dayscan_web_container.py).
    מחליף את לולאת ה-UI האיטית. מחזיר dict תוצאה."""
    pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    page = next(p for p in pages if 'tradingview.com' in p.get('url', ''))
    ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=20, header={'Origin': 'http://localhost'})
    mid = [1]
    def run_js(code, await_promise=False):
        m = mid[0]; mid[0] += 1
        ws.send(json.dumps({'id': m, 'method': 'Runtime.evaluate', 'params': {'expression': code, 'returnByValue': True, 'awaitPromise': await_promise}}))
        for _ in range(120):
            r = json.loads(ws.recv())
            if r.get('id') == m:
                return r.get('result', {}).get('result', {}).get('value', '')
        return 'timeout'
    raw = run_js("""
(async function(){
  var lists = await (await fetch('/api/v1/symbols_list/custom/',{credentials:'include'})).json();
  var L = lists.find(function(l){ return l.name === '""" + name + """'; });
  if(!L) return JSON.stringify({err:'not_found'});
  var body = """ + json.dumps(symbols) + """;
  var r = await fetch('/api/v1/symbols_list/custom/'+L.id+'/replace/?unsafe=true',{
    method:'POST', credentials:'include',
    headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
    body: JSON.stringify(body)
  });
  var after = await (await fetch('/api/v1/symbols_list/custom/',{credentials:'include'})).json();
  var L2 = after.find(function(l){ return l.name === '""" + name + """'; });
  return JSON.stringify({status:r.status, stored:L2?L2.symbols:[]});
})()
""", await_promise=True)
    ws.close()
    try:
        return json.loads(raw) if raw and raw != 'timeout' else {'err': 'timeout'}
    except Exception:
        return {'err': 'parse'}


def sanitize_list(name):
    """מסיר מהליסט סמלים מושחתים דרך REST. מחזיר רשימת הסמלים שהוסרו."""
    pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    page = next(p for p in pages if 'tradingview.com' in p.get('url', ''))
    ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=20, header={'Origin': 'http://localhost'})
    mid = [1]
    def run_js(code, await_promise=False):
        m = mid[0]; mid[0] += 1
        ws.send(json.dumps({'id': m, 'method': 'Runtime.evaluate', 'params': {'expression': code, 'returnByValue': True, 'awaitPromise': await_promise}}))
        for _ in range(120):
            r = json.loads(ws.recv())
            if r.get('id') == m:
                return r.get('result', {}).get('result', {}).get('value', '')
        return 'timeout'
    raw = run_js("""
(async function(){
  var lists = await (await fetch('/api/v1/symbols_list/custom/',{credentials:'include'})).json();
  var L = lists.find(function(l){ return l.name === '""" + name + """'; });
  if(!L) return JSON.stringify({err:'not_found'});
  var keep=[], drop=[];
  (L.symbols||[]).forEach(function(s){
    var parts = String(s).split(':');
    if(parts.length===2 && /^[A-Za-z0-9.\\-]+$/.test(parts[1])) keep.push(s);
    else drop.push(s);
  });
  if(drop.length===0) return JSON.stringify({dropped:[]});
  var r = await fetch('/api/v1/symbols_list/custom/'+L.id+'/replace/?unsafe=true',{
    method:'POST', credentials:'include',
    headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
    body: JSON.stringify(keep)
  });
  return JSON.stringify({dropped:drop, status:r.status});
})()
""", await_promise=True)
    ws.close()
    try:
        res = json.loads(raw) if raw and raw != 'timeout' else {}
    except Exception:
        res = {}
    dropped = res.get('dropped', [])
    if res.get('err'):
        print(f"  sanitize {name}: {res['err']}")
    elif dropped:
        print(f"  sanitize {name}: הוסרו {len(dropped)} סמלים מושחתים → {dropped}")
    else:
        print(f"  sanitize {name}: נקי, אין מה להסיר")
    return dropped


# ══════════════════════════════════════════════════════════════════════════════
# משיכת נתונים מ-Yahoo
# ══════════════════════════════════════════════════════════════════════════════
def fetch_yahoo(scr_id, count=25):
    H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url = f'https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds={scr_id}&count={count}'
    r = requests.get(url, headers=H, verify=False, timeout=15)
    quotes = r.json()['finance']['result'][0]['quotes']
    return [q['symbol'] for q in quotes]


# מיפוי קוד בורסה של Yahoo → קידומת TradingView (לבניית סמל מלא לכתיבת REST)
_EXMAP = {'NYQ': 'NYSE', 'NYE': 'NYSE', 'PCX': 'AMEX', 'ASE': 'AMEX', 'AMX': 'AMEX',
          'NMS': 'NASDAQ', 'NCM': 'NASDAQ', 'NGM': 'NASDAQ', 'NAS': 'NASDAQ', 'BTS': 'BATS'}


def fetch_yahoo_q(scr_id, count=25):
    """כמו fetch_yahoo אבל מחזיר סמלים מלאים 'EXCHANGE:TICKER' (לכתיבת REST דרך set_list).
    משתמש בשדה exchange של Yahoo. אם לא ממופה — מחזיר טיקר גולמי (sanitize/UI יטפלו)."""
    H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    url = f'https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds={scr_id}&count={count}'
    r = requests.get(url, headers=H, verify=False, timeout=15)
    quotes = r.json()['finance']['result'][0]['quotes']
    out = []
    for q in quotes:
        sym = q['symbol']
        ex = _EXMAP.get(q.get('exchange', ''))
        out.append(f'{ex}:{sym}' if ex else sym)
    return out


def qualify_tickers(bare):
    """פותר רשימת טיקרים גולמיים ל-'EXCHANGE:TICKER' דרך Yahoo v8 chart meta.exchangeName.
    לטיקרים בלי exchange (Benzinga). אם לא ניתן לפתור — משאיר גולמי."""
    H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    out = []
    for s in bare:
        ex = None
        try:
            u = f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?interval=1d&range=1d'
            meta = requests.get(u, headers=H, verify=False, timeout=10).json()['chart']['result'][0]['meta']
            ex = _EXMAP.get(meta.get('exchangeName', ''))
        except Exception:
            ex = None
        out.append(f'{ex}:{s}' if ex else s)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# קריאת סמלים מליסט לפי שם
# ══════════════════════════════════════════════════════════════════════════════
def read_list(src):
    """מחזיר רשימת טיקרים מליסט TV לפי שם, או None אם לא נמצא"""
    pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    page = next(p for p in pages if 'tradingview.com' in p.get('url',''))
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
    raw = run_js("""
(async function(){
  var lists = await (await fetch('/api/v1/symbols_list/custom/',{credentials:'include'})).json();
  var L = lists.find(function(l){ return l.name === '""" + src + """'; });
  if(!L) return '__not_found__';
  return JSON.stringify(L.symbols || []);
})()
""", await_promise=True)
    ws.close()
    if not raw or raw == '__not_found__':
        return None
    syms = json.loads(raw)
    return [s.split(':')[-1] for s in syms]


# ══════════════════════════════════════════════════════════════════════════════
# פונקציות ציבוריות
# ══════════════════════════════════════════════════════════════════════════════
def clean():
    cleanL()
    cleanS()

def cleanL():
    clean_list('CoffeeL')

def cleanS():
    clean_list('CoffeeS')

def demoL():
    syms = fetch_yahoo('day_gainers')
    add_to_list('CoffeeL', syms)

def demoS():
    syms = fetch_yahoo('day_losers')
    add_to_list('CoffeeS', syms)

def day_gainers():
    """brew day_gainers — סקיל-איסוף LONG מ-Yahoo day_gainers.
    1) מוודא תקשורת ל-TV (מפעיל אם צריך)
    2) מנקה את dw_skill_gainers
    3) מושך day_gainers מ-Yahoo ומכניס ל-dw_skill_gainers (שיטת dayscan_pivot)
    4) מעתיק dw_skill_gainers → CoffeeL (copy2L)
    """
    LIST = 'dw_skill_gainers'

    # ─── שלב 1 — תקשורת ────────────────────────────────────────────────────────
    if not ensure_tv():
        print("ERROR: אין תקשורת ל-TradingView — עוצר.")
        return

    # שלב הניקוי הוסר — set_list עושה REST replace שדורס את כל הרשימה ממילא

    # ─── שלב 3 — משיכת day_gainers + הכנסה ──────────────────────────────────────
    print(f"\n══ שלב 3: משיכת day_gainers מ-Yahoo ══")
    syms = fetch_yahoo_q('day_gainers')
    print(f"נמשכו {len(syms)} טיקרים: {syms}")
    if not syms:
        print("אין טיקרים מ-Yahoo — עוצר.")
        return
    print(f"\n══ הכנסה ל-{LIST} (REST set_list — מהיר ואמין) ══")
    res = set_list(LIST, syms)
    print(f"  נכתבו {len(res.get('stored', []))} סמלים | status {res.get('status')} | err {res.get('err')}")
    print(f"\n══ ניקוי סמלים מושחתים מ-{LIST} ══")
    sanitize_list(LIST)

    # ─── שלב 4 — copy2L → CoffeeL ──────────────────────────────────────────────
    print(f"\n══ שלב 4: copy2L — {LIST} → CoffeeL ══")
    copy2L(LIST)
    sanitize_list('CoffeeL')
    print("\n✅ brew day_gainers הושלם.")


def small_cap_gainers():
    """brew small_cap_gainers — סקיל-איסוף LONG מ-Yahoo small_cap_gainers.
    1) מוודא תקשורת ל-TV
    2) מנקה את dw_skill_smallcap
    3) מושך small_cap_gainers מ-Yahoo ומכניס ל-dw_skill_smallcap (שיטת dayscan_pivot)
    4) מעתיק dw_skill_smallcap → CoffeeL (copy2L)
    """
    LIST = 'dw_skill_smallcap'

    if not ensure_tv():
        print("ERROR: אין תקשורת ל-TradingView — עוצר.")
        return

    # שלב הניקוי הוסר — set_list עושה REST replace שדורס את כל הרשימה ממילא

    print(f"\n══ שלב 3: משיכת small_cap_gainers מ-Yahoo ══")
    syms = fetch_yahoo_q('small_cap_gainers')
    print(f"נמשכו {len(syms)} טיקרים: {syms}")
    if not syms:
        print("אין טיקרים מ-Yahoo — עוצר.")
        return
    print(f"\n══ הכנסה ל-{LIST} (REST set_list — מהיר ואמין) ══")
    res = set_list(LIST, syms)
    print(f"  נכתבו {len(res.get('stored', []))} סמלים | status {res.get('status')} | err {res.get('err')}")
    print(f"\n══ ניקוי סמלים מושחתים מ-{LIST} ══")
    sanitize_list(LIST)

    print(f"\n══ שלב 4: copy2L — {LIST} → CoffeeL ══")
    copy2L(LIST)
    sanitize_list('CoffeeL')
    print("\n✅ brew small_cap_gainers הושלם.")


def bz_gainers():
    """brew Gainers — Benzinga Gainers → dw_skill_bz_gainers → CoffeeL (LONG).
    מקור: WebFetch על https://www.benzinga.com/movers (שיטת הפרויקט — 'Benzinga is the working source').
    WebFetch הוא כלי צד-עוזר ולא נגיש מפייתון, לכן העוזר ממלא את הטיקרים מראש ל-_bz_gainers.json,
    והפונקציה הזו קוראת משם ומבצעת: ניקוי → הוספה (שיטת dayscan_pivot) → sanitize → copy2L.
    """
    import os
    LIST = 'dw_skill_bz_gainers'
    SRC_FILE = r'C:\Users\nsyon\SCAN\_bz_gainers.json'

    if not ensure_tv():
        print("ERROR: אין תקשורת ל-TradingView — עוצר.")
        return

    if not os.path.exists(SRC_FILE):
        print(f"ERROR: אין {SRC_FILE} — העוזר צריך למשוך מ-Benzinga (WebFetch) ולכתוב טיקרים לקובץ.")
        return
    try:
        syms = json.load(open(SRC_FILE, encoding='utf-8'))
    except Exception as e:
        print(f"ERROR קריאת {SRC_FILE}: {e}")
        return
    if not syms:
        print("הקובץ ריק — אין טיקרים.")
        return
    print(f"נקראו {len(syms)} טיקרים מ-Benzinga: {syms}")

    # שלב הניקוי הוסר — set_list עושה REST replace שדורס את כל הרשימה ממילא

    print(f"\n══ שלב 3: פתרון exchange + הכנסה ל-{LIST} (REST set_list) ══")
    qsyms = qualify_tickers(syms)
    print(f"  סמלים מלאים: {qsyms}")
    res = set_list(LIST, qsyms)
    print(f"  נכתבו {len(res.get('stored', []))} סמלים | status {res.get('status')} | err {res.get('err')}")
    sanitize_list(LIST)

    print(f"\n══ שלב 4: copy2L — {LIST} → CoffeeL ══")
    copy2L(LIST)
    sanitize_list('CoffeeL')
    print("\n✅ brew Gainers (Benzinga) הושלם.")


def bz_losers():
    """brew Losers — Benzinga Losers → dw_skill_bz_losers → CoffeeS (SHORT).
    מקור: WebFetch על https://www.benzinga.com/movers (צד יורדות). הטיקרים מסופקים מראש
    ל-_bz_losers.json (WebFetch הוא כלי צד-עוזר). זרימה: פתרון exchange → set_list → sanitize → copy2S.
    """
    import os
    LIST = 'dw_skill_bz_losers'
    SRC_FILE = r'C:\Users\nsyon\SCAN\_bz_losers.json'

    if not ensure_tv():
        print("ERROR: אין תקשורת ל-TradingView — עוצר.")
        return
    if not os.path.exists(SRC_FILE):
        print(f"ERROR: אין {SRC_FILE} — העוזר צריך למשוך מ-Benzinga (WebFetch) ולכתוב טיקרים לקובץ.")
        return
    try:
        syms = json.load(open(SRC_FILE, encoding='utf-8'))
    except Exception as e:
        print(f"ERROR קריאת {SRC_FILE}: {e}")
        return
    if not syms:
        print("הקובץ ריק — אין טיקרים.")
        return
    print(f"נקראו {len(syms)} טיקרים מ-Benzinga: {syms}")

    print(f"\n══ שלב 3: פתרון exchange + הכנסה ל-{LIST} (REST set_list) ══")
    qsyms = qualify_tickers(syms)
    print(f"  סמלים מלאים: {qsyms}")
    res = set_list(LIST, qsyms)
    print(f"  נכתבו {len(res.get('stored', []))} סמלים | status {res.get('status')} | err {res.get('err')}")
    sanitize_list(LIST)

    print(f"\n══ שלב 4: copy2S — {LIST} → CoffeeS ══")
    copy2S(LIST)
    sanitize_list('CoffeeS')
    print("\n✅ brew Losers (Benzinga) הושלם.")


def day_losers():
    """brew day_losers — סקיל-איסוף SHORT מ-Yahoo day_losers.
    ensure_tv → ניקוי dw_skill_losers → משיכה+הכנסה → sanitize → copy2S → CoffeeS.
    """
    LIST = 'dw_skill_losers'
    if not ensure_tv():
        print("ERROR: אין תקשורת ל-TradingView — עוצר.")
        return
    # שלב הניקוי הוסר — set_list עושה REST replace שדורס את כל הרשימה ממילא
    print(f"\n══ שלב 3: משיכת day_losers מ-Yahoo ══")
    syms = fetch_yahoo_q('day_losers')
    print(f"נמשכו {len(syms)} טיקרים: {syms}")
    if not syms:
        print("אין טיקרים מ-Yahoo — עוצר.")
        return
    print(f"\n══ הכנסה ל-{LIST} (REST set_list — מהיר ואמין) ══")
    res = set_list(LIST, syms)
    print(f"  נכתבו {len(res.get('stored', []))} סמלים | status {res.get('status')} | err {res.get('err')}")
    print(f"\n══ ניקוי סמלים מושחתים מ-{LIST} ══")
    sanitize_list(LIST)
    print(f"\n══ שלב 4: copy2S — {LIST} → CoffeeS ══")
    copy2S(LIST)
    sanitize_list('CoffeeS')
    print("\n✅ brew day_losers הושלם.")


def _copy_append(src, dst):
    """העתקה אמינה דרך REST: dst := dst ∪ src (שומר קיים, מוסיף חדשים, dedup).
    לא תלוי בלולאת UI/החלפת watchlist (שנכשלת על ליסט ריק). מחזיר dict תוצאה."""
    pages = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    page = next(p for p in pages if 'tradingview.com' in p.get('url', ''))
    ws = websocket.create_connection(page['webSocketDebuggerUrl'], timeout=20, header={'Origin': 'http://localhost'})
    mid = [1]
    def run_js(code, await_promise=False):
        m = mid[0]; mid[0] += 1
        ws.send(json.dumps({'id': m, 'method': 'Runtime.evaluate', 'params': {'expression': code, 'returnByValue': True, 'awaitPromise': await_promise}}))
        for _ in range(120):
            r = json.loads(ws.recv())
            if r.get('id') == m:
                return r.get('result', {}).get('result', {}).get('value', '')
        return 'timeout'
    raw = run_js("""
(async function(){
  var lists = await (await fetch('/api/v1/symbols_list/custom/',{credentials:'include'})).json();
  var S = lists.find(function(l){ return l.name === '""" + src + """'; });
  var D = lists.find(function(l){ return l.name === '""" + dst + """'; });
  if(!S) return JSON.stringify({err:'src_not_found'});
  if(!D) return JSON.stringify({err:'dst_not_found'});
  var out = (D.symbols||[]).slice(); var seen={}; out.forEach(function(s){ seen[s]=1; });
  var added=[];
  (S.symbols||[]).forEach(function(s){ if(!seen[s]){ seen[s]=1; out.push(s); added.push(s); } });
  var r = await fetch('/api/v1/symbols_list/custom/'+D.id+'/replace/?unsafe=true',{
    method:'POST', credentials:'include',
    headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
    body: JSON.stringify(out)
  });
  return JSON.stringify({added:added.length, total:out.length, status:r.status});
})()
""", await_promise=True)
    ws.close()
    try:
        res = json.loads(raw) if raw and raw != 'timeout' else {'err': 'timeout'}
    except Exception:
        res = {'err': 'parse'}
    return res


def copy2L(src):
    """מעתיק את src → CoffeeL דרך REST (מוסיף לקיים, dedup)."""
    res = _copy_append(src, 'CoffeeL')
    if res.get('err'):
        print(f"copy2L ERROR: {res['err']}")
    else:
        print(f"copy2L — נוספו {res['added']} מ-{src} → CoffeeL (סה\"כ {res['total']})")

def copy2S(src):
    """מעתיק את src → CoffeeS דרך REST (מוסיף לקיים, dedup)."""
    res = _copy_append(src, 'CoffeeS')
    if res.get('err'):
        print(f"copy2S ERROR: {res['err']}")
    else:
        print(f"copy2S — נוספו {res['added']} מ-{src} → CoffeeS (סה\"כ {res['total']})")


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════
_FUNCS = {'clean': clean, 'cleanL': cleanL, 'cleanS': cleanS, 'demoL': demoL, 'demoS': demoS,
          'day_gainers': day_gainers,
          'small_cap_gainers': small_cap_gainers,
          'Gainers': bz_gainers,
          'day_losers': day_losers,
          'Losers': bz_losers,
          'copy2L': lambda: copy2L(sys.argv[2] if len(sys.argv) > 2 else ''),
          'copy2S': lambda: copy2S(sys.argv[2] if len(sys.argv) > 2 else '')}

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd in _FUNCS:
        _FUNCS[cmd]()
    else:
        print("שימוש: python brew.py [clean|cleanL|cleanS|demoL|demoS|day_gainers|small_cap_gainers|Gainers|day_losers|Losers|copy2L <src>|copy2S <src>]")
