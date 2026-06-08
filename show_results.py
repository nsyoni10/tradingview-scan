import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('C:/Users/nsyon/SCAN/_trading_analysis_results.json') as f:
    data = json.load(f)
for r in data:
    sym = r['symbol']
    print(f"{sym:8} | ${r['price']:<8} | chg={r['change_pct']:>6}% | RSI={r['rsi']:>5} | SMA20=${r['sma20']:<8} | SMA50=${r['sma50']:<8} | MACD={r['macd']:>7} | sig={r['signal']:>7} | BB+=${r['bb_upper']:<8} | BB-=${r['bb_lower']:<8} | vol={r['vol']:>6} | {r['rec']:>12} | {r['sentiment']}")
print(f"\nTotal: {len(data)} records, 13 fields each")
