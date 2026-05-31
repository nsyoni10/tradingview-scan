import requests, sys, warnings, time
from datetime import datetime
import xml.etree.ElementTree as ET
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

now = datetime.now().strftime("%Y-%m-%d %H:%M")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def fetch(sym):
    try:
        u = "https://query1.finance.yahoo.com/v8/finance/chart/"+sym+"?interval=1d&range=5d"
        m = requests.get(u,headers=H,verify=False,timeout=15).json()["chart"]["result"][0]["meta"]
        p = m.get("regularMarketPrice") or m.get("previousClose",0)
        c = m.get("chartPreviousClose") or m.get("regularMarketPreviousClose") or m.get("previousClose",p)
        if not p or p==0: return {"p":0,"chg":0,"ok":False}
        chg = round((p-c)/c*100,2) if c and c!=0 else 0
        return {"p":round(p,2),"chg":chg,"ok":True}
    except:
        return {"p":0,"chg":0,"ok":False}

_cache = {}
def translate_he(text):
    if not text or len(text)<4: return text
    if text in _cache: return _cache[text]
    try:
        from urllib.parse import quote
        url = "https://api.mymemory.translated.net/get?q="+quote(text[:400])+"&langpair=en|he"
        r = requests.get(url,verify=False,timeout=10)
        res = r.json()["responseData"]["translatedText"]
        if res and len(res)>3 and res!=text and not res.startswith("MYMEMORY"):
            _cache[text] = res
            return res
        return text
    except:
        return text

def fetch_rss(url, label):
    try:
        r = requests.get(url,headers=H,verify=False,timeout=10)
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:8]:
            t = item.find("title")
            d = item.find("description")
            if t is not None and t.text:
                items.append({"title":t.text.strip(),"desc":(d.text.strip()[:150] if d is not None and d.text else ""),"source":label})
        return items
    except:
        return []

# ---- שליפת נתונים ----
print("מביא נתוני שוק...")
sp   = fetch("^GSPC")
qq   = fetch("QQQ")
vx   = fetch("^VIX")
ol   = fetch("CL=F")
gold = fetch("GC=F")
bond = fetch("^TNX")
es   = fetch("ES=F")
nq   = fetch("NQ=F")
ym   = fetch("YM=F")
rty  = fetch("RTY=F")

sp_chg=sp["chg"]; qq_chg=qq["chg"]; vix_val=vx["p"]; oil_chg=ol["chg"]
print(f"S&P:{sp['p']} | QQQ:{qq['p']} | VIX:{vix_val} | נפט:{ol['p']} | זהב:{gold['p']} | אגח10Y:{bond['p']}%")
print(f"ES:{es['p']} ({es['chg']:+.2f}%) | NQ:{nq['p']} ({nq['chg']:+.2f}%) | YM:{ym['p']} ({ym['chg']:+.2f}%) | RTY:{rty['p']} ({rty['chg']:+.2f}%)")

# ---- חישוב ציון ודגל (מ-coffee.py) ----
ds=0
for v,mx in [(sp_chg,25),(qq_chg,20)]:
    if v>=1:ds+=mx
    elif v>=0.5:ds+=int(mx*0.72)
    elif v>=0:ds+=int(mx*0.32)
    elif v>=-0.5:ds-=int(mx*0.2)
    elif v>=-1:ds-=int(mx*0.6)
    else:ds-=mx

vv=vix_val
if vv<15:ds+=20
elif vv<18:ds+=14
elif vv<22:ds+=5
elif vv<25:ds-=5
elif vv<30:ds-=15
else:ds-=20

oa=abs(oil_chg)
if oa<1:ds+=10
elif oa<2:ds+=5
elif oa<4:ds-=5
else:ds-=10

sc=max(0,min(100,int(50+(ds/75)*50)))

