---
name: ticker-report
description: "Ticker Report — מקבל רשימת טיקרים ומפיק אקסל עם ציון לונג (0-100), ATR ו-ADX יומיים, זיהוי נר אחרון (פטיש / איש תלוי / נר אדום / נר 2/3 ירוק אחרי אדום / בולעני) ותמיכות/התנגדויות קרובות. הפעל כאשר המשתמש כותב: ticker report, דוח טיקרים, או שולח רשימת טיקרים ומבקש ציונים."
---

## שפה
**תמיד לענות למשתמש בעברית**, גם כשהוא כותב באנגלית. מונחים טכניים (ATR, ADX, RSI, טיקרים, קוד) אפשר להשאיר באנגלית.


## מתי להשתמש
- המשתמש שולח רשימת טיקרים (מופרדים בפסיקים) ומבקש ציון / ATR / ADX / נרות / רמות
- המשתמש כותב: `ticker report`, `דוח טיקרים`

---

## שלב 1 — זיהוי בורסה
קרא ל-`mcp-tv-get-symbol-data-batch` עם `NASDAQ:<T>` / `NYSE:<T>` (עד 50 בקריאה).
טיקר שמופיע ב-`missing` — נסה את הבורסה השנייה (NYSE / NASDAQ / AMEX).

## שלב 2 — משיכת אינדיקטורים (קריאה אחת)
`mcp-tv-get-symbol-data-batch` עם העמודות:

```
open high low close ATR ADX ADX+DI ADX-DI RSI EMA20 EMA50
Pivot.M.Classic.Middle Pivot.M.Classic.R1 Pivot.M.Classic.R2
Pivot.M.Classic.S1 Pivot.M.Classic.S2 High.1M Low.1M High.3M Low.3M
average_volume_10d_calc
```

## שלב 3 — נר קודם
לכל טיקר: `mcp-tv-get-ohlcv` עם `count=3, format=columns, interval=1D`.
- `last` = הבר האחרון, `prev` = הבר שלפניו
- אם השוק עדיין פתוח (הבר האחרון בתהליך) — השתמש בבר שלפניו כ-`last` ובזה שלפניו כ-`prev`

## שלב 4 — קובץ JSON
שמור את הנתונים כ-`reports/data_YYYY-MM-DD.json` במבנה:

```json
{"date": "YYYY-MM-DD", "tickers": {"NASDAQ:XXX": {
  "prev": [o,h,l,c], "last": [o,h,l,c],
  "ATR": 0, "ADX": 0, "DIp": 0, "DIm": 0, "RSI": 0, "EMA20": 0, "EMA50": 0,
  "PP": 0, "R1": 0, "R2": 0, "S1": 0, "S2": 0,
  "H1M": 0, "L1M": 0, "H3M": 0, "L3M": 0, "vol10": 0}}}
```

דוגמה מלאה: `reports/data_2026-10-21.json`

## שלב 5 — הפקת האקסל

```bash
python3 ticker_report.py reports/data_YYYY-MM-DD.json reports/ticker_report_YYYY-MM-DD.xlsx
```

## שלב 6 — מסירה
- commit + push של ה-JSON וה-xlsx
- שלח למשתמש את הקובץ + לינק הורדה:
  `https://github.com/nsyoni10/tradingview-scan/raw/<branch>/reports/ticker_report_YYYY-MM-DD.xlsx`
- סיכום קצר: TOP לפי ציון, נרות בולטים (פטיש / 2/3), אזהרות (איש תלוי, RSI קיצוני, מחיר "קפוא")

---

## לוגיקה (ב-`ticker_report.py`)
- **מגמה:** עולה = סגירה > EMA20 > EMA50 ו-+DI > -DI; יורדת = ההפך; אחרת מעורבת
- **ציון לונג (100):** מבנה EMA 25 | ADX עם +DI>-DI 20 | עליונות +DI 10 | נר 25 | RSI 45-68 10 | מרחב ≥1.5 ATR להתנגדות 10
- **נרות:** פטיש (צל תחתון ≥ 2×גוף) — במגמה עולה = איש תלוי; נר 2/3 = גוף ≥ 2/3 מהטווח, ירוק אחרי אדום
- **רמות:** Pivot חודשי, שיא/שפל חודש ו-3 חודשים, EMA20/50, גבוה/נמוך של 2 הנרות האחרונים; רמות במרחק < 0.25 ATR מאוחדות
- **מחיר קפוא:** ATR < 0.5% מהמחיר → ציון 0 (ייתכן מיזוג/רכישה)
