import json, os

LONG_RAW = [
    {"symbol":"SAN","price":12.15,"chg":-2.57,"rsi":56.8,"vol":31.3,"rec":"SELL","sentiment":"bearish","sma20":12.19,"sma50":12.03},
    {"symbol":"NSC","price":313.45,"chg":2.04,"rsi":48.0,"vol":27.3,"rec":"BUY","sentiment":"bullish","sma20":312.65,"sma50":306.14},
    {"symbol":"MOD","price":276.51,"chg":-8.20,"rsi":51.4,"vol":88.5,"rec":"BUY","sentiment":"bullish","sma20":276.84,"sma50":255.38},
    {"symbol":"UDR","price":39.20,"chg":0.77,"rsi":69.3,"vol":20.4,"rec":"BUY","sentiment":"bullish","sma20":37.57,"sma50":36.12},
    {"symbol":"AM","price":21.52,"chg":-0.28,"rsi":43.4,"vol":20.6,"rec":"SELL","sentiment":"bearish","sma20":21.56,"sma50":21.77},
    {"symbol":"ABVX","price":101.53,"chg":-3.24,"rsi":44.6,"vol":196.9,"rec":"SELL","sentiment":"bearish","sma20":116.70,"sma50":116.70},
    {"symbol":"BRX","price":30.98,"chg":2.08,"rsi":70.4,"vol":19.2,"rec":"BUY","sentiment":"bullish","sma20":30.24,"sma50":29.97},
    {"symbol":"PSO","price":15.56,"chg":1.70,"rsi":68.5,"vol":25.7,"rec":"HOLD","sentiment":"neutral","sma20":15.03,"sma50":14.46},
    {"symbol":"FR","price":61.58,"chg":-0.16,"rsi":53.9,"vol":20.0,"rec":"SELL","sentiment":"bearish","sma20":61.88,"sma50":61.33},
    {"symbol":"LTH","price":32.39,"chg":-0.49,"rsi":41.6,"vol":34.0,"rec":"HOLD","sentiment":"neutral","sma20":32.81,"sma50":29.75},
    {"symbol":"MSM","price":115.51,"chg":-1.26,"rsi":77.9,"vol":23.6,"rec":"BUY","sentiment":"bullish","sma20":108.81,"sma50":101.59},
    {"symbol":"NATL","price":44.15,"chg":-0.14,"rsi":44.8,"vol":15.4,"rec":"HOLD","sentiment":"neutral","sma20":44.63,"sma50":44.46},
    {"symbol":"AKR","price":22.40,"chg":2.10,"rsi":72.6,"vol":19.4,"rec":"BUY","sentiment":"bullish","sma20":21.73,"sma50":21.11},
    {"symbol":"CALY","price":14.80,"chg":-1.33,"rsi":43.2,"vol":79.0,"rec":"HOLD","sentiment":"neutral","sma20":15.47,"sma50":14.90},
    {"symbol":"DRH","price":11.61,"chg":0.61,"rsi":82.6,"vol":24.5,"rec":"BUY","sentiment":"bullish","sma20":10.88,"sma50":10.39},
    {"symbol":"PUMP","price":14.74,"chg":-10.50,"rsi":31.7,"vol":66.5,"rec":"HOLD","sentiment":"neutral","sma20":16.46,"sma50":15.69},
    {"symbol":"SEM","price":16.54,"chg":0.30,"rsi":58.3,"vol":2.2,"rec":"BUY","sentiment":"bullish","sma20":16.49,"sma50":16.43},
    {"symbol":"NVGS","price":21.79,"chg":0.23,"rsi":26.5,"vol":24.2,"rec":"BUY","sentiment":"bullish","sma20":22.90,"sma50":21.52},
    {"symbol":"NVRI","price":19.30,"chg":-2.03,"rsi":49.5,"vol":73.4,"rec":"SELL","sentiment":"bearish","sma20":19.22,"sma50":19.32},
    {"symbol":"OLPX","price":2.04,"chg":0.00,"rsi":54.5,"vol":7.2,"rec":"BUY","sentiment":"bullish","sma20":2.04,"sma50":2.03},
    {"symbol":"FLTCF","price":4.91,"chg":9.43,"rsi":45.6,"vol":146.4,"rec":"SELL","sentiment":"bearish","sma20":5.30,"sma50":4.19},
    {"symbol":"RIOFF","price":1.92,"chg":-11.28,"rsi":37.3,"vol":77.8,"rec":"HOLD","sentiment":"neutral","sma20":2.23,"sma50":2.08},
    {"symbol":"VGZ","price":2.17,"chg":-8.05,"rsi":50.0,"vol":56.0,"rec":"SELL","sentiment":"bearish","sma20":2.28,"sma50":2.15},
    {"symbol":"ALXO","price":1.54,"chg":-1.28,"rsi":11.1,"vol":58.6,"rec":"BUY","sentiment":"bullish","sma20":1.91,"sma50":1.84},
    {"symbol":"ARRNF","price":0.28,"chg":-5.12,"rsi":33.6,"vol":86.0,"rec":"HOLD","sentiment":"neutral","sma20":0.30,"sma50":0.27},
    {"symbol":"MJNA","price":0.0002,"chg":-33.33,"rsi":42.9,"vol":1005.2,"rec":"STRONG BUY","sentiment":"bullish","sma20":0.0002,"sma50":0.0002},
    {"symbol":"QEDN","price":0.0002,"chg":0.00,"rsi":50.0,"vol":570.0,"rec":"BUY","sentiment":"bullish","sma20":0.0002,"sma50":0.0002},
]