configs = [
    (75,"GREEN", 10,0, 3.0,0,  "#00cc66","#0d2b1a","🟢 ירוק — שוק חזק",  "שוק חזק! כנס LONG בביטחון"),
    (60,"WHITE",  8,2, 2.0,1.0,"#e0e0e0","#1a1a2e","⬜ לבן — שוק בריא",  "שוק בריא, העדף LONG"),
    (45,"YELLOW", 5,5, 0.5,0.5,"#ffd700","#2a2200","🟡 צהוב — זהירות",   "מבולבל — מינוף נמוך"),
    (30,"ORANGE", 2,8, 1.0,2.0,"#ff8c00","#2a1500","🟠 כתום — שוק חלש", "שוק יורד — העדף SHORT"),
    (15,"RED",    0,10,0,  3.0,"#ff4444","#2a0d0d","🔴 אדום — שוק רע",   "SHORT בלבד!"),
    (0, "BLACK",  0,0, 0,  0,  "#888",   "#111",   "⬛ שחור — סכנה!",    "אל תיכנס היום!"),
]
for thr,fl,lc,sc2,ll,sl_lev,fc,fb,fh,fm in configs:
    if sc >= thr: break

EM={"GREEN":"🟢","WHITE":"⬜","YELLOW":"🟡","ORANGE":"🟠","RED":"🔴","BLACK":"⬛"}
em=EM[fl]
if vv>=30: ll=min(ll,1.0);sl_lev=min(sl_lev,1.0);fm+=" | VIX גבוה — הגבל מינוף"
ll2="x"+str(ll) if ll>0 else "---"
sl2="x"+str(sl_lev) if sl_lev>0 else "---"

# ---- חדשות ----
print("מביא חדשות...")
all_news = []
all_news += fetch_rss("https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US","יאהו פיננס")
all_news += fetch_rss("https://feeds.finance.yahoo.com/rss/2.0/headline?s=CL=F&region=US&lang=en-US","חדשות נפט")
all_news += fetch_rss("https://feeds.finance.yahoo.com/rss/2.0/headline?s=^VIX&region=US&lang=en-US","חדשות VIX")
all_news += fetch_rss("https://www.cnbc.com/id/100003114/device/rss/rss.html","CNBC")
all_news += fetch_rss("https://feeds.marketwatch.com/marketwatch/topstories/","MarketWatch")
print(f"סך כותרות: {len(all_news)}")

# ---- ניתוח ----
alerts=[]; watch=[]; good=[]
if abs(oil_chg)>=5:
    d="עלייה חדה" if oil_chg>0 else "ירידה חדה"
    alerts.append(f"🛢️ נפט: {d} של {abs(oil_chg):.1f}% — בדוק חדשות גיאופוליטיות")
    if oil_chg<-5: watch.append("ירידת נפט חדה = ירידה בציפיות אינפלציה = טוב לשוק המניות")
    else: watch.append("עלייה חדה בנפט = לחץ אינפלציוני = רע לשוק המניות")
elif abs(oil_chg)>=2:
    alerts.append(f"🛢️ נפט: {oil_chg:+.1f}% — תנועה משמעותית, שים עין")

if vv>=30:   alerts.append(f"⚠️ VIX {vv} — פחד קיצוני! הקטן פוזיציות ל-x1")
elif vv>=25: alerts.append(f"⚠️ VIX {vv} — חשש בשוק, הזהר ממינוף גבוה")
elif vv>=20: watch.append(f"VIX {vv} — מעט מוגבר, היה ערני")
elif vv<15:  good.append(f"✅ VIX {vv} — שוק רגוע מאוד, מינוף מלא מותר")

if bond["ok"] and bond["p"]>0:
    bc=bond["chg"]
    if bc>=3:   alerts.append(f"📊 אגח 10Y עלה {bc:+.1f}% ({bond['p']}%) — לחץ על מניות טק")
    elif bc<=-3: good.append(f"📊 אגח 10Y ירד {bc:+.1f}% ({bond['p']}%) — תמיכה בטק")
    else:        watch.append(f"📊 אגח 10Y: {bond['p']}% (שינוי {bc:+.1f}%)")

if gold["ok"] and gold["p"]>0:
    gc=gold["chg"]
    if gc>=1.5:   alerts.append(f"🥇 זהב עולה {gc:+.1f}% (${gold['p']:,}) — חשש גיאופוליטי")
    elif gc<=-1.5: good.append(f"🥇 זהב יורד {gc:+.1f}% (${gold['p']:,}) — אמון בשוק")

