import requests, sys, warnings
from datetime import datetime
import xml.etree.ElementTree as ET
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

now = datetime.now().strftime("%Y-%m-%d %H:%M")
print("Coffee Market Conditions - " + now)
H = {"User-Agent": "Mozilla/5.0"}

def fetch(sym):
    try:
        u = "https://query1.finance.yahoo.com/v8/finance/chart/"+sym+"?interval=1d&range=5d"
        m = requests.get(u,headers=H,verify=False,timeout=15).json()["chart"]["result"][0]["meta"]
        p = m.get("regularMarketPrice") or m.get("previousClose")
        c = m.get("chartPreviousClose") or m.get("previousClose")
        return {"p":round(p,2),"chg":round((p-c)/c*100,2)}
    except:
        return {"p":0,"chg":0}

def get_news():
    try:
        u="https://feeds.finance.yahoo.com/rss/2.0/headline?s=SPY&region=US&lang=en-US"
        root=ET.fromstring(requests.get(u,headers=H,verify=False,timeout=10).content)
        return [t.text.strip() for t in root.findall(".//item/title") if t.text][:5]
    except:
        return ["No news available"]

sp=fetch("^GSPC"); qq=fetch("QQQ"); vx=fetch("^VIX"); ol=fetch("CL=F")
nw=get_news()
print("SP500:",sp["p"],sp["chg"],"% | QQQ:",qq["p"],qq["chg"],"%")
print("VIX:",vx["p"],vx["chg"],"% | OIL:",ol["p"],ol["chg"],"%")

ds=0
for v,mx in [(sp["chg"],25),(qq["chg"],20)]:
    if v>=1:ds+=mx
    elif v>=0.5:ds+=int(mx*0.72)
    elif v>=0:ds+=int(mx*0.32)
    elif v>=-0.5:ds-=int(mx*0.2)
    elif v>=-1:ds-=int(mx*0.6)
    else:ds-=mx

vv=vx["p"]
if vv<15:ds+=20
elif vv<18:ds+=14
elif vv<22:ds+=5
elif vv<25:ds-=5
elif vv<30:ds-=15
else:ds-=20

oa=abs(ol["chg"])
if oa<1:ds+=10
elif oa<2:ds+=5
elif oa<4:ds-=5
else:ds-=10

sc=max(0,min(100,int(50+(ds/75)*50)))

configs = [
    (75, "GREEN",  5,0,3.0,0,   "#00cc66","#0d2b1a","ירוק - שוק חזק",    "שוק חזק! LONG בביטחון"),
    (60, "WHITE",  4,1,2.0,1.0, "#e0e0e0","#1a1a2e","לבן - שוק בריא",    "שוק בריא, העדף LONG"),
    (45, "YELLOW", 2,2,0.5,0.5, "#ffd700","#2a2200","צהוב - זהירות",     "מבולבל - מינוף נמוך לכולם"),
    (30, "ORANGE", 1,4,1.0,2.0, "#ff8c00","#2a1500","כתום - שוק חלש",   "שוק יורד - העדף SHORT"),
    (15, "RED",    0,5,0,  3.0, "#ff4444","#2a0d0d","אדום - שוק רע",     "SHORT בלבד!"),
    (0,  "BLACK",  0,0,0,  0,   "#666",   "#111",   "שחור - סכנה!",      "אל תיכנס היום!"),
]
for thr,fl,lc,sc2,ll,sl_lev,fc,fb,fh,fm in configs:
    if sc >= thr: break

EM={"GREEN":"🟢","WHITE":"⬜","YELLOW":"🟡","ORANGE":"🟠","RED":"🔴","BLACK":"⬛"}
em=EM[fl]
if vv>=30: ll=min(ll,1.0);sl_lev=min(sl_lev,1.0);fm+=" | VIX גבוה"

def ic(k): return "✅" if k=="OK" else ("⚠️" if k=="WARN" else "❌")
def clr(v): return "#00cc66" if v>=0 else "#ff4444"
def vclr(v): return "#ff4444" if v>=0 else "#00cc66"
def sgn(v): return ("+" if v>=0 else "")+str(v)

si="OK" if sp["chg"]>=0.3 else ("WARN" if sp["chg"]>=-0.3 else "BAD")
qi="OK" if qq["chg"]>=0.3 else ("WARN" if qq["chg"]>=-0.3 else "BAD")
vi="OK" if vv<18 else ("WARN" if vv<25 else "BAD")
oi="OK" if abs(ol["chg"])<2 else ("WARN" if abs(ol["chg"])<4 else "BAD")

nl="".join("<li>"+n+"</li>" for n in nw)
ll2="x"+str(ll) if ll>0 else "---"
sl2="x"+str(sl_lev) if sl_lev>0 else "---"