SHORT_RAW = [
    {"symbol":"MCD","price":279.84,"chg":2.61,"rsi":54.7,"vol":19.3,"rec":"BUY","sentiment":"bullish","sma20":277.90,"sma50":291.53},
    {"symbol":"ABT","price":91.07,"chg":0.32,"rsi":70.8,"vol":30.0,"rec":"SELL","sentiment":"bearish","sma20":86.63,"sma50":92.55},
    {"symbol":"BAM","price":46.18,"chg":-1.13,"rsi":42.6,"vol":36.2,"rec":"HOLD","sentiment":"neutral","sma20":48.13,"sma50":47.19},
    {"symbol":"B","price":39.46,"chg":-7.78,"rsi":45.8,"vol":60.3,"rec":"SELL","sentiment":"bearish","sma20":42.24,"sma50":41.46},
    {"symbol":"SE","price":86.56,"chg":-6.00,"rsi":47.5,"vol":69.0,"rec":"SELL","sentiment":"bearish","sma20":89.87,"sma50":87.02},
    {"symbol":"EA","price":203.00,"chg":-0.20,"rsi":69.4,"vol":3.5,"rec":"HOLD","sentiment":"neutral","sma20":201.37,"sma50":202.20},
    {"symbol":"FOXA","price":66.89,"chg":2.06,"rsi":56.8,"vol":39.8,"rec":"STRONG BUY","sentiment":"bullish","sma20":65.28,"sma50":63.37},
    {"symbol":"FOX","price":59.88,"chg":1.96,"rsi":56.9,"vol":41.9,"rec":"STRONG BUY","sentiment":"bullish","sma20":58.52,"sma50":56.90},
    {"symbol":"INCY","price":102.38,"chg":1.13,"rsi":69.2,"vol":32.5,"rec":"BUY","sentiment":"bullish","sma20":97.52,"sma50":96.51},
    {"symbol":"AMCR","price":38.13,"chg":1.30,"rsi":58.3,"vol":32.5,"rec":"SELL","sentiment":"bearish","sma20":38.47,"sma50":39.24},
    {"symbol":"TLK","price":15.54,"chg":-3.00,"rsi":37.8,"vol":33.1,"rec":"SELL","sentiment":"bearish","sma20":16.66,"sma50":17.39},
    {"symbol":"FMS","price":22.03,"chg":0.46,"rsi":54.6,"vol":34.3,"rec":"BUY","sentiment":"bullish","sma20":21.70,"sma50":22.24},
    {"symbol":"BJ","price":89.21,"chg":0.92,"rsi":34.3,"vol":39.2,"rec":"SELL","sentiment":"bearish","sma20":90.92,"sma50":93.13},
    {"symbol":"ORI","price":38.16,"chg":2.61,"rsi":41.0,"vol":20.1,"rec":"SELL","sentiment":"bearish","sma20":38.62,"sma50":39.75},
    {"symbol":"KRMN","price":49.44,"chg":-9.10,"rsi":33.7,"vol":87.6,"rec":"SELL","sentiment":"bearish","sma20":60.76,"sma50":71.22},
    {"symbol":"CAE","price":25.50,"chg":0.24,"rsi":50.1,"vol":59.5,"rec":"SELL","sentiment":"bearish","sma20":25.63,"sma50":26.10},
    {"symbol":"RYTM","price":86.40,"chg":-1.38,"rsi":42.8,"vol":50.9,"rec":"HOLD","sentiment":"neutral","sma20":89.35,"sma50":87.31},
    {"symbol":"PTCT","price":70.97,"chg":0.47,"rsi":48.8,"vol":67.5,"rec":"SELL","sentiment":"bearish","sma20":71.44,"sma50":69.78},
    {"symbol":"ESNT","price":57.44,"chg":0.47,"rsi":37.5,"vol":26.2,"rec":"SELL","sentiment":"bearish","sma20":59.65,"sma50":60.51},
    {"symbol":"OLLI","price":76.70,"chg":2.99,"rsi":46.8,"vol":54.5,"rec":"SELL","sentiment":"bearish","sma20":79.36,"sma50":85.94},
    {"symbol":"KRC","price":37.03,"chg":0.35,"rsi":68.9,"vol":27.2,"rec":"BUY","sentiment":"bullish","sma20":34.68,"sma50":32.34},
    {"symbol":"DNLI","price":19.52,"chg":-3.08,"rsi":55.7,"vol":46.6,"rec":"SELL","sentiment":"bearish","sma20":19.52,"sma50":19.58},
    {"symbol":"TARS","price":59.28,"chg":-1.76,"rsi":40.4,"vol":49.2,"rec":"SELL","sentiment":"bearish","sma20":61.13,"sma50":64.56},
    {"symbol":"ZBIO","price":17.47,"chg":-4.95,"rsi":45.7,"vol":74.9,"rec":"STRONG SELL","sentiment":"bearish","sma20":18.59,"sma50":19.59},
]