if abs(sp_chg-qq_chg)>=1.5:
    if qq_chg>sp_chg: good.append("טק (QQQ) מוביל — כוח בצמיחה")
    else: watch.append("S&P חזק מ-QQQ — רוטציה לסקטורים ערך")

if es["chg"]>=0.5: good.append(f"📈 ES=F {es['chg']:+.1f}% — פתיחה חיובית צפויה")
elif es["chg"]<=-0.5: alerts.append(f"📉 ES=F {es['chg']:+.1f}% — פתיחה שלילית, הזהר")

if nq["chg"]>es["chg"]+0.5: good.append(f"💻 NQ=F {nq['chg']:+.1f}% מוביל — יום טכנולוגיה חזק ל-LONG")
elif nq["chg"]<es["chg"]-0.5: watch.append(f"💻 NQ=F {nq['chg']:+.1f}% פגור — רוטציה לסקטורים ערך")

if rty["chg"]>=1.0: good.append(f"🏘️ RTY=F {rty['chg']:+.1f}% — תיאבון סיכון גבוה, טוב לסטאפים!")
elif rty["chg"]<=-1.0: watch.append(f"🏘️ RTY=F {rty['chg']:+.1f}% — בריחה מסיכון, הקטן פוזיציות")

# ---- נושאי חדשות ----
kw_map={"fed":"🏦 Fed/ריבית","rate":"📈 ריבית","inflation":"🔥 אינפלציה","recession":"📉 מיתון",
         "war":"⚔️ מלחמה","oil":"🛢️ נפט","china":"🇨🇳 סין","tariff":"💰 מכסים",
         "earnings":"📋 דיווחי רווחים","crash":"🚨 קריסה","opec":"🛢️ OPEC",
         "ukraine":"🇺🇦 אוקראינה","israel":"🇮🇱 ישראל","trump":"🇺🇸 טראמפ","jobs":"👷 תעסוקה"}
found_kw={}
for item in all_news:
    txt=(item["title"]+" "+item["desc"]).lower()
    for kw,lbl in kw_map.items():
        if kw in txt and kw not in found_kw:
            found_kw[kw]={"label":lbl,"headline":item["title"][:80]}

# ---- תרגום ----
print("מתרגם לעברית...")
seen=set(); headlines=[]
for item in all_news:
    t=item["title"][:90]
    if t not in seen and len(t)>20:
        seen.add(t)
        t_he=translate_he(t)
        time.sleep(0.3)
        desc=item.get("desc","")
        d_he=translate_he(desc) if desc and len(desc)>10 else ""
        if desc: time.sleep(0.3)
        headlines.append({"title":t_he,"desc":d_he,"src":item["source"]})
    if len(headlines)>=12: break

kw_items=[]
for kw,data in list(found_kw.items())[:8]:
    h_he=translate_he(data["headline"])
    time.sleep(0.2)
    kw_items.append(f'<div class="ki"><span class="kl">{data["label"]}</span><div class="kh">{h_he}</div></div>')

# ---- עוזרי HTML ----
def pct_color(v,inv=False):
    if inv: return "#ff4444" if v>=0 else "#00cc66"
    return "#00cc66" if v>=0 else "#ff4444"
def fmt_bond(v):
    if not v or v==0: return "N/A"
    return f"{v:.3f}%"
def ic(v,inv=False):
    if inv: return "✅" if v<18 else ("⚠️" if v<25 else "❌")
    return "✅" if v>=0.3 else ("⚠️" if v>=-0.3 else "❌")

sum_html=""
if alerts:
    sum_html+="<div class='ss'><div class='st2'>🚨 התראות חשובות</div>"
    for a in alerts: sum_html+=f"<div class='si alert'>{a}</div>"
    sum_html+="</div>"
if watch:
    sum_html+="<div class='ss'><div class='st2'>👁️ שים לב</div>"
    for w in watch: sum_html+=f"<div class='si watch'>• {w}</div>"
    sum_html+="</div>"