h = []
h.append("<!DOCTYPE html><html lang=he dir=rtl><head><meta charset=UTF-8>")
h.append("<title>Coffee "+now+"</title><style>")
h.append("*{box-sizing:border-box;margin:0;padding:0}")
h.append("body{font-family:Segoe UI;background:#0d0d1a;color:#e0e0e0;padding:24px;direction:rtl}")
h.append(".C{background:#12122a;border-radius:14px;padding:20px 24px;margin-bottom:20px}")
h.append(".HH{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}")
h.append(".FB{border:2px solid "+fc+";border-radius:12px;padding:16px 28px;text-align:center;background:"+fb+"}")
h.append(".FT{font-size:16px;font-weight:bold;color:"+fc+";margin-top:6px}")
h.append(".BW{background:#222;border-radius:6px;height:14px;width:100%;margin:10px 0}")
h.append(".BF{height:14px;border-radius:6px;background:"+fc+";width:"+str(sc)+"%}")
h.append(".SN{font-size:38px;font-weight:bold;color:"+fc+";text-align:center}")
h.append("table{width:100%;border-collapse:collapse}")
h.append("th{background:#1e1e3a;color:#8888cc;padding:10px 14px;text-align:right;font-size:13px;border-bottom:1px solid #333}")
h.append("td{padding:12px 14px;border-bottom:1px solid #1a1a2a;font-size:15px}")
h.append(".RB{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-top:4px}")
h.append(".RI{background:#1a1a2e;border-radius:10px;padding:16px;text-align:center}")
h.append(".RN{font-size:34px;font-weight:bold}.RL{font-size:12px;color:#666;margin-top:4px}.LV{font-size:20px;font-weight:bold;margin-top:8px}")
h.append(".MB{border:1px solid "+fc+";border-radius:10px;padding:14px 20px;font-size:16px;color:"+fc+";font-weight:bold;text-align:center;margin-top:16px;background:"+fb+"}")
h.append(".ST{font-size:16px;color:#8888cc;font-weight:bold;margin-bottom:12px;border-bottom:1px solid #333;padding-bottom:6px}")
h.append("ul{padding-right:20px;margin-top:8px}li{margin-bottom:6px;color:#ccc}")
h.append("</style></head><body>")
h.append("<div class=C><div class=HH>")
h.append("<div><div style=font-size:28px;font-weight:bold>"+em+" Coffee</div>")
h.append("<div style=font-size:13px;color:#555;margin-top:4px>Market Conditions - "+now+"</div></div>")
h.append("<div class=FB><div style=font-size:48px>"+em+"</div><div class=FT>"+fh+"</div></div></div>")
h.append("<div style=margin-top:16px><div style=display:flex;justify-content:space-between;align-items:center>")
h.append("<span style=color:#888;font-size:13px>0 - מסוכן</span>")
h.append("<div class=SN>"+str(sc)+"/100</div>")
h.append("<span style=color:#888;font-size:13px>100 - חזק</span></div>")
h.append("<div class=BW><div class=BF></div></div></div></div>")
h.append("<div class=C><div class=ST>📊 מדדי שוק</div><table><thead><tr><th>מדד</th><th>מחיר</th><th>שינוי</th><th>סטטוס</th></tr></thead><tbody>")
h.append("<tr><td style=font-weight:bold>S&amp;P 500</td><td>$"+str(sp["p"])+"</td><td style=color:"+clr(sp["chg"])+";font-weight:bold>"+sgn(sp["chg"])+"%</td><td>"+ic(si)+"</td></tr>")
h.append("<tr><td style=font-weight:bold>QQQ</td><td>$"+str(qq["p"])+"</td><td style=color:"+clr(qq["chg"])+";font-weight:bold>"+sgn(qq["chg"])+"%</td><td>"+ic(qi)+"</td></tr>")
h.append("<tr><td style=font-weight:bold>VIX</td><td>"+str(vx["p"])+"</td><td style=color:"+vclr(vx["chg"])+";font-weight:bold>"+sgn(vx["chg"])+"%</td><td>"+ic(vi)+"</td></tr>")
h.append("<tr><td style=font-weight:bold>נפט</td><td>$"+str(ol["p"])+"</td><td style=color:"+clr(ol["chg"])+";font-weight:bold>"+sgn(ol["chg"])+"%</td><td>"+ic(oi)+"</td></tr>")
h.append("</tbody></table></div>")
h.append("<div class=C><div class=ST>🎯 המלצה להיום</div><div class=RB>")
h.append("<div class=RI style=border:1px solid #00cc6644><div class=RN style=color:#00cc66>"+str(lc)+"</div><div class=RL>📈 LONG</div><div class=LV style=color:#00cc66>"+ll2+"</div><div class=RL>מינוף</div></div>")
h.append("<div class=RI style=border:1px solid #ff444444><div class=RN style=color:#ff4444>"+str(sc2)+"</div><div class=RL>📉 SHORT</div><div class=LV style=color:#ff4444>"+sl2+"</div><div class=RL>מינוף</div></div>")
h.append("<div class=RI style=border:1px solid "+fc+"44><div style=font-size:44px>"+em+"</div><div class=RL style=margin-top:6px>"+fl+"</div><div style=font-size:14px;color:"+fc+";font-weight:bold;margin-top:4px>"+str(sc)+"/100</div></div></div>")
h.append("<div class=MB>"+fm+"</div></div>")
h.append("<div class=C><div class=ST>📰 חדשות שוק</div><ul>"+nl+"</ul></div>")
h.append("<div style=text-align:center;color:#333;font-size:11px;margin-top:8px>Coffee Market Skill | Yahoo Finance | "+now+"</div>")
h.append("</body></html>")

with open("C:/Users/nsyon/SCAN/coffee_results.html","w",encoding="utf-8") as f: f.write("".join(h))
print("="*40)
print(em+" "+fh)
print("Score: "+str(sc)+"/100")
print("LONG: "+str(lc)+" "+ll2+" | SHORT: "+str(sc2)+" "+sl2)
print(fm)
print("="*40)
print("Saved: C:\\Users\\nsyon\\SCAN\\coffee_results.html")
