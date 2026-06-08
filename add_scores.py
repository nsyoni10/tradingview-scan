import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('C:/Users/nsyon/SCAN/_trading_analysis_results.json') as f:
    data = json.load(f)
for r in data:
    sc = 0
    rsi = r['rsi']
    if rsi < 30: sc += 2
    elif rsi < 45: sc += 1
    elif rsi > 70: sc -= 2
    elif rsi > 60: sc -= 1
    if r['macd'] > r['signal']: sc += 1
    else: sc -= 1
    if r['price'] > r['sma20'] > r['sma50']: sc += 2
    elif r['price'] < r['sma20'] < r['sma50']: sc -= 2
    r['score'] = sc
with open('C:/Users/nsyon/SCAN/_trading_analysis_results.json', 'w') as f:
    json.dump(data, f, indent=2)
for r in data:
    print(f"{r['symbol']:8} | score={r['score']:>3} | {r['rec']}")
