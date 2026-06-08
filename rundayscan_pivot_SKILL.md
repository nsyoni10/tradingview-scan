---
name: rundayscan_pivot
description: "Reads dayscan_pivot_results.html, adds stocks to DAYSCAN watchlist in TradingView, marks Entry/SL/TP on charts, and writes dashboard with full Pivot Points data."
---

Do NOT run DAYSCAN_PIVOT. Only read the existing files.

## ⚠️ CRITICAL RULE — NEVER OPEN CHROME
This skill works ONLY with the TradingView Desktop App.
NEVER run chrome.exe, NEVER open Chrome web, NEVER suggest using the browser version.

## STEP 1 — Read data

Read: C:\Users\nsyon\SCAN\_pivot_scan_results.json
Extract for each symbol: symbol, direction, entry (P), sl, tp, rr, days_est, shares, rsi, vol_ratio, atr, P, R1, S1, R2, S2, scan_time.

## STEP 2 — Verify TradingView CDP connection

TradingView was already launched by dayscan_pivot — do NOT restart it.
Only verify the connection is alive:
Invoke-RestMethod http://localhost:9222/json | Where-Object { $_.url -like "*tradingview*" }

If the connection is not found, notify the user: "אנא הפעל תחילה את dayscan_pivot" and STOP.

## STEP 3 — Add TOP symbols to DAYSCAN watchlist

Run: C:\Users\nsyon\SCAN\tv_watchlist_pivot.py

TOP 5 LONG + TOP 5 SHORT (10 symbols total) are added automatically from dayscan_pivot_results.html.
How it works:
- Opens watchlist panel using [data-name="base-watchlist-widget-button"]
- Switches to DAYSCAN watchlist
- For each symbol: clicks add-symbol-button → Input.insertText → Enter → Escape

## STEP 4 — Mark Entry/SL/TP on charts and SAVE

Run: C:\Users\nsyon\SCAN\tv_mark_charts_pivot.py

Only TOP 5 LONG + TOP 5 SHORT are processed.
For each symbol:
1. Navigate to https://www.tradingview.com/chart/?symbol=SYMBOL
2. Wait 8 seconds for chart to load
3. Find widget via: for(var k in window){ if(window[k] && typeof window[k].activeChart==='function') }
4. chart.removeAllShapes() — delete all existing drawings first
5. chart.createShape for Entry (P) (green #1D9E75) with label "Entry (P) - LONG/SHORT | DD.MM.YYYY"
6. chart.createShape for Stop Loss (red #D85A30) with label "Stop Loss"
7. chart.createShape for Take Profit (blue #185FA5) with label "Take Profit"
8. Call widget.saveChartToServer(null, null, {}) to persist drawings to server

## STEP 5 — Write dashboard

Write to: C:\Users\nsyon\SCAN\rundayscan_pivot_dashboard.html

Read data from: C:\Users\nsyon\SCAN\_pivot_scan_results.json

Interactive dark-theme HTML dashboard:

METRICS BAR (top):
- Total setups / LONG count / SHORT count / Avg R:R / Avg Days Est.

FILTER BUTTONS:
- All / LONG only / SHORT only

MAIN TABLE (all symbols):
Columns:
  Symbol | P (תאריך) | כיוון | R1 | S1 | R2 | S2 | Days Est. | קנייה ב-$100 | Score

- P (תאריך) = Pivot value + scan date in brackets, e.g. "58.19 (02.06.2026)"
- כיוון = LONG (green) if last_close > P, SHORT (red) if last_close < P
- LONG rows: green left border (#00cc66)
- SHORT rows: red left border (#ff4444)
- Clickable rows — clicking opens detail panel

DETAIL PANEL (shown on row click):
- Symbol name (large, bold)
- כיוון badge (green=LONG / red=SHORT)
- P (Pivot): $XX.XX — נקודת כניסה
- R1: $XX.XX — התנגדות 1 (Take Profit LONG)
- S1: $XX.XX — תמיכה 1 (Stop Loss LONG)
- R2: $XX.XX — התנגדות 2
- S2: $XX.XX — תמיכה 2
- Days Est.: X.X ימים
- קנייה ב-$100: XX מניות
- RSI: XX | ATR: XX | Volume: ×XX
- "Open in TradingView" button → https://www.tradingview.com/chart/?symbol=SYMBOL

FOOTER:
- Scan date/time
- "Data: Yahoo Finance | Pivot Points: Standard Floor"
- File path: C:\Users\nsyon\SCAN\rundayscan_pivot_dashboard.html

Style:
- Background: #111
- Text: #eee
- Font: Arial
- Dark cards with colored borders
