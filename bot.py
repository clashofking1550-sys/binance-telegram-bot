import os
import requests
import time
import ccxt
import pandas as pd

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
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")

def main():
    send_telegram_message("🤖 بوت بينانس يعمل الآن بنجاح على Render!")
    exchange = ccxt.binance()
    
    while True:
        try:
            # مثال لجلب سعر البيتكوين وتحديث البيانات
            ticker = exchange.fetch_ticker('BTC/USDT')
            price = ticker['last']
            print(f"Current BTC Price: {price}")
            
            # يمكنك إضافة استراتيجية التنبيه الخاصة بك هنا
            
            time.sleep(60)  # الانتظار لمدة دقيقة قبل الفحص التالي
        except Exception as e:
            print(f"Error in loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
