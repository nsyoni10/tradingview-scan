import json, sys
sys.stdout.reconfigure(encoding='utf-8')

def calc_score(r):
    sc = 0
    if r['rsi'] < 30: sc += 2
    elif r['rsi'] < 45: sc += 1
    elif r['rsi'] > 70: sc -= 2
    elif r['rsi'] > 60: sc -= 1
    if r['macd'] > r['signal']: sc += 1
    else: sc -= 1
    if r['price'] > r['sma20'] > r['sma50']: sc += 2
    elif r['price'] < r['sma20'] < r['sma50']: sc -= 2
    return sc

# LONG
with open('C:/Users/nsyon/SCAN/_trading_analysis_long.json') as f:
    long_data = json.load(f)
for r in long_data:
    r['score'] = calc_score(r)
print('LONG:')
for r in long_data:
    print(f"  {r['symbol']:8} | score={r['score']:>3} | {r['rec']}")

# SHORT
with open('C:/Users/nsyon/SCAN/_trading_analysis_short.json') as f:
    short_data = json.load(f)
for r in short_data:
    r['score'] = calc_score(r)
print('SHORT:')
for r in short_data:
    print(f"  {r['symbol']:8} | score={r['score']:>3} | {r['rec']}")

# Save
with open('C:/Users/nsyon/SCAN/_trading_analysis_long.json', 'w') as f:
    json.dump(long_data, f, indent=2)
with open('C:/Users/nsyon/SCAN/_trading_analysis_short.json', 'w') as f:
    json.dump(short_data, f, indent=2)

# Select TOP 10
top_long = sorted([r for r in long_data if r['rec'] == 'STRONG BUY'], key=lambda x: -x['score'])
top_long += sorted([r for r in long_data if r['rec'] != 'STRONG BUY'], key=lambda x: -x['score'])
top_long = top_long[:10]

top_short = sorted([r for r in short_data if r['rec'] == 'STRONG SELL'], key=lambda x: x['score'])
top_short += sorted([r for r in short_data if r['rec'] != 'STRONG SELL'], key=lambda x: x['score'])
top_short = top_short[:10]

print(f"\nTOP LONG ({len(top_long)}):")
for r in top_long:
    print(f"  {r['symbol']:8} | score={r['score']:>3} | {r['rec']}")
print(f"TOP SHORT ({len(top_short)}):")
for r in top_short:
    print(f"  {r['symbol']:8} | score={r['score']:>3} | {r['rec']}")

print("\nScores saved.")