def calc_score(t):
    score = 0
    rsi = t["rsi"]
    p, s20, s50 = t["price"], t["sma20"], t["sma50"]
    # RSI tiers (exclusive)
    if rsi < 30:
        score += 2
    elif rsi < 45:
        score += 1
    elif rsi > 70:
        score -= 2
    elif rsi > 60:
        score -= 1
    # SMA alignment
    if p > s20 > s50:
        score += 2
    elif p < s20 < s50:
        score -= 2
    return score

# Score all
for t in LONG_RAW:
    t["score"] = calc_score(t)
for t in SHORT_RAW:
    t["score"] = calc_score(t)

# Save trading analysis JSONs
with open("_trading_analysis_long.json","w") as f:
    json.dump(LONG_RAW, f, indent=2)
with open("_trading_analysis_short.json","w") as f:
    json.dump(SHORT_RAW, f, indent=2)
print("Saved _trading_analysis_long.json / _trading_analysis_short.json")

# TOP 10 LONG: STRONG BUY first (by score desc), then rest by score desc
strong_buy_long = sorted([t for t in LONG_RAW if t["rec"] == "STRONG BUY"], key=lambda x: -x["score"])
rest_long = sorted([t for t in LONG_RAW if t["rec"] != "STRONG BUY"], key=lambda x: -x["score"])
top10_long = (strong_buy_long + rest_long)[:10]

# TOP 10 SHORT: STRONG SELL first (by score asc), then rest by score asc
strong_sell_short = sorted([t for t in SHORT_RAW if t["rec"] == "STRONG SELL"], key=lambda x: x["score"])
rest_short = sorted([t for t in SHORT_RAW if t["rec"] != "STRONG SELL"], key=lambda x: x["score"])
top10_short = (strong_sell_short + rest_short)[:10]

