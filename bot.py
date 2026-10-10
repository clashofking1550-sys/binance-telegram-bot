import os
import requests
import time
import ccxt
import pandas as pd
import numpy as np

# ----------------------------
# إعدادات متغيرات البيئة
# ----------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
# ----------------------------

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")

def calculate_indicators(df):
    # حساب المتوسطات ومؤشرات العزم للتحليل
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # حساب MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # حساب RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # حساب Stochastic (%K و %D)
    low_14 = df['low'].rolling(window=14).min()
    high_14 = df['high'].rolling(window=14).max()
    df['Stoch_K'] = (df['close'] - low_14) / (high_14 - low_14) * 100
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
    
    return df

def analyze_market():
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    try:
        exchange.load_markets()
        # نختار أهم العملات المقابلة لـ USDT لتخفيف الحمل وضمان السيولة
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOGE/USDT', 'LINK/USDT', 'DOT/USDT']
        
        send_telegram_message("🔍 *بدء دورة جديدة لفحص السوق واكتشاف الفرص...*")
        
        for symbol in symbols:
            try:
                # جلب بيانات الشموع (فريم 4 ساعات أو ساعة)
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='4h', limit=50)
                if len(ohlcv) < 50:
                    continue
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df = calculate_indicators(df)
                
                current_close = df['close'].iloc[-1]
                prev_close = df['close'].iloc[-2]
                
                rsi = df['RSI'].iloc[-1]
                macd = df['MACD'].iloc[-1]
                macd_signal = df['MACD_Signal'].iloc[-1]
                prev_macd = df['MACD'].iloc[-2]
                prev_macd_signal = df['MACD_Signal'].iloc[-2]
                
                stoch_k = df['Stoch_K'].iloc[-1]
                stoch_d = df['Stoch_D'].iloc[-1]
                prev_stoch_k = df['Stoch_K'].iloc[-2]
                prev_stoch_d = df['Stoch_D'].iloc[-2]
                
                # 1. التقاطع الإيجابي لمؤشر MACD و Stochastic
                macd_bullish_cross = (prev_macd <= prev_macd_signal) and (macd > macd_signal)
                stoch_bullish_cross = (prev_stoch_k <= prev_stoch_d) and (stoch_k > stoch_d)
                
                # 2. التشبع البيعي والسقوط الحر (RSI أقل من 30 مع محاولة ارتداد)
                is_oversold = rsi < 30
                
                # 3. صندوق جان (أقرب أدنى مستوى في آخر 30 شمعة كمنطقة دعم رئيسية)
                gann_box_low = df['low'].tail(30).min()
                near_gann_low = current_close <= (gann_box_low * 1.01) # القريب من قاع الصندوق بنسبة 1%
                
                # 4. التجهيز لانفجار (تقارب الشموع / تقلب منخفض يسبق الحركة القوية + تقاطع إيجابي)
                price_change_pct = ((current_close - prev_close) / prev_close) * 100
                
                alert_messages = []
                
                if macd_bullish_cross and stoch_bullish_cross:
                    alert_messages.append("⚡ *تقاطع إيجابي مزدوج (MACD + Stochastic)*")
                
                if is_oversold:
                    alert_messages.append(f"📉 *تشبع بيعي حاد وسقوط حر (RSI: {rsi:.1f})*")
                    
                if near_gann_low:
                    alert_messages.append(f"📦 *السعر وصل لأدنى مستوى في صندوق جان (الدعم: {gann_box_low})*")
                    
                if macd_bullish_cross and (current_close > df['EMA_20'].iloc[-1]):
                    alert_messages.append("🚀 *إشارة تجهيز لانفجار صعودي (Breakout Squeeze)*")

                # إذا تحققت أي شروط إيجابية، أرسل التنبيه فوراً
                if alert_messages:
                    msg = f"🚨 **تنبيه فرصة لعملة {symbol}** 🚨\n"
                    msg += f"💰 السعر الحالي: `{current_close}`\n"
                    msg += f"📊 مؤشر RSI: `{rsi:.1f}`\n\n"
                    msg += "الأسباب المكتشفة:\n" + "\n".join(alert_messages)
                    send_telegram_message(msg)
                
                time.sleep(1) # لتفادي الحظر من بينانس بسبب كثرة الطلبات
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                
    except Exception as e:
        print(f"Error in market analysis: {e}")

def main():
    send_telegram_message("🤖 *تم تحديث بوت التداول بنجاح لراصد الفرص وانفجارات العملات!*")
    
    while True:
        try:
            analyze_market()
            # الفحص كل ساعة لتوفير الموارد ومراقبة الإغلاقات بشكل دقيق
            time.sleep(3600) 
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
