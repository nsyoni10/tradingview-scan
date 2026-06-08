---
name: coffee
description: "☕ Coffee — סריקת בוקר יומית. מביא מדדי שוק (S&P, QQQ, VIX, נפט, זהב, אגח 10Y), חוזים עתידיים (ES, NQ, YM, RTY), מריץ morning-note, ומציג טבלאות TOP LONG/SHORT מ-dayscan_pivot עם כל השדות והציונים. הפעל כאשר המשתמש כותב: coffee, קופי, סקירת בוקר."
---

# ☕ Coffee — סריקת בוקר

## הרץ:
cd C:\Users\nsyon\SCAN
python build_coffee.py

## פתח בדפדפן:
start C:\Users\nsyon\SCAN\coffee_pivot.html

## הסקריפט מייצר קובץ אחד עם:
- 6 מדדים: S&P, QQQ, VIX, נפט, זהב, אגח 10Y
- 4 חוזים עתידיים: ES, NQ, YM, RTY
- Morning Note — סיכום בוקר עם כותרת ראשית, התפתחויות לילה, אירועים, רעיונות מסחר
- TOP LONG — כל השדות מ-trading-analysis + ציון
  - ה-TOP 10 שנבחרו (מ-_top10_long.json) מופיעים ראשונים לפי סדר הבחירה
  - שורות TOP 10 מוצגות בצבע צהוב
- TOP SHORT — כל השדות מ-trading-analysis + ציון
  - ה-TOP 10 שנבחרו (מ-_top10_short.json) מופיעים ראשונים לפי סדר הבחירה
  - שורות TOP 10 מוצגות בצבע צהוב
- כותרות עמודות מיושרות לצד ימין (RTL)
- הערות ריצה מ-dayscan_pivot

## תלויות:
- _trading_analysis_long.json (מ-dayscan_pivot שלב 2)
- _trading_analysis_short.json (מ-dayscan_pivot שלב 2)
- _top10_long.json (מ-dayscan_pivot שלב 3)
- _top10_short.json (מ-dayscan_pivot שלב 3)
- dayscan_pivot_notes.html (מ-dayscan_pivot שלב 4)

## הערה:
הגרסה הישנה שמורה כ-coffee_old_SKILL.md ומריצה coffee_news.py → coffee.html
