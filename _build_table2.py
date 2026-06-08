import json

LONG_DATA = [
    {"symbol":"MJNA","price":0.0002,"52wH":0.0004,"52wL":0.0001,"resU":0.000233,"resN":0.000167,
     "supN":0.0000667,"supS":0.0000333,"supM":0.0000333,
     "entAgg":0.0001,"entCons":0.0000667,"shortOpp":0.0002,"shortTgt":0.0000333},
    {"symbol":"NSC","price":313.45,"52wH":326.00,"52wL":245.19,"resU":326.00,"resN":314.72,
     "supN":299.76,"supS":280.00,"supM":245.19,
     "entAgg":312.00,"entCons":299.50,"shortOpp":325.00,"shortTgt":299.76},
    {"symbol":"SEM","price":16.54,"52wH":16.99,"52wL":11.65,"resU":16.99,"resN":16.54,
     "supN":15.94,"supS":15.26,"supM":13.55,
     "entAgg":16.50,"entCons":15.94,"shortOpp":None,"shortTgt":15.26},
    {"symbol":"NVGS","price":21.79,"52wH":24.36,"52wL":13.66,"resU":24.36,"resN":22.74,
     "supN":20.50,"supS":17.93,"supM":13.66,
     "entAgg":21.75,"entCons":20.00,"shortOpp":23.93,"shortTgt":20.50},
    {"symbol":"ALXO","price":1.54,"52wH":2.66,"52wL":0.404,"resU":2.06,"resN":1.85,
     "supN":1.43,"supS":1.30,"supM":0.404,
     "entAgg":1.485,"entCons":1.30,"shortOpp":1.955,"shortTgt":1.30},
    {"symbol":"UDR","price":39.20,"52wH":42.22,"52wL":32.94,"resU":42.22,"resN":38.07,
     "supN":37.35,"supS":36.77,"supM":32.94,
     "entAgg":38.85,"entCons":37.26,"shortOpp":41.50,"shortTgt":37.26},
    {"symbol":"ABVX","price":101.53,"52wH":148.83,"52wL":5.69,"resU":133.27,"resN":102.08,
     "supN":87.50,"supS":72.50,"supM":60.34,
     "entAgg":100.00,"entCons":87.50,"shortOpp":126.50,"shortTgt":80.00},
    {"symbol":"PSO","price":15.56,"52wH":15.64,"52wL":12.02,"resU":15.64,"resN":15.09,
     "supN":14.875,"supS":14.66,"supM":12.02,
     "entAgg":15.38,"entCons":14.755,"shortOpp":15.60,"shortTgt":14.85},
    {"symbol":"LTH","price":32.39,"52wH":35.33,"52wL":24.14,"resU":35.33,"resN":34.265,
     "supN":32.75,"supS":32.42,"supM":27.59,
     "entAgg":32.57,"entCons":29.75,"shortOpp":34.88,"shortTgt":32.42},
    {"symbol":"NATL","price":44.15,"52wH":48.50,"52wL":23.56,"resU":48.50,"resN":46.25,
     "supN":43.805,"supS":40.00,"supM":33.67,
     "entAgg":43.825,"entCons":40.00,"shortOpp":48.00,"shortTgt":43.50},
]

