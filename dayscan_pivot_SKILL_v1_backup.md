---
name: dayscan_pivot
description: "Daily stock watchlist scan using Pivot Points — reads CoffeeL/CoffeeS screeners, fetches data from Yahoo Finance, calculates Pivot Points (P, R1, S1) as Entry/TP/SL, estimates trade duration in days using ATR, and generates an HTML dashboard."
---

Step 0 — Launch TradingView with CDP

Run via PowerShell:
taskkill /f /im TradingView.exe
Start-Sleep -Seconds 2
Start-Process 'C:\Program Files\WindowsApps\TradingView.Desktop_3.1.0.7818_x64__n534cwy3pjxzj\TradingView.exe' -ArgumentList '--remote-debugging-port=9222','--remote-allow-origins=*'
Start-Sleep -Seconds 12

Verify CDP: Invoke-RestMethod http://localhost:9222/json | Where-Object { $_.url -like "*tradingview*" }

TradingView stays open after dayscan_pivot finishes — RunDayscan will use it.

Step 1 — Read symbols from TradingView Screeners via CDP

Same as dayscan — run C:\Users\nsyon\SCAN\step1_screeners.py
Parse result: LONG_SYMBOLS from _long_syms.json, SHORT_SYMBOLS from _short_syms.json

Step 2 — Fetch real market data from Yahoo Finance

url = https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}?interval=1d&range=3mo
headers = {'User-Agent': 'Mozilla/5.0'}
verify = False, timeout = 15

Parse the JSON response:
closes  = data['chart']['result'][0]['indicators']['quote'][0]['close']  (filter None)
highs   = data['chart']['result'][0]['indicators']['quote'][0]['high']   (filter None)
lows    = data['chart']['result'][0]['indicators']['quote'][0]['low']    (filter None)
volumes = data['chart']['result'][0]['indicators']['quote'][0]['volume'] (filter None)
If fetch fails or data is missing — mark as DATA ERROR and skip.

Step 3 — Calculate indicators

EMA20: multiplier = 2/21, apply iteratively on last 20 closes
EMA50: multiplier = 2/51, apply iteratively on last 50 closes
last_close = closes[-1]
avg_volume_20 = average of volumes[-20:]
last_volume = volumes[-1]
volume_ratio = last_volume / avg_volume_20

RSI(14):
  gains  = [max(closes[i]-closes[i-1], 0) for i in last 14]
  losses = [max(closes[i-1]-closes[i], 0) for i in last 14]
  RS = avg(gains) / avg(losses)
  RSI = 100 - 100/(1+RS)

ATR(14):
  true_ranges = [max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])) for last 14]
  ATR = average(true_ranges)

Step 4 — Calculate Pivot Points (Standard Floor Pivot)

Uses the PREVIOUS day's High, Low, Close (last completed candle):
  prev_high  = highs[-2]
  prev_low   = lows[-2]
  prev_close = closes[-2]

  P  = (prev_high + prev_low + prev_close) / 3   ← Pivot (Entry)
  R1 = 2 * P - prev_low                           ← Resistance 1 (Take Profit LONG)
  S1 = 2 * P - prev_high                          ← Support 1 (Stop Loss LONG)
  R2 = P + (prev_high - prev_low)                 ← Resistance 2 (extended target)
  S2 = P - (prev_high - prev_low)                 ← Support 2 (extended stop)

Round all to 2 decimal places.

Step 5 — Direction filter

LONG:  include only if last_close > P (price above pivot = bullish bias)
SHORT: include only if last_close < P (price below pivot = bearish bias)
Otherwise → skip

Step 6 — Setup levels

LONG:
  Entry       = P
  Stop Loss   = S1
  Take Profit = R1
  Risk        = abs(Entry - SL)
  Reward      = abs(TP - Entry)
  R:R         = Reward / Risk
  Days Est.   = Reward / ATR   ← estimated days to reach TP
  Shares      = int(100 / (P - S1))   ← כמה מניות לקנות ב-$100 סיכון

SHORT:
  Entry       = P
  Stop Loss   = R1
  Take Profit = S1
  Risk        = abs(Entry - SL)
  Reward      = abs(TP - Entry)
  R:R         = Reward / Risk
  Days Est.   = Reward / ATR
  Shares      = int(100 / (R1 - P))   ← כמה מניות לקנות ב-$100 סיכון

Filter: keep only setups where Days Est. <= 3 AND R:R >= 2.0
If risk < 0.001 → skip (SL too close to entry)

Step 7 — Score each setup (0-100)

LONG score:
  volume_score = min(vol_ratio * 30, 40)
  rsi_score    = max(0, min((RSI-50)/50*25, 25))
  trend_score  = min(dist_ema20/10*20, 20)
  atr_score    = min(ATR/last_close*100/2*15, 15)
  total        = volume_score + rsi_score + trend_score + atr_score

SHORT score:
  volume_score = min(vol_ratio * 30, 40)
  rsi_score    = max(0, min((50-RSI)/50*25, 25))
  trend_score  = min(abs(dist_ema20)/10*20, 20)
  atr_score    = min(ATR/last_close*100/2*15, 15)
  total        = volume_score + rsi_score + trend_score + atr_score

Select TOP 5 LONG and TOP 5 SHORT by score.

Step 8 — Save results as HTML

Save to C:\Users\nsyon\SCAN\dayscan_pivot_results.html

Run: C:\Users\nsyon\SCAN\dayscan_pivot_main.py

SECTION A — TOP PICKS:
  Two side-by-side cards: "🏆 TOP 5 LONG" and "🏆 TOP 5 SHORT"
  Each card shows ranked list (1-5) with:
    - Rank + Symbol (bold)
    - Score out of 100 (colored bar)
    - One-line reason: e.g. "Volume ×2.3 | RSI 67 | Days Est: 1.8 | R:R 2.1"
  Style: dark card, green border for LONG, red border for SHORT

SECTION B — Summary cards:
  Total / LONG count / SHORT count / Avg Days Est.

SECTION C — Full tables:
  Two separate tables: LONG Setups and SHORT Setups
  Columns: Symbol, Direction, P, R1, S1, R2, S2, R:R, Days Est., קנייה ב-$100, Score
  Each row must include: data-symbol, data-entry, data-sl, data-tp, data-p, data-r1, data-s1, data-r2, data-s2
  TOP 5 rows get a ⭐ star badge next to symbol name

SECTION D — Errors:
  List failed symbols at bottom

Show scan date/time and "Data: Yahoo Finance | Pivot Points: Standard Floor | Source: TradingView Screeners (CoffeeL/CoffeeS)" at the top.
Display the file path when done.
