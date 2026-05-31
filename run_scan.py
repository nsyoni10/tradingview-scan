import requests, json, warnings, pickle
from datetime import datetime
warnings.filterwarnings('ignore')

def fetch(symbol):
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=3mo'
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, verify=False, timeout=15)
        d = r.json()['chart']['result'][0]['indicators']['quote'][0]
        closes  = [x for x in d['close']  if x]
        highs   = [x for x in d['high']   if x]
        lows    = [x for x in d['low']    if x]
        volumes = [x for x in d['volume'] if x]
        if len(closes) < 20: return None
        return closes, highs, lows, volumes
    except:
        return None

def ema(prices, n):
    k = 2/(n+1)
    e = prices[0]
    for p in prices[1:]: e = p*k + e*(1-k)
    return e

def rsi(closes, n=14):
    gains  = [max(closes[i]-closes[i-1], 0) for i in range(-n, 0)]
    losses = [max(closes[i-1]-closes[i], 0) for i in range(-n, 0)]
    ag = sum(gains)/n
    al = sum(losses)/n
    return 100 - 100/(1 + ag/al) if al > 0 else 100

def atr(highs, lows, closes, n=14):
    trs = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])) for i in range(-n, 0)]
    return sum(trs)/n

long_syms  = open('C:/Users/nsyon/SCAN/LONG.CSV').read().strip().split()
short_syms = open('C:/Users/nsyon/SCAN/SHORT.CSV').read().strip().split()

results = []
errors  = []

all_syms = [(s,'LONG') for s in long_syms] + [(s,'SHORT') for s in short_syms]
print(f"Scanning {len(all_syms)} symbols...")

for sym, direction in all_syms:
    data = fetch(sym)
    if not data:
        errors.append(sym)
        print(f"  ERROR: {sym}")
        continue

    closes, highs, lows, volumes = data
    last = closes[-1]
    e20  = ema(closes[-20:], 20)
    e50  = ema(closes[-50:] if len(closes) >= 50 else closes, 50)
    r    = rsi(closes)
    at   = atr(highs, lows, closes)
    vr   = volumes[-1] / (sum(volumes[-20:])/20) if volumes else 0
    d20  = (last - e20) / e20 * 100

    if direction == 'LONG'  and not (last > e20 and last > e50): continue
    if direction == 'SHORT' and not (last < e20 and last < e50): continue

    if direction == 'LONG':
        entry = last
        sl    = round(min(lows[-3:]) * 0.995, 2)
        tp    = round(entry + 2*(entry - sl), 2)
        vs = min(vr*30, 40)
        rs = max(0, min((r-50)/50*25, 25))
        ts = min(d20/10*20, 20)
        as_ = min(at/last*100/2*15, 15)
    else:
        entry = last
        sl    = round(max(highs[-3:]) * 1.005, 2)
        tp    = round(entry - 2*(sl - entry), 2)
        vs = min(vr*30, 40)
        rs = max(0, min((50-r)/50*25, 25))
        ts = min(abs(d20)/10*20, 20)
        as_ = min(at/last*100/2*15, 15)

    score  = round(vs + rs + ts + as_, 1)
    rr     = round(abs(tp-entry) / abs(entry-sl), 2) if abs(entry-sl) > 0 else 0
    reason = f"Volume x{vr:.1f} | RSI {r:.0f} | {d20:+.1f}% vs EMA20"
    results.append({'sym':sym,'dir':direction,'entry':round(entry,2),'sl':sl,'tp':tp,'rr':rr,'score':score,'reason':reason})
    print(f"  OK: {sym:6} {direction:5} Score:{score:5.1f} | {reason}")

results.sort(key=lambda x: x['score'], reverse=True)
longs  = [r for r in results if r['dir']=='LONG'][:5]
shorts = [r for r in results if r['dir']=='SHORT'][:5]

print()
print(f"=== RESULTS ===")
print(f"Passed: {len(results)} | LONG: {len([r for r in results if r['dir']=='LONG'])} | SHORT: {len([r for r in results if r['dir']=='SHORT'])}")
print(f"Errors: {len(errors)}")
print()
print("TOP 5 LONG:")
for i,r in enumerate(longs,1):
    print(f"  {i}. {r['sym']:6} Entry:{r['entry']:8.2f}  SL:{r['sl']:8.2f}  TP:{r['tp']:8.2f}  R:R 1:{r['rr']}  Score:{r['score']}")
print()
print("TOP 5 SHORT:")
for i,r in enumerate(shorts,1):
    print(f"  {i}. {r['sym']:6} Entry:{r['entry']:8.2f}  SL:{r['sl']:8.2f}  TP:{r['tp']:8.2f}  R:R 1:{r['rr']}  Score:{r['score']}")

with open('C:/Users/nsyon/SCAN/_scan_data.pkl','wb') as f:
    pickle.dump({'longs':longs,'shorts':shorts,'all':results,'errors':errors,'time':datetime.now().strftime('%Y-%m-%d %H:%M')}, f)
print()
print("Data saved to _scan_data.pkl")