SHORT_DATA = [
    {"symbol":"ZBIO","price":17.47,"52wH":44.60,"52wL":8.91,"resU":44.60,"resN":16.52,
     "supN":17.05,"supS":17.00,"supM":8.91,
     "entAgg":17.30,"entCons":15.76,"shortOpp":23.50,"shortTgt":13.00},
    {"symbol":"ABT","price":91.07,"52wH":139.06,"52wL":81.97,"resU":124.04,"resN":92.56,
     "supN":84.485,"supS":81.97,"supM":83.235,
     "entAgg":90.79,"entCons":84.75,"shortOpp":92.56,"shortTgt":83.235},
    {"symbol":"AMCR","price":38.13,"52wH":50.94,"52wL":36.25,"resU":50.94,"resN":40.465,
     "supN":39.76,"supS":39.30,"supM":36.25,
     "entAgg":39.44,"entCons":36.75,"shortOpp":40.465,"shortTgt":37.00},
    {"symbol":"CAE","price":25.50,"52wH":34.24,"52wL":22.76,"resU":29.62,"resN":27.035,
     "supN":25.42,"supS":24.42,"supM":22.76,
     "entAgg":23.15,"entCons":24.92,"shortOpp":28.06,"shortTgt":21.265},
    {"symbol":"OLLI","price":76.70,"52wH":141.74,"52wL":73.31,"resU":141.74,"resN":114.215,
     "supN":74.22,"supS":73.31,"supM":73.31,
     "entAgg":74.61,"entCons":106.54,"shortOpp":81.87,"shortTgt":73.765},
    {"symbol":"EA","price":203.00,"52wH":204.89,"52wL":141.19,"resU":204.89,"resN":202.255,
     "supN":200.69,"supS":199.98,"supM":155.725,
     "entAgg":200.755,"entCons":194.50,"shortOpp":203.71,"shortTgt":194.46},
    {"symbol":"TLK","price":15.54,"52wH":23.52,"52wL":15.63,"resU":23.52,"resN":17.385,
     "supN":16.96,"supS":16.31,"supM":15.63,
     "entAgg":16.595,"entCons":15.825,"shortOpp":17.385,"shortTgt":15.95},
    {"symbol":"BJ","price":89.21,"52wH":115.43,"52wL":83.65,"resU":115.43,"resN":95.165,
     "supN":84.16,"supS":83.65,"supM":83.65,
     "entAgg":84.47,"entCons":89.00,"shortOpp":95.165,"shortTgt":84.015},
    {"symbol":"ORI","price":38.16,"52wH":46.76,"52wL":35.60,"resU":46.355,"resN":44.35,
     "supN":40.62,"supS":37.14,"supM":35.135,
     "entAgg":37.20,"entCons":35.80,"shortOpp":40.62,"shortTgt":36.37},
    {"symbol":"KRMN","price":49.44,"52wH":118.38,"52wL":42.80,"resU":67.52,"resN":55.945,
     "supN":49.25,"supS":46.16,"supM":42.75,
     "entAgg":50.07,"entCons":43.63,"shortOpp":53.65,"shortTgt":47.05},
]

def fmt(v):
    if v is None: return "—"
    if isinstance(v, float):
        if abs(v) < 0.01: return f"{v:.7f}"
        return f"{v:.2f}"
    return str(v)

def make_row(t):
    cells = [
        f"<td><b>{t['symbol']}</b></td>",
        f"<td style='color:#cba6f7'>{fmt(t['price'])}</td>",
        f"<td style='color:#89dceb'>{fmt(t['52wH'])}</td>",
        f"<td style='color:#f38ba8'>{fmt(t['52wL'])}</td>",
        f"<td style='color:#89b4fa'>{fmt(t['resU'])}</td>",
        f"<td style='color:#89b4fa'>{fmt(t['resN'])}</td>",
        f"<td style='color:#f38ba8'>{fmt(t['supN'])}</td>",
        f"<td style='color:#f38ba8'>{fmt(t['supS'])}</td>",
        f"<td style='color:#f38ba8'>{fmt(t['supM'])}</td>",
        f"<td style='color:#a6e3a1'>{fmt(t['entAgg'])}</td>",
        f"<td style='color:#a6e3a1'>{fmt(t['entCons'])}</td>",
        f"<td style='color:#fab387'>{fmt(t['shortOpp'])}</td>",
        f"<td style='color:#fab387'>{fmt(t['shortTgt'])}</td>",
    ]
    return "<tr>" + "".join(cells) + "</tr>"

COLS = ["Symbol","Price","52W H","52W L","Res Upper","Res Near",
        "Sup Near","Sup Strong","Sup Main","Entry Agg","Entry Cons","Short Opp","Short Tgt"]