if good:
    sum_html+="<div class='ss'><div class='st2'>✅ נקודות חיוביות</div>"
    for g in good: sum_html+=f"<div class='si good'>{g}</div>"
    sum_html+="</div>"
if not alerts and not watch and not good:
    sum_html="<div class='si good'>✅ שוק יציב — אין התראות מיוחדות היום</div>"

hl_html=""
src_colors={"יאהו פיננס":"#8888ff","חדשות נפט":"#ff8c00","CNBC":"#ff4444","MarketWatch":"#00cc66","חדשות VIX":"#ffd700"}
for h in headlines:
    sc_=src_colors.get(h["src"],"#666")
    dh=f'<div class="hd">{h["desc"]}</div>' if h.get("desc") else ""
    hl_html+=f'<div class="hi"><span class="hs" style="background:{sc_}22;color:{sc_}">{h["src"]}</span><div class="hb"><div class="ht">{h["title"]}</div>{dh}</div></div>'

kw_html="".join(kw_items) if kw_items else "<div style='color:#555'>לא נמצאו נושאים מיוחדים</div>"

FUTURES=[
    ("ES=F",es,"S&P 500 עתידי","כיוון כללי — פתיחת שוק"),
    ("NQ=F",nq,'נאסד"ק עתידי',"כיוון מניות הטכנולוגיה"),
    ("YM=F",ym,"דאו ג'ונס עתידי","שוק מסורתי — בנקים ותעשייה"),
    ("RTY=F",rty,"ראסל 2000 עתידי","מד סיכון — מניות קטנות"),
]
fut_rows=""
for sym_,d_,name_,desc_ in FUTURES:
    clr=pct_color(d_["chg"])
    p_s=f"${d_['p']:,}" if d_["ok"] else "N/A"
    c_s=f"{d_['chg']:+.2f}%" if d_["ok"] else "N/A"
    fut_rows+=f"<tr><td style='padding:11px 14px;border-bottom:1px solid #1a1a2a;font-weight:bold;color:#aaaaff;font-size:16px'>{sym_}</td><td style='padding:11px 14px;border-bottom:1px solid #1a1a2a'>{name_}</td><td style='padding:11px 14px;border-bottom:1px solid #1a1a2a;font-weight:bold'>{p_s}</td><td style='padding:11px 14px;border-bottom:1px solid #1a1a2a;font-weight:bold;color:{clr}'>{c_s}</td><td style='padding:11px 14px;border-bottom:1px solid #1a1a2a;font-size:12px;color:#888'>{desc_}</td></tr>"

macro_note=""
dow=datetime.now().weekday()
if dow==4: macro_note="⚠️ יום שישי — נזילות נמוכה אחה\"צ, הזהר ממינוף גבוה"
elif dow==0: macro_note="📅 יום שני — Gap שבועי אפשרי, המתן ל-9:45 EST"

