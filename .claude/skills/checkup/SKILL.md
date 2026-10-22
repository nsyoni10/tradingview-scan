---
name: checkup
description: "Checkup — קורא את רשימת המעקב 'Check list' בטריידינגוויו, מנקד כל מניה ללונג (0-100) ומפיק Google Sheet בשם 'Summary of [תאריך]': מעל SMA150, RVOL ≥ 1.2, ATR/ADX יומיים, נר אחרון (פטיש / איש תלוי / נר אדום / נר 2/3 ירוק אחרי אדום), תמיכות והתנגדויות. הפעל כאשר המשתמש כותב: checkup, צ'קאפ."
---

## מתי מריצים — רק כשהשוק סגור
- **הרצה מותרת:** אחרי הסגירה (16:00 ET = 23:00 שעון ישראל) ועד הפתיחה (09:30 ET = 16:30 שעון ישראל).
- הנתונים מתייחסים תמיד ל**יום המסחר הרגיל האחרון שנסגר**. פרה-מרקט ואפטר-מרקט לא נכללים (גם ה-OHLCV של טריידינגוויו הוא Regular Session בלבד).
- **אם השוק פתוח בזמן ההרצה:** לעצור ולהודיע למשתמש שהנתונים חלקיים (RVOL ונר אחרון לא אמינים) ולא להפיק גיליון.

## מתי להשתמש
- המשתמש כותב `checkup` / `צ'קאפ`
- המשתמש מבקש סיכום יומי של רשימת "Check list"

---

## שלב 1 — קריאת הרשימה
`mcp-watchlist-list-watchlists` → הרשימה ששמה **`Check list`**.
- דלג על שורות שמתחילות ב-`###` (כותרות סקשן) ועל סימבולים בלי בורסה (בלי `:`).

## שלב 2 — אינדיקטורים (קריאה אחת, עד 50 סימבולים)
`mcp-tv-get-symbol-data-batch` עם העמודות:

```
open high low close volume ATR ADX ADX+DI ADX-DI RSI EMA20 EMA50 SMA150
relative_volume_10d_calc average_volume_10d_calc
Pivot.M.Classic.Middle Pivot.M.Classic.R1 Pivot.M.Classic.R2
Pivot.M.Classic.S1 Pivot.M.Classic.S2 High.1M Low.1M High.3M Low.3M
```

## שלב 3 — נר קודם
לכל טיקר: `mcp-tv-get-ohlcv` עם `count=2, format=columns, interval=1D` (במקביל).
- `prev` = הבר הראשון, `last` = הבר השני
- `last_vol` = הווליום של הבר האחרון (`v`)
- שגיאת 502 → לנסות שוב פעם אחת

## שלב 3א — בדיקת עקביות (חובה)
- תאריך הבר האחרון (`t`) חייב להיות יום המסחר האחרון שנסגר, זהה לכל הטיקרים → זה ה-`bar_date`.
- `close` מה-batch חייב להיות שווה ל-close של הבר האחרון. אם לא (למשל הסקרינר כבר התחיל יום חדש) — להשתמש בערכי ה-OHLCV ולציין זאת למשתמש.
- `checkup.py` מחשב בעצמו RVOL = `last_vol` / `vol10` כשיש `last_vol`, כך שהוא לא תלוי בתזמון של הסקרינר. מוסיף הערה אם הוא שונה ביותר מ-15% מה-RVOL של טריידינגוויו.

## שלב 4 — JSON
שמור כ-`checkup_data/data_YYYY-MM-DD.json` (תאריך הבקשה לפי שעון ישראל):

```json
{"date": "YYYY-MM-DD", "bar_date": "YYYY-MM-DD", "watchlist": "Check list", "tickers": {"NASDAQ:XXX": {
  "prev": [o,h,l,c], "last": [o,h,l,c],
  "ATR": 0, "ADX": 0, "DIp": 0, "DIm": 0, "RSI": 0, "EMA20": 0, "EMA50": 0,
  "SMA150": 0, "RVOL": 0, "last_vol": 0,
  "PP": 0, "R1": 0, "R2": 0, "S1": 0, "S2": 0,
  "H1M": 0, "L1M": 0, "H3M": 0, "L3M": 0, "vol10": 0}}}
```

מיפוי: `RVOL` ← `relative_volume_10d_calc`, `last_vol` ← `v` של הבר האחרון, `vol10` ← `average_volume_10d_calc`, `DIp/DIm` ← `ADX+DI/ADX-DI`, `PP` ← `Pivot.M.Classic.Middle`.
דוגמה מלאה: `checkup_data/data_2026-10-22.json`

## שלב 5 — חישוב

```bash
python3 checkup.py checkup_data/data_YYYY-MM-DD.json "checkup_data/Summary of YYYY-MM-DD.xlsx"
```

נוצרים `.xlsx` ו-`.csv` באותו שם.

## שלב 6 — Google Sheet
`Google_Drive create_file`:
- `title`: `Summary of YYYY-MM-DD`
- `contentMimeType`: `text/csv`
- `textContent`: תוכן קובץ ה-CSV
- Drive ממיר אוטומטית ל-Google Sheet.
- אם כבר קיים קובץ בשם הזה (`search_files`): ליצור את החדש ואז להעביר את הישן לפח (`trash_file`). אי אפשר להחליף תוכן של קובץ קיים — `update_file` משנה רק מטא-דאטה.

## שלב 7 — מסירה
- commit + push של ה-JSON, ה-CSV וה-xlsx
- למשתמש: לינק ל-Google Sheet + סיכום קצר:
  - TOP לפי ציון
  - מניות שעומדות בשני התנאים (✅ SMA150 + ✅ RVOL)
  - נרות בולטים ואזהרות (איש תלוי, RSI > 70, מגמת ירידה)

---

## לוגיקה (`checkup.py`, משתמש בפונקציות של `ticker_report.py`)
- **מעל SMA150:** סגירה > SMA150 יומי → ✅
- **RVOL ≥ 1.2:** ווליום אחרון / ממוצע 10 ימים → ✅
- **מגמה:** עולה = סגירה > EMA20 > EMA50 ו-+DI > -DI; יורדת = ההפך; אחרת מעורבת
- **ציון לונג (100):** מבנה EMA 20 | SMA150 10 | ADX עם +DI>-DI 15 | עליונות +DI 10 | נר 20 | RVOL 10 | RSI 45-68 10 | מרחב להתנגדות 5
- **נרות:** פטיש (צל תחתון ≥ 2×גוף) — במגמה עולה = איש תלוי; נר 2/3 = גוף ≥ 2/3 מהטווח, ירוק אחרי אדום
- **רמות:** Pivot חודשי, שיא/שפל חודש ו-3 חודשים, EMA20/50, גבוה/נמוך 2 נרות אחרונים; רמות במרחק < 0.25 ATR מאוחדות