def make_thead():
    ths = "".join(f"<th>{c}</th>" for c in COLS)
    return f"<thead style='background:#1e1e2e;color:#cdd6f4'><tr>{ths}</tr></thead>"

def make_table(data, title):
    rows = "".join(make_row(t) for t in data)
    return f"""<h2>{title}</h2>
<table border='1' cellpadding='5' cellspacing='0' style='border-collapse:collapse;width:100%;font-family:monospace;font-size:13px;margin-bottom:30px'>
{make_thead()}<tbody>{rows}</tbody></table>"""

html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<title>DayScan Pivot — Table 2 (TOP 10)</title>
<style>
body{{background:#0f0f17;color:#cdd6f4;padding:20px;font-family:sans-serif}}
h1{{color:#cba6f7}} h2{{color:#89b4fa}}
td,th{{padding:6px 10px;border:1px solid #313244;white-space:nowrap}}
tbody tr:hover{{background:#1e1e2e}}
.legend{{font-size:12px;color:#a6adc8;margin-bottom:15px}}
</style></head><body>
<h1>DayScan Pivot — Table 2 (TOP 10) &nbsp;<small style='font-size:14px;color:#a6adc8'>2026-06-08</small></h1>
<p class='legend'>
  <span style='color:#89b4fa'>■</span> Blue = Resistance / 52W  &nbsp;
  <span style='color:#f38ba8'>■</span> Red = Support  &nbsp;
  <span style='color:#a6e3a1'>■</span> Green = Entry / TP  &nbsp;
  <span style='color:#fab387'>■</span> Orange = Short levels
</p>
{make_table(LONG_DATA, "TOP 10 LONG — CoffeeL")}
{make_table(SHORT_DATA, "TOP 10 SHORT — CoffeeS")}
</body></html>"""

with open("dayscan_pivot_table2.html","w",encoding="utf-8") as f:
    f.write(html)
print("Generated dayscan_pivot_table2.html")

# Save drawings data
def build_levels(t, side):
    def fmt2(v):
        if v is None: return None
        if isinstance(v, float):
            if abs(v) < 0.01: return f"{v:.7f}"
            return f"{v:.2f}"
        return str(v)
    levels = [
        {"price": t["supN"],    "color": "red",   "label": f"S Near: {fmt2(t['supN'])}"},
        {"price": t["supS"],    "color": "red",   "label": f"S Strong: {fmt2(t['supS'])}"},
        {"price": t["supM"],    "color": "red",   "label": f"S Main: {fmt2(t['supM'])}"},
        {"price": t["entAgg"],  "color": "green", "label": f"Entry Agg: {fmt2(t['entAgg'])}"},
        {"price": t["entCons"], "color": "green", "label": f"Entry Cons: {fmt2(t['entCons'])}"},
        {"price": t["shortTgt"],"color": "green", "label": f"TP: {fmt2(t['shortTgt'])}"},
        {"price": t["resU"],    "color": "blue",  "label": f"Res Upper: {fmt2(t['resU'])}"},
        {"price": t["resN"],    "color": "blue",  "label": f"Res Near: {fmt2(t['resN'])}"},
        {"price": t["52wH"],    "color": "blue",  "label": f"52W High: {fmt2(t['52wH'])}"},
        {"price": t["52wL"],    "color": "blue",  "label": f"52W Low: {fmt2(t['52wL'])}"},
    ]
    if t.get("shortOpp") is not None:
        levels.append({"price": t["shortOpp"], "color": "blue", "label": f"Short Opp: {fmt2(t['shortOpp'])}"})
    return [l for l in levels if l["price"] is not None]

drawings = {
    "long":  [{"symbol": t["symbol"], "levels": build_levels(t,"long")}  for t in LONG_DATA],
    "short": [{"symbol": t["symbol"], "levels": build_levels(t,"short")} for t in SHORT_DATA],
}
with open("_drawings_data.json","w") as f:
    json.dump(drawings, f, indent=2)
print("Saved _drawings_data.json")
