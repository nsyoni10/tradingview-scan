---
name: checkup
description: "Checkup — קורא את רשימת המעקב 'Check list' בטריידינגוויו, מנקד כל מניה לכניסה ללונג בתחילת מהלך (0-100) ומפיק Google Sheet בשם 'Summary of [תאריך]': מעל SMA150, RVOL ≥ 1.2, כיוון DI/ADX, CCI, מרובוזו ב-3 ימים, נר אחרון, תמיכות והתנגדויות. הפעל כאשר המשתמש כותב: checkup, צ'קאפ."
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
close ATR ADX ADX[1] ADX+DI ADX-DI CCI20 CCI20[1] EMA20 EMA50 SMA150
relative_volume_10d_calc average_volume_10d_calc
Pivot.M.Classic.Middle Pivot.M.Classic.R1 Pivot.M.Classic.R2
Pivot.M.Classic.S1 Pivot.M.Classic.S2 High.1M Low.1M High.3M Low.3M
```

## שלב 3 — נרות
לכל טיקר: `mcp-tv-get-ohlcv` עם `count=12, format=columns, interval=1D` (במקביל).
- `bars` = 12 הנרות `[o,h,l,c,v]` מהישן לחדש. מהם `checkup.py` גוזר את הנר האחרון והקודם, את ה-RVOL ואת המרובוזו.
- שגיאת 502 → לנסות שוב פעם אחת

## שלב 3א — בדיקת עקביות (חובה)
- תאריך הבר האחרון (`t`) חייב להיות יום המסחר האחרון שנסגר, זהה לכל הטיקרים → זה ה-`bar_date`.
- `close` מה-batch חייב להיות שווה ל-close של הבר האחרון. אם לא (למשל הסקרינר כבר התחיל יום חדש) — להשתמש בערכי ה-OHLCV ולציין זאת למשתמש.

## שלב 4 — JSON
שמור כ-`checkup_data/data_YYYY-MM-DD.json` (תאריך הבקשה לפי שעון ישראל):

```json
{"date": "YYYY-MM-DD", "bar_date": "YYYY-MM-DD", "watchlist": "Check list", "tickers": {"NASDAQ:XXX": {
  "bars": [[o,h,l,c,v], ...12],
  "ATR": 0, "ADX": 0, "ADX1": 0, "DIp": 0, "DIm": 0, "CCI": 0, "CCI1": 0, "EMA20": 0, "EMA50": 0,
  "SMA150": 0, "RVOL": 0,
  "PP": 0, "R1": 0, "R2": 0, "S1": 0, "S2": 0,
  "H1M": 0, "L1M": 0, "H3M": 0, "L3M": 0, "vol10": 0}}}
```

מיפוי: `ADX1` ← `ADX[1]`, `CCI/CCI1` ← `CCI20/CCI20[1]`, `RVOL` ← `relative_volume_10d_calc` (גיבוי בלבד), `vol10` ← `average_volume_10d_calc`, `DIp/DIm` ← `ADX+DI/ADX-DI`, `PP` ← `Pivot.M.Classic.Middle`.
דוגמה מלאה: `checkup_data/data_2026-10-26.json`

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
  - TOP לפי ציון כניסה
  - מניות עם כיוון ללונג (+DI > -DI) ו-ADX סביב 20 ומעלה
  - מרובוזו ב-3 הימים האחרונים, ווליום חריג על נר ירוק, CCI שיוצא מתיקון

---

## לוגיקה (`checkup.py`, משתמש בפונקציות של `ticker_report.py`)
מטרה: לתפוס **תחילת מהלך אחרי תיקון**, לא מגמה שכבר רצה. לכן אין RSI ואין ניקוד על מבנה EMA.
- **כיוון (30):** +DI > -DI = 15, ADX ≥ 20 = 10 (18-20 = 5), ADX עולה מאתמול = 5. כש-DI- מעל DI+ = 0
- **נר עם עוצמה (25):** מרובוזו ירוק היום 15 / ב-3 ימים האחרונים 10, ועוד דפוס הנר האחרון עד 10.
  מרובוזו = נר ירוק, גוף ≥ 85% מהטווח וגוף ≥ 0.5 ATR
- **ווליום (15):** ווליום היום האחרון חלקי ממוצע 10 הימים שלפניו (בלי היום עצמו), מחושב מהנרות. רק על נר ירוק: ≥1.5 = 15, ≥1.2 = 10, ≥1.0 = 4
- **CCI(20) (15):** חוצה למעלה את -100 או את 0 = 15, עולה מתחת ל-100 = 10, עולה מתחת ל-200 = 4
- **מעל SMA150 (10)**
- **לא מתוח (5):** סגירה עד 1.5 ATR מעל EMA20
- **רמות:** Pivot חודשי, שיא/שפל חודש ו-3 חודשים, EMA20/50, גבוה/נמוך 2 נרות אחרונים; רמות במרחק < 0.25 ATR מאוחדות
