# -*- coding: utf-8 -*-
"""
dw_skill_gainers.py — סקיל איסוף ראשון: מניות עולות (gainers)
============================================================
תפקיד: *איסוף בלבד*. אין סינון, אין דירוג, אין ניתוח —
כל זה קורה במורד הזרם (dayscan_pivot + 2 הסקרינרים).

מחזיר רשימת טיקרים (bare). הקונטיינר אחראי על הכתיבה ל-TradingView.
מקור: Yahoo Finance predefined screener — day_gainers.
"""
import requests, warnings
warnings.filterwarnings('ignore')

H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(count=25):
    url = (f'https://query1.finance.yahoo.com/v1/finance/screener/'
           f'predefined/saved?scrIds=day_gainers&count={count}')
    r = requests.get(url, headers=H, verify=False, timeout=15)
    quotes = r.json()['finance']['result'][0]['quotes']
    # איסוף בלבד — מחזיר טיקרים כפי שהם
    return [q['symbol'] for q in quotes]

if __name__ == '__main__':
    syms = fetch()
    print(f"gainers ({len(syms)}): {syms}")
