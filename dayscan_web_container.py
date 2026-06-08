# -*- coding: utf-8 -*-
"""
dayscan_web_container.py — קונטיינר dayscan_web (דמו)
=====================================================
אחראי על *כל* התקשורת ל-TradingView והכתיבה אליו.
הסקילים רק אוספים טיקרים ומחזירים רשימה — הקונטיינר מנקה, כותב ומעתיק.
אין כאן סינון/דירוג — זה קורה במורד הזרם (dayscan_pivot + 2 הסקרינרים).

קוד גנרי (DRY): 2 פרימיטיבים בלבד — clean_list() ו-copy_list() —
וכל שאר הפונקציות הן wrappers דקים עליהם.
"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from tv_switch_dayscan import connect_tv, make_runner   # ← ממחזרים את החיבור הקיים

# ── הגדרות: שמות הליסטים ב-TradingView ────────────────────────────────────────
# (לאשר/לעדכן לשמות האמיתיים אצלך לפני הרצה חיה)
LONG_LIST    = "DW_LONG"    # ליסט מצטבר ללונג  → הסקרינר CoffeeL יקרא ממנו
SHORT_LIST   = "DW_SHORT"   # ליסט מצטבר לשורט  → הסקרינר CoffeeS יקרא ממנו
WORKING_LIST = "DW_WORK"    # הליסט שעובדים עליו (כל סקיל ממלא אותו זמנית)

# ── חיבור ─────────────────────────────────────────────────────────────────────
_ws = None
_run = None

def connect():
    global _ws, _run
    _ws = connect_tv()
    _run = make_runner(_ws)
    return _run

def close():
    if _ws:
        _ws.close()

# ── תבנית REST גנרית: מוצאת ליסט לפי שם ומבצעת replace ────────────────────────
def _replace(name, body_js):
    """body_js = ביטוי JS שמייצר את גוף ה-POST (מערך סמלים או [])."""
    js = """
(async function(){
  try{
    var lists = await (await fetch('/api/v1/symbols_list/custom/',{credentials:'include'})).json();
    var L = lists.find(function(l){ return l.name === %s; });
    if(!L) return 'not_found';
    var body = %s;
    var r = await fetch('/api/v1/symbols_list/custom/'+L.id+'/replace/?unsafe=true',{
      method:'POST', credentials:'include',
      headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
      body: JSON.stringify(body)
    });
    return r.status===200 ? 'ok_'+body.length : 'err_'+r.status;
  }catch(e){ return 'ex:'+e.message; }
})()
""" % (json.dumps(name), body_js)
    return _run(js, await_promise=True)

# ── פרימיטיב 1: ניקוי ליסט (replace עם []) ────────────────────────────────────
def clean_list(name):
    return _replace(name, "[]")

# ── פרימיטיב 2: העתקה בין ליסטים (קריאת המקור server-side + replace ליעד) ──────
def copy_list(src, dst):
    js = """
(async function(){
  try{
    var lists = await (await fetch('/api/v1/symbols_list/custom/',{credentials:'include'})).json();
    var S = lists.find(function(l){ return l.name === %s; });
    var D = lists.find(function(l){ return l.name === %s; });
    if(!S) return 'src_not_found';
    if(!D) return 'dst_not_found';
    var syms = S.symbols || [];
    var r = await fetch('/api/v1/symbols_list/custom/'+D.id+'/replace/?unsafe=true',{
      method:'POST', credentials:'include',
      headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
      body: JSON.stringify(syms)
    });
    return r.status===200 ? 'copied_'+syms.length : 'err_'+r.status;
  }catch(e){ return 'ex:'+e.message; }
})()
""" % (json.dumps(src), json.dumps(dst))
    return _run(js, await_promise=True)

# ── כתיבת טיקרים גולמיים לליסט (למילוי ה-working מ-bare tickers) ───────────────
def set_list(name, symbols):
    return _replace(name, json.dumps(symbols))

# ── Wrappers נדרשים (רוח הדברים שביקשת) ───────────────────────────────────────
def clean_long_list():       return clean_list(LONG_LIST)
def clean_short_list():      return clean_list(SHORT_LIST)
def clean_working_list():    return clean_list(WORKING_LIST)
def copy_working_to_long():  return copy_list(WORKING_LIST, LONG_LIST)
def copy_working_to_short(): return copy_list(WORKING_LIST, SHORT_LIST)

# ── רישום סקילים: שם → (פונקציית איסוף, כיוון) ────────────────────────────────
# כאן "נקבע לכל סקיל" לאיזה ליסט הוא מעתיק. להוסיף/להסיר מקור = שורה אחת.
import dw_skill_gainers
SKILLS = {
    'gainers': (dw_skill_gainers.fetch, 'long'),
    # בהמשך:
    # 'losers':       (dw_skill_losers.fetch,      'short'),
    # 'most_active':  (dw_skill_most_active.fetch, 'long'),
    # 'most_watched': (dw_skill_most_watched.fetch,'long'),
}

# ── הרצת סקיל בודד: ניקוי working → איסוף → כתיבה → העתקה לכיוון ───────────────
def run_skill(name):
    fetch, direction = SKILLS[name]
    print(f"\n▶ סקיל '{name}'  (כיוון: {direction})")
    print("  ניקוי working list  :", clean_working_list())
    tickers = fetch()                          # הסקיל אוסף בלבד
    print(f"  נאספו {len(tickers)} טיקרים   : {tickers[:12]}{'...' if len(tickers)>12 else ''}")
    print("  כתיבה ל-working list:", set_list(WORKING_LIST, tickers))
    copy = copy_working_to_long if direction == 'long' else copy_working_to_short
    print(f"  העתקה working → {direction.upper():5}:", copy())

# ── דיספצ'ר ראשי ──────────────────────────────────────────────────────────────
def run(param='long'):
    """param: 'long' / 'short' / שם סקיל. דמו: מריץ את gainers."""
    connect()
    try:
        print("== ניקוי ליסטים מצטברים (בעלות הקונטיינר, בתחילת ריצה) ==")
        print("  LONG :", clean_long_list())
        print("  SHORT:", clean_short_list())
        run_skill('gainers')      # דמו — הסקיל הראשון
    finally:
        close()
    print("\n✅ דמו הקונטיינר הושלם.")

if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'long')
