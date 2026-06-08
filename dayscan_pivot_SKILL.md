---
name: dayscan_pivot
description: "Daily stock scan using trading-analysis and us-stock-analysis skills. Reads CoffeeL/CoffeeS screeners, runs trading-analysis on all tickers, scores and selects TOP 10 LONG/SHORT, runs us-stock-analysis on TOP 10, and draws on charts."
---

## Step 0 — Launch TradingView with CDP

Run via PowerShell:
taskkill /f /im TradingView.exe
Start-Sleep -Seconds 2
Start-Process 'C:\Program Files\WindowsApps\TradingView.Desktop_3.2.0.7916_x64__n534cwy3pjxzj\TradingView.exe' -ArgumentList '--remote-debugging-port=9222','--remote-allow-origins=*'
Start-Sleep -Seconds 12

Verify CDP: Invoke-RestMethod http://localhost:9222/json | Where-Object { $_.url -like "*tradingview*" }

## Step 1 — Read tickers from TradingView Screeners

Run: C:\Users\nsyon\SCAN\step1_screeners.py

Result:
  LONG_SYMBOLS  ← CoffeeL screener → _long_syms.json
  SHORT_SYMBOLS ← CoffeeS screener → _short_syms.json

Remove "R" from both lists (not a ticker — screener marker).

## Step 2 — Run trading-analysis on all tickers → Table 1

Run skill: trading-analysis(LONG_SYMBOLS)
Run skill: trading-analysis(SHORT_SYMBOLS)

Pass tickers as comma-separated list from _long_syms.json / _short_syms.json

Each ticker returns 9 fields:
  symbol, price, change_pct, rsi, vol, rec, sentiment, sma20, sma50

Save results to: _trading_analysis_long.json / _trading_analysis_short.json

Generate: C:\Users\nsyon\SCAN\dayscan_pivot_table1.html
  — One row per ticker, all 9 fields + Score column

## Step 3 — Score and select TOP 10

Calculate score for each ticker:
  RSI < 30  → +2
  RSI < 45  → +1
  RSI > 70  → -2
  RSI > 60  → -1
  MACD > Signal → +1
  MACD < Signal → -1
  Price > SMA20 > SMA50 → +2
  Price < SMA20 < SMA50 → -2

TOP 10 LONG selection:
  1. First: Rec = STRONG BUY, sorted by highest score
  2. Then: remaining, sorted by highest score
  Fill up to 10

TOP 10 SHORT selection:
  1. First: Rec = STRONG SELL, sorted by lowest score
  2. Then: remaining, sorted by lowest score
  Fill up to 10

Save: _top10_long.json / _top10_short.json

## Step 4 — Run us-stock-analysis on TOP 10 → Table 2 + Chart drawings

Run skill: us-stock-analysis(TOP 10 LONG tickers)
Run skill: us-stock-analysis(TOP 10 SHORT tickers)

### 4a — Search and collect data

For each ticker, search web for: 52W high/low, support, resistance, key levels

### 4b — Extract fields to Table 2

Extract from results:
  52W high, 52W low
  Resistance upper, Resistance near
  Support near, Support strong, Support main
  Entry long aggressive, Entry long conservative
  Short opportunity, Short target

Generate: C:\Users\nsyon\SCAN\dayscan_pivot_table2.html
  — One row per ticker, all fields above

### 4c — Save notes as HTML

Save raw results to: C:\Users\nsyon\SCAN\dayscan_pivot_notes.html
  Title: "תוצאת הרצה — [DATE]"
  TAG: "dayscan_pivot_run" in meta tag
  One row per ticker: Symbol + raw text from search

## Step 5 — Add to DAYSCAN watchlist + Draw on charts

Add TOP 10 LONG + TOP 10 SHORT to DAYSCAN watchlist:
  Run: C:\Users\nsyon\SCAN\tv_watchlist_pivot.py
  Reads from: _top10_long.json / _top10_short.json

Draw colored lines on charts:
  Run: C:\Users\nsyon\SCAN\tv_mark_charts_pivot.py
  Reads from: _top10_long.json / _top10_short.json
  Red = Support, Green = Target, Blue = Resistance/52W

## Output files

- dayscan_pivot_table1.html — All tickers with trading-analysis data + score
- dayscan_pivot_table2.html — TOP 10 with us-stock-analysis data
- dayscan_pivot_notes.html — Raw skill output per ticker with TAG
- _trading_analysis_long.json
- _trading_analysis_short.json
- _top10_long.json
- _top10_short.json
- C:/Users/nsyon/reports/*.png — Charts per ticker
