import ssl, urllib.request, json, os, sys
ssl._create_default_https_context = ssl._create_unverified_context
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

OUTPUT_DIR = 'C:/Users/nsyon/reports'
os.makedirs(OUTPUT_DIR, exist_ok=True)

symbols = sys.argv[1].split(',') if len(sys.argv) > 1 else []

def fetch_data(symbol):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=6mo&interval=1d'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    result = data['chart']['result'][0]
    q = result['indicators']['quote'][0]
    df = pd.DataFrame({
        'Open': q['open'], 'High': q['high'],
        'Low': q['low'], 'Close': q['close'], 'Volume': q['volume'],
    }, index=pd.to_datetime(result['timestamp'], unit='s'))
    return df.dropna()

def calc(df):
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()
    d = df['Close'].diff()
    g = d.clip(lower=0).rolling(14).mean()
    l = -d.clip(upper=0).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + g / l))
    e12 = df['Close'].ewm(span=12).mean()
    e26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = e12 - e26
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    std = df['Close'].rolling(20).std()
    df['BB_upper'] = df['SMA20'] + 2 * std
    df['BB_lower'] = df['SMA20'] - 2 * std
    df['Volatility'] = df['Close'].pct_change().rolling(20).std() * np.sqrt(252) * 100
    return df

def get_rec(rsi, macd, sig, price, s20, s50):
    sc = 0
    if rsi < 30: sc += 2
    elif rsi < 45: sc += 1
    elif rsi > 70: sc -= 2
    elif rsi > 60: sc -= 1
    if macd > sig: sc += 1
    else: sc -= 1
    if price > s20 > s50: sc += 2
    elif price < s20 < s50: sc -= 2
    if sc >= 3: return 'STRONG BUY', 'bullish'
    elif sc >= 1: return 'BUY', 'bullish'
    elif sc == 0: return 'HOLD', 'neutral'
    elif sc >= -2: return 'SELL', 'bearish'
    else: return 'STRONG SELL', 'bearish'

results = []
for sym in symbols:
    try:
        df = calc(fetch_data(sym)).dropna()
        r = df.iloc[-1]
        p = df.iloc[-2]
        price = r['Close']
        chg = (price - p['Close']) / p['Close'] * 100
        rc, sent = get_rec(r['RSI'], r['MACD'], r['Signal'], price, r['SMA20'], r['SMA50'])
        results.append({
            'symbol': sym, 'price': round(price, 2), 'change_pct': round(chg, 2),
            'rsi': round(r['RSI'], 1), 'vol': round(r['Volatility'], 1),
            'rec': rc, 'sentiment': sent,
            'sma20': round(r['SMA20'], 2), 'sma50': round(r['SMA50'], 2),
            'bb_upper': round(r['BB_upper'], 2), 'bb_lower': round(r['BB_lower'], 2),
            'macd': round(r['MACD'], 2), 'signal': round(r['Signal'], 2)
        })
        print(f"{sym:8} | {rc:12} | RSI={r['RSI']:.1f} | ${price:.2f}")
    except Exception as e:
        print(f"ERROR {sym}: {e}")

with open('C:/Users/nsyon/SCAN/_trading_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nנשמר {len(results)} מניות")
