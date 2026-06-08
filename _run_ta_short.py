import ssl, urllib.request, json, os
ssl._create_default_https_context = ssl._create_unverified_context
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = "C:/Users/nsyon/reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_data(symbol, period='6mo'):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={period}&interval=1d'
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

def calculate_indicators(df):
    df['SMA20'] = df['Close'].rolling(20).mean()
    df['SMA50'] = df['Close'].rolling(50).mean()
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain / loss))
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    df['BB_mid'] = df['Close'].rolling(20).mean()
    bb_std = df['Close'].rolling(20).std()
    df['BB_upper'] = df['BB_mid'] + 2 * bb_std
    df['BB_lower'] = df['BB_mid'] - 2 * bb_std
    df['Volatility'] = df['Close'].pct_change().rolling(20).std() * np.sqrt(252) * 100
    return df

def get_recommendation(rsi, macd, signal, price, sma20, sma50):
    score = 0
    if rsi < 30: score += 2
    elif rsi < 45: score += 1
    elif rsi > 70: score -= 2
    elif rsi > 60: score -= 1
    if macd > signal: score += 1
    else: score -= 1
    if price > sma20 > sma50: score += 2
    elif price < sma20 < sma50: score -= 2
    if score >= 3: return 'STRONG BUY', 'bullish'
    elif score >= 1: return 'BUY', 'bullish'
    elif score == 0: return 'HOLD', 'neutral'
    elif score >= -2: return 'SELL', 'bearish'
    else: return 'STRONG SELL', 'bearish'

def analyze(symbols):
    results = []
    for symbol in symbols:
        try:
            df = calculate_indicators(fetch_data(symbol)).dropna()
            latest, prev = df.iloc[-1], df.iloc[-2]
            price = latest['Close']
            change_pct = (price - prev['Close']) / prev['Close'] * 100
            rsi = latest['RSI']
            macd = latest['MACD']
            sig = latest['Signal']
            vol = latest['Volatility']
            rec, sentiment = get_recommendation(rsi, macd, sig, price, latest['SMA20'], latest['SMA50'])

            date_str = datetime.now().strftime('%Y-%m-%d')
            fig = plt.figure(figsize=(16, 12))
            gs = gridspec.GridSpec(3, 2, figure=fig)
            ax1 = fig.add_subplot(gs[0, :])
            ax1.plot(df.index, df['Close'], label='Price', color='#1f77b4', linewidth=2)
            ax1.plot(df.index, df['SMA20'], label='SMA20', color='orange', linestyle='--')
            ax1.plot(df.index, df['SMA50'], label='SMA50', color='red', linestyle='--')
            ax1.fill_between(df.index, df['BB_upper'], df['BB_lower'], alpha=0.1, color='blue')
            ax1.set_title(f'{symbol} - Price & Moving Averages', fontsize=14, fontweight='bold')
            ax1.legend(); ax1.grid(True, alpha=0.3)
            ax2 = fig.add_subplot(gs[1, 0])
            ax2.plot(df.index, df['RSI'], color='purple', linewidth=1.5)
            ax2.axhline(70, color='red', linestyle='--', alpha=0.7, label='Overbought')
            ax2.axhline(30, color='green', linestyle='--', alpha=0.7, label='Oversold')
            ax2.fill_between(df.index, df['RSI'], 50, where=df['RSI']>=50, alpha=0.3, color='green')
            ax2.fill_between(df.index, df['RSI'], 50, where=df['RSI']<50, alpha=0.3, color='red')
            ax2.set_title('RSI (14)', fontsize=12, fontweight='bold')
            ax2.legend(); ax2.grid(True, alpha=0.3)
            ax3 = fig.add_subplot(gs[1, 1])
            ax3.plot(df.index, df['MACD'], label='MACD', color='blue', linewidth=1.5)
            ax3.plot(df.index, df['Signal'], label='Signal', color='red', linewidth=1.5)
            colors = ['green' if m > s else 'red' for m, s in zip(df['MACD'], df['Signal'])]
            ax3.bar(df.index, df['MACD'] - df['Signal'], alpha=0.4, color=colors, width=1)
            ax3.set_title('MACD', fontsize=12, fontweight='bold')
            ax3.legend(); ax3.grid(True, alpha=0.3)
            ax4 = fig.add_subplot(gs[2, :])
            ax4.fill_between(df.index, df['Volatility'], alpha=0.5, color='orange')
            ax4.plot(df.index, df['Volatility'], color='darkorange', linewidth=1.5)
            ax4.set_title('Historical Volatility (20-day)', fontsize=12, fontweight='bold')
            ax4.grid(True, alpha=0.3)
            plt.suptitle(f'{symbol} Technical Dashboard | {date_str}', fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f'{OUTPUT_DIR}/{symbol}_dashboard.png', dpi=150, bbox_inches='tight')
            plt.close()

            results.append({
                'symbol': symbol, 'price': round(price, 2), 'change_pct': round(change_pct, 2),
                'rsi': round(rsi, 1), 'vol': round(vol, 1), 'rec': rec, 'sentiment': sentiment,
                'sma20': round(latest['SMA20'], 2), 'sma50': round(latest['SMA50'], 2),
                'macd': round(macd, 4), 'signal': round(sig, 4)
            })
            print(f'OK {symbol}')
        except Exception as e:
            print(f'ERROR {symbol}: {e}')
    return results

symbols = 'MCD,ABT,BAM,B,SE,EA,FOXA,FOX,INCY,AMCR,TLK,FMS,BJ,ORI,KRMN,CAE,RYTM,PTCT,ESNT,OLLI,KRC,DNLI,TARS,ZBIO'.split(',')
results = analyze(symbols)
with open('_trading_analysis_short.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f'Saved {len(results)} results to _trading_analysis_short.json')
