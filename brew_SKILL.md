---
name: brew
description: "מנהל את watchlists CoffeeL (לונג) ו-CoffeeS (שורט) — ניקוי, הוספת מועמדים, והעתקה בין רשימות. תשתית לסקילים שמאכלסים את הרשימות לפני הרצת dayscan_pivot."
---

## מתי להשתמש
- כשהמשתמש כותב: `brew clean`, `brew cleanL`, `brew cleanS`, `brew demoL`, `brew demoS`
- כשהמשתמש כותב: `brew copy2L <שם>`, `brew copy2S <שם>`
- לפני הרצת `dayscan_pivot` — כדי לאכלס את CoffeeL / CoffeeS

---

## דרישות מקדימות

TradingView Desktop חייב לרוץ עם CDP (port 9222).
אם לא רץ — הפעל:

```powershell
taskkill /f /im TradingView.exe
Start-Sleep -Seconds 2
Start-Process 'C:\Program Files\WindowsApps\TradingView.Desktop_3.2.0.7916_x64__n534cwy3pjxzj\TradingView.exe' -ArgumentList '--remote-debugging-port=9222','--remote-allow-origins=*'
Start-Sleep -Seconds 12
```

---

## פקודות

| מה המשתמש כותב | פקודה להריץ | מה עושה |
|----------------|-------------|---------|
| `brew clean` | `python C:\Users\nsyon\SCAN\brew.py clean` | מנקה CoffeeL + CoffeeS |
| `brew cleanL` | `python C:\Users\nsyon\SCAN\brew.py cleanL` | מנקה CoffeeL בלבד |
| `brew cleanS` | `python C:\Users\nsyon\SCAN\brew.py cleanS` | מנקה CoffeeS בלבד |
| `brew demoL` | `python C:\Users\nsyon\SCAN\brew.py demoL` | מוסיף Yahoo day_gainers → CoffeeL |
| `brew demoS` | `python C:\Users\nsyon\SCAN\brew.py demoS` | מוסיף Yahoo day_losers → CoffeeS |
| `brew copy2L <שם>` | `python C:\Users\nsyon\SCAN\brew.py copy2L <שם>` | מעתיק ליסט → CoffeeL |
| `brew copy2S <שם>` | `python C:\Users\nsyon\SCAN\brew.py copy2S <שם>` | מעתיק ליסט → CoffeeS |

---

## הרצה

בצע את הפקודה המתאימה לפי הטבלה למעלה.
הצג למשתמש את הפלט כמו שהוא — אל תוסיף ניתוח.

---

## קבצים
- `C:\Users\nsyon\SCAN\brew.py` — הקוד
- `C:\Users\nsyon\SCAN\brew_SKILL.md` — הסקיל הזה
