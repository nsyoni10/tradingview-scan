---
name: rundayscan
description: "\"\\\"Reads dayscan_results.html, adds stocks to DAYSCAN watchlist in TradingView, marks Entry/SL/TP on charts, and writes dashboard. Triggers on: 'הפעל דייסקן', 'RunDayscan', 'show dayscan dashboard', 'daily scan'.\\\"\""
---

Do NOT run DAYSCAN. Only read the existing HTML file.

## STEP 1 — Read data

Read: C:\Users\nsyon\SCAN\dayscan_results.html
Extract: Symbol, Direction (LONG/SHORT), Entry, Stop Loss, Take Profit from all rows.
Extract scan date/time from the <p> tag.

## STEP 2 — Verify TradingView CDP connection

TradingView was already launched by dayscan — do NOT restart it.
Only verify the connection is alive:
Invoke-RestMethod http://localhost:9222/json | Where-Object { $_.url -like "*tradingview*" }

If the connection is not found, notify the user to run dayscan first.

## STEP 3 — Add TOP 10 symbols to DAYSCAN watchlist

Run: C:\Users\nsyon\SCAN\tv_watchlist.py

Only TOP 5 LONG + TOP 5 SHORT (10 symbols total) are added.
How it works:
- Clicks [data-name="watchlists-button"] to open dropdown
- Waits 800ms, finds element with text "DAYSCAN", clicks it
- For each symbol: clicks [data-name="add-symbol-button"] → Input.insertText → Enter (13) → Escape (27)
- Verifies via [data-symbol-full] attributes

## STEP 4 — Mark Entry/SL/TP on charts and SAVE

Run: C:\Users\nsyon\SCAN\tv_mark_charts.py

Only TOP 10 symbols are processed.
For each symbol:
1. Navigate to https://il.tradingview.com/chart/?symbol=SYMBOL
2. Wait 5 seconds for chart to load
3. Find widget via: for(var k in window){ if(window[k] && typeof window[k].activeChart==='function') }
4. chart.removeAllShapes() — delete all existing drawings first
5. chart.createShape for Entry (green #1D9E75) with label "Entry - LONG/SHORT | DD.MM.YYYY"
6. chart.createShape for Stop Loss (red #D85A30)
7. chart.createShape for Take Profit (blue #185FA5)
8. Call widget.saveChartToServer(null, null, {}) to persist drawings to server

## STEP 5 — Write dashboard

Write to: C:\Users\nsyon\SCAN\rundayscan_dashboard.html
Interactive dark-theme HTML dashboard with:
- Metrics bar: Total / LONG / SHORT / Avg R:R
- Filter buttons: All / LONG only / SHORT only
- Table with all symbols, clickable rows
- Detail panel: Entry, Stop Loss, Take Profit with % from entry
- "Open in TradingView" button per symbol