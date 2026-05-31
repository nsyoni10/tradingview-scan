import requests, json, time, sys, warnings
from datetime import datetime
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

# ── Load symbols ──────────────────────────────────────────────────────────────
with open('C:/Users/nsyon/SCAN/_long_syms.json')  as f: LONG_SYMS  = json.load(f)
with open('C:/Users/nsyon/SCAN/_short_syms.json') as f: SHORT_SYMS = json.load(f)

print(f"LONG:  {len(LONG_SYMS)} symbols")
print(f"SHORT: {len(SHORT_SYMS)} symbols")
print(f"Total: {len(LONG_SYMS)+len(SHORT_SYMS)} symbols to scan\n")

# ── Step 2: Fetch Yahoo Finance data ─────────────────────────────────────────
def fetch_yahoo(symbol):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=3mo'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        data = r.json()
        result = data['chart']['result'][0]
        q = result['indicators']['quote'][0]
        closes  = [x for x in q.get('close',[])  if x is not None]
        highs   = [x for x in q.get('high',[])   if x is not None]
        lows    = [x for x in q.get('low',[])    if x is not None]
        volumes = [x for x in q.get('volume',[]) if x is not None]
        if len(closes) < 20:
            return None, f"Insufficient data ({len(closes)} bars)"
        return {'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes}, None
    except Exception as e:
        return None, str(e)[:60]

# ── Step 3: Calculate indicators ─────────────────────────────────────────────
def calc_ema(closes, period):
    if len(closes) < period:
        period = len(closes)
    k = 2 / (period + 1)
    ema = closes[0]
    for c in closes[1:]:
        ema = c * k + ema * (1 - k)
    return ema

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains  = [max(d, 0) for d in deltas[-period:]]
    losses = [max(-d, 0) for d in deltas[-period:]]
    avg_g = sum(gains) / period
    avg_l = sum(losses) / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100 - 100 / (1 + rs)

def calc_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        period = len(closes) - 1
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return sum(trs[-period:]) / min(period, len(trs))

def analyze(symbol, direction, data):
    closes  = data['closes']
    highs   = data['highs']
    lows    = data['lows']
    volumes = data['volumes']

    last_close = closes[-1]
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    rsi   = calc_rsi(closes, 14)
    atr   = calc_atr(highs, lows, closes, 14)

    avg_vol  = sum(volumes[-20:]) / min(20, len(volumes)) if volumes else 1
    last_vol = volumes[-1] if volumes else 0
    vol_ratio = last_vol / avg_vol if avg_vol > 0 else 0

    dist_ema20 = (last_close - ema20) / ema20 * 100
    dist_ema50 = (last_close - ema50) / ema50 * 100

    # Step 4: Direction filter
    if direction == 'LONG':
        if not (last_close > ema20 and last_close > ema50):
            return None, f"Below EMAs (close={last_close:.2f} EMA20={ema20:.2f} EMA50={ema50:.2f})"
    else:  # SHORT
        if not (last_close < ema20 and last_close < ema50):
            return None, f"Above EMAs (close={last_close:.2f} EMA20={ema20:.2f} EMA50={ema50:.2f})"

    # Step 5: Setup levels
    if direction == 'LONG':
        entry = last_close
        sl    = round(min(lows[-3:]) * 0.995, 2)
        tp    = round(entry + 2 * (entry - sl), 2)
    else:
        entry = last_close
        sl    = round(max(highs[-3:]) * 1.005, 2)
        tp    = round(entry - 2 * (sl - entry), 2)
    entry = round(entry, 2)
    sl    = round(sl, 2)
    risk  = abs(entry - sl)
    if risk < 0.001:
        return None, f"SL too close to entry (risk={risk:.4f})"
    rr = round(abs(tp - entry) / risk, 2)

    # Step 5b: Score
    if direction == 'LONG':
        volume_score = min(vol_ratio * 30, 40)
        rsi_score    = max(0, min((rsi - 50) / 50 * 25, 25))
        trend_score  = min(dist_ema20 / 10 * 20, 20)
        atr_score    = min(atr / last_close * 100 / 2 * 15, 15)
    else:
        volume_score = min(vol_ratio * 30, 40)
        rsi_score    = max(0, min((50 - rsi) / 50 * 25, 25))
        trend_score  = min(abs(dist_ema20) / 10 * 20, 20)
        atr_score    = min(atr / last_close * 100 / 2 * 15, 15)
    score = round(volume_score + rsi_score + trend_score + atr_score, 1)

    return {
        'symbol': symbol, 'direction': direction,
        'entry': entry, 'sl': sl, 'tp': tp, 'rr': rr,
        'score': score, 'rsi': round(rsi, 1),
        'vol_ratio': round(vol_ratio, 2),
        'dist_ema20': round(dist_ema20, 2),
        'atr': round(atr, 3),
        'ema20': round(ema20, 2), 'ema50': round(ema50, 2)
    }, None

# ── Run scan ──────────────────────────────────────────────────────────────────
results  = []
errors   = []
skipped  = []

all_tasks = [(s, 'LONG') for s in LONG_SYMS] + [(s, 'SHORT') for s in SHORT_SYMS]
total = len(all_tasks)

for i, (sym, direction) in enumerate(all_tasks):
    print(f"[{i+1}/{total}] {sym} ({direction})...", end=' ')
    data, err = fetch_yahoo(sym)
    if err:
        errors.append({'symbol': sym, 'error': err})
        print(f"ERROR: {err}")
        continue
    result, skip_reason = analyze(sym, direction, data)
    if skip_reason:
        skipped.append({'symbol': sym, 'reason': skip_reason})
        print(f"skip: {skip_reason}")
    else:
        results.append(result)
        print(f"✓ score={result['score']} entry={result['entry']} SL={result['sl']} TP={result['tp']}")
    time.sleep(0.15)

# Sort by score
long_results  = sorted([r for r in results if r['direction']=='LONG'],  key=lambda x: -x['score'])
short_results = sorted([r for r in results if r['direction']=='SHORT'], key=lambda x: -x['score'])

top5_long  = long_results[:5]
top5_short = short_results[:5]

print(f"\n{'='*60}")
print(f"LONG setups: {len(long_results)} | SHORT setups: {len(short_results)}")
print(f"TOP 5 LONG:  {[r['symbol'] for r in top5_long]}")
print(f"TOP 5 SHORT: {[r['symbol'] for r in top5_short]}")

# Save results for HTML generation
with open('C:/Users/nsyon/SCAN/_scan_results.json','w') as f:
    json.dump({
        'long': long_results, 'short': short_results,
        'top5_long': top5_long, 'top5_short': top5_short,
        'errors': errors, 'skipped': skipped,
        'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }, f, indent=2)
print("Saved to _scan_results.json")