with open("_top10_long.json","w") as f:
    json.dump(top10_long, f, indent=2)
with open("_top10_short.json","w") as f:
    json.dump(top10_short, f, indent=2)

print("\nTOP 10 LONG:")
for t in top10_long:
    print(f"  {t['symbol']:8s} score={t['score']:+d}  rec={t['rec']}")
print("\nTOP 10 SHORT:")
for t in top10_short:
    print(f"  {t['symbol']:8s} score={t['score']:+d}  rec={t['rec']}")

# Generate Table 1 HTML
def rec_color(rec):
    return {"STRONG BUY":"#00c853","BUY":"#69f0ae","HOLD":"#ffd740","SELL":"#ff6d00","STRONG SELL":"#d50000"}.get(rec,"#888")

def sent_color(s):
    return {"bullish":"#00c853","neutral":"#ffd740","bearish":"#ff6d00"}.get(s,"#888")

def score_color(sc):
    if sc >= 3: return "#00c853"
    if sc >= 1: return "#69f0ae"
    if sc == 0: return "#888"
    if sc >= -2: return "#ff6d00"
    return "#d50000"

def make_table(data, title, highlight_syms):
    rows = ""
    for t in data:
        hl = " style='background:#1a2a1a'" if t["symbol"] in highlight_syms else ""
        rows += f"""<tr{hl}>
  <td><b>{t['symbol']}</b></td>
  <td>{t['price']:.4f}</td>
  <td style='color:{"#69f0ae" if t["chg"]>=0 else "#ff6d00"}'>{t['chg']:+.2f}%</td>
  <td>{t['rsi']:.1f}</td>
  <td>{t['vol']:.1f}%</td>
  <td style='background:{rec_color(t["rec"])};color:#000;font-weight:bold'>{t['rec']}</td>
  <td style='color:{sent_color(t["sentiment"])}'>{t['sentiment']}</td>
  <td>{t['sma20']:.4f}</td>
  <td>{t['sma50']:.4f}</td>
  <td style='color:{score_color(t["score"])};font-weight:bold'>{t['score']:+d}</td>
</tr>"""
    return f"""<h2>{title}</h2>
<table border='1' cellpadding='5' cellspacing='0' style='border-collapse:collapse;width:100%;font-family:monospace;font-size:13px'>
<thead style='background:#1e1e2e;color:#cdd6f4'>
<tr><th>Symbol</th><th>Price</th><th>Chg%</th><th>RSI</th><th>Vol%</th><th>Rec</th><th>Sentiment</th><th>SMA20</th><th>SMA50</th><th>Score</th></tr>
</thead><tbody>
{rows}
</tbody></table>"""

long_highlights = {t["symbol"] for t in top10_long}
short_highlights = {t["symbol"] for t in top10_short}

html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<title>DayScan Pivot — Table 1</title>
<style>body{{background:#0f0f17;color:#cdd6f4;padding:20px;font-family:sans-serif}}
h1{{color:#cba6f7}} h2{{color:#89b4fa}} table{{margin-bottom:30px}}
td,th{{padding:6px 10px;border:1px solid #313244}} tbody tr:hover{{background:#1e1e2e}}
.legend{{font-size:12px;margin-bottom:10px;color:#a6adc8}}</style></head><body>
<h1>DayScan Pivot — Table 1 &nbsp;<small style='font-size:14px;color:#a6adc8'>2026-06-08</small></h1>
<p class='legend'>Highlighted rows = selected TOP 10 | Score: RSI tiers ±1/±2, SMA alignment ±2</p>
{make_table(LONG_RAW, "LONG (CoffeeL) — 27 tickers", long_highlights)}
{make_table(SHORT_RAW, "SHORT (CoffeeS) — 24 tickers", short_highlights)}
</body></html>"""

with open("dayscan_pivot_table1.html","w",encoding="utf-8") as f:
    f.write(html)
print("\nGenerated dayscan_pivot_table1.html")
