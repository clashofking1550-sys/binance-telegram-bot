import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests

# ------------------- ضع معلوماتك هنا -------------------
TELEGRAM_TOKEN = "8906463254:AAGvQkCDwcm89j5_Pi_acP1nF1MqsWzSZxI"
TELEGRAM_CHAT_ID = "2063919632"
# ------------------------------------------------------

# إعداد الاتصال بباينانس سبوت
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"خطأ في إرسال الإشعار: {e}")

def scan_market():
    print("🔍 جاري فحص سوق باينانس سبوت...")
    try:
        exchange.load_markets()
    except Exception as e:
        print(f"خطأ في الاتصال بالمنصة: {e}")
        return

    # استخراج عملات الـ Spot فقط المستهدفة بـ USDT
    symbols = [s for s in exchange.symbols if s.endswith('/USDT') and ':' not in s]

    for symbol in symbols:
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker['last']
            volume_24h = ticker['quoteVolume'] # السيولة بـ USDT

            # الشروط: السعر أقل من 10$ والعملة غير خاملة (سيولة 24س أكثر من 200,000$)
            if price and price < 10 and volume_24h > 200000:
                # جلب بيانات الشمعات (إطار 15 دقيقة)
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=100)
                df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

                # حساب المؤشرات
                df['EMA_7'] = ta.ema(df['close'], length=7)
                df['EMA_25'] = ta.ema(df['close'], length=25)
                df['RSI'] = ta.rsi(df['close'], length=14)

                # حساب Supertrend (10, 3)
                st = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3)
                df['ST_direction'] = st['SUPERTd_10_3.0']

                last = df.iloc[-1]
                prev = df.iloc[-2]

                # شروط التجميع (Confluence Signals):
                ema_cross = (prev['EMA_7'] <= prev['EMA_25']) and (last['EMA_7'] > last['EMA_25'])
                supertrend_buy = (prev['ST_direction'] == -1) and (last['ST_direction'] == 1)
                rsi_buy = 50 <= last['RSI'] <= 70

                # إذا تحققت الإشارات
                if (ema_cross or supertrend_buy) and rsi_buy:
                    msg = (
                        f"🚀 *تنبيه انطلاقة مبكرة!*\n\n"
                        f"📌 *العملة:* {symbol}\n"
                        f"💵 *السعر:* ${price:.4f}\n"
                        f"📊 *مؤشر RSI:* {last['RSI']:.1f}\n"
                        f"📈 *حجم التداول 24س:* ${volume_24h:,.0f}\n\n"
                        f"💡 تم اكتشاف تقاطع إيجابي وبداية زخم صاعد."
                    )
                    send_telegram_alert(msg)
                    print(f"✅ تم اكتشاف إشارة في {symbol} وإرسال التنبيه!")
                  except Exception as e:
        continue

print(f"✨ تم الانتهاء من الفحص! تم فحص {count} عملة مطابقة للشروط، وإرسال {found_signals} تنبيه.")