# ---- HTML מאוחד ----
html=f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<title>☕ Coffee — {now}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Segoe UI,Arial,sans-serif;background:#0d0d1a;color:#e0e0e0;padding:24px;direction:rtl}}
.C{{background:#12122a;border-radius:14px;padding:20px 24px;margin-bottom:20px}}
.ST{{font-size:16px;color:#8888cc;font-weight:bold;margin-bottom:14px;border-bottom:1px solid #333;padding-bottom:6px}}
.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.metric{{background:#1a1a2e;border-radius:10px;padding:14px;text-align:center}}
.mp{{font-size:26px;font-weight:bold;margin-bottom:4px}}
.mc{{font-size:16px;font-weight:bold;margin-bottom:4px}}
.ml{{font-size:14px;color:#e0e0e0;margin-top:2px;font-weight:bold}}
.BW{{background:#222;border-radius:6px;height:16px;width:100%;margin:10px 0}}
.BF{{height:16px;border-radius:6px;background:{fc};width:{sc}%}}
.RB{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-top:4px}}
.RI{{background:#1a1a2e;border-radius:10px;padding:16px;text-align:center}}
.ss{{margin-bottom:16px}}
.st2{{font-size:14px;color:#aaa;font-weight:bold;margin-bottom:8px}}
.si{{padding:10px 14px;border-radius:8px;margin-bottom:8px;font-size:14px;line-height:1.6}}
.si.alert{{background:#2a0d0d;border-left:3px solid #ff4444;color:#ffaaaa}}
.si.watch{{background:#2a1f0d;border-left:3px solid #ffd700;color:#ffe9aa}}
.si.good{{background:#0d2a1a;border-left:3px solid #00cc66;color:#aaffcc}}
.ki{{background:#1a1a2e;border-radius:8px;padding:10px 14px;margin-bottom:8px}}
.kl{{font-size:12px;font-weight:bold;color:#8888cc;display:block;margin-bottom:4px}}
.kh{{font-size:13px;color:#ccc;line-height:1.4}}
.hi{{padding:10px 14px;border-bottom:1px solid #1a1a2a;display:flex;align-items:flex-start;gap:10px}}
.hs{{font-size:10px;padding:3px 8px;border-radius:4px;white-space:nowrap;margin-top:2px;flex-shrink:0;font-weight:bold}}
.hb{{flex:1}}
.ht{{font-size:13px;color:#ccc;font-weight:bold;line-height:1.4}}
.hd{{font-size:12px;color:#888;line-height:1.5;margin-top:4px}}
table{{width:100%;border-collapse:collapse}}
th{{background:#1e1e3a;color:#8888cc;padding:10px 14px;text-align:right;font-size:12px;border-bottom:1px solid #333}}
.MB{{border:1px solid {fc};border-radius:10px;padding:14px 20px;font-size:18px;color:{fc};font-weight:bold;text-align:center;margin-top:16px;background:{fb}}}
</style>
</head>
<body>

<!-- כותרת + דגל -->
<div class="C">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">
    <div>
      <div style="font-size:30px;font-weight:bold;color:#aaaaff">☕ Coffee — סקירת שוק יומית</div>
      <div style="font-size:13px;color:#555;margin-top:6px">{now} | יאהו פיננס · CNBC · MarketWatch</div>
    </div>
    <div style="border:2px solid {fc};border-radius:14px;padding:18px 32px;text-align:center;background:{fb}">
      <div style="font-size:72px;line-height:1">{em}</div>
      <div style="font-size:18px;font-weight:bold;color:{fc};margin-top:8px">{fh}</div>
    </div>
  </div>
  <div style="margin-top:18px">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="color:#888;font-size:13px">0 — מסוכן</span>
      <span style="font-size:36px;font-weight:bold;color:{fc}">{sc}/100</span>
      <span style="color:#888;font-size:13px">100 — חזק</span>
    </div>
    <div class="BW"><div class="BF"></div></div>
  </div>
</div>

{"<div class='C'><div style='background:#1e1e3a;border:1px solid #444;border-radius:8px;padding:10px 16px;font-size:13px;color:#aaa'>"+macro_note+"</div></div>" if macro_note else ""}

<!-- המלצה -->
<div class="C">
  <div class="ST">🎯 המלצה להיום</div>
  <div class="RB">
    <div class="RI" style="border:1px solid #00cc6644">
      <div style="font-size:40px;font-weight:bold;color:#00cc66">{lc}</div>
      <div style="font-size:15px;color:#e0e0e0;margin-top:6px;font-weight:bold">📈 לונג</div>
      <div style="font-size:32px;font-weight:bold;color:#00cc66;margin-top:8px">{ll2}</div>
      <div style="font-size:15px;color:#e0e0e0;font-weight:bold">מינוף</div>
    </div>
    <div class="RI" style="border:1px solid #ff444444">
      <div style="font-size:40px;font-weight:bold;color:#ff4444">{sc2}</div>
      <div style="font-size:15px;color:#e0e0e0;margin-top:6px;font-weight:bold">📉 שורט</div>
      <div style="font-size:32px;font-weight:bold;color:#ff4444;margin-top:8px">{sl2}</div>
      <div style="font-size:15px;color:#e0e0e0;font-weight:bold">מינוף</div>
    </div>
    <div class="RI" style="border:1px solid {fc}44">
      <div style="font-size:64px;line-height:1">{em}</div>
      <div style="font-size:15px;color:#e0e0e0;margin-top:8px;font-weight:bold">{fh.split('—')[0].strip()}</div>
      <div style="font-size:16px;color:{fc};font-weight:bold;margin-top:4px">{sc}/100</div>
    </div>
  </div>
  <div class="MB">{fm}</div>
</div>

<!-- מדדים -->
<div class="C">
  <div class="ST">📊 מדדים מרכזיים</div>
  <div class="metrics">
    <div class="metric">
      <div class="mp">${sp['p']:,}</div>
      <div class="mc" style="color:{pct_color(sp_chg)}">{sp_chg:+.2f}%</div>
      <div class="ml">מדד S&P 500 {ic(sp_chg)}</div>
    </div>
    <div class="metric">
      <div class="mp">${qq['p']:,}</div>
      <div class="mc" style="color:{pct_color(qq_chg)}">{qq_chg:+.2f}%</div>
      <div class="ml">נאסד"ק QQQ {ic(qq_chg)}</div>
    </div>
    <div class="metric">
      <div class="mp">{vx['p']}</div>
      <div class="mc" style="color:{pct_color(vx['chg'],inv=True)}">{vx['chg']:+.2f}%</div>
      <div class="ml">VIX — מדד פחד {ic(vv,inv=True)}</div>
    </div>
    <div class="metric">
      <div class="mp">${ol['p']}</div>
      <div class="mc" style="color:{pct_color(oil_chg)}">{oil_chg:+.2f}%</div>
      <div class="ml">🛢️ נפט גולמי</div>
    </div>
    <div class="metric">
      <div class="mp">{"${:,}".format(gold['p']) if gold['ok'] else "N/A"}</div>
      <div class="mc" style="color:{pct_color(gold['chg']) if gold['ok'] else '#666'}">{"" + f"{gold['chg']:+.2f}%" if gold['ok'] else "---"}</div>
      <div class="ml">🥇 זהב</div>
    </div>
    <div class="metric">
      <div class="mp">{fmt_bond(bond['p'])}</div>
      <div class="mc" style="color:{pct_color(bond['chg'],inv=True) if bond['ok'] else '#666'}">{"" + f"{bond['chg']:+.2f}%" if bond['ok'] else "---"}</div>
      <div class="ml">📊 אגח 10Y</div>
    </div>
  </div>
</div>

<!-- חוזים עתידיים -->
<div class="C">
  <div class="ST">⚡ חוזים עתידיים</div>
  <table>
    <thead><tr><th>טיקר</th><th>שם</th><th>מחיר</th><th>שינוי</th><th>למה חשוב</th></tr></thead>
    <tbody>{fut_rows}</tbody>
  </table>
</div>

<!-- ניתוח -->
<div class="C">
  <div class="ST">🧠 ניתוח שוק</div>
  {sum_html}
</div>

<!-- נושאים -->
<div class="C">
  <div class="ST">🔍 נושאים בחדשות</div>
  {kw_html}
</div>

<!-- כותרות בעברית -->
<div class="C">
  <div class="ST">📰 כותרות מובילות — עברית</div>
  {hl_html}
</div>

<div style="text-align:center;color:#333;font-size:11px;margin-top:10px">
  ☕ Coffee | {now} | יאהו פיננס · CNBC · MarketWatch · MyMemory
</div>
</body>
</html>"""

with open("C:/Users/nsyon/SCAN/coffee.html","w",encoding="utf-8") as f:
    f.write(html)

print("\n"+"="*45)
print(f"{em} {fh} | ציון: {sc}/100")
print(f"LONG: {lc} {ll2} | SHORT: {sc2} {sl2}")
print(fm)
if alerts:
    print("🚨 " + " | ".join(alerts[:2]))
print("="*45)
print("נשמר: C:\\Users\\nsyon\\SCAN\\coffee.html")
