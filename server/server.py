import os
import requests
import threading
import time
from flask import Flask, request

app = Flask(__name__)

# ================== ENV VARIABLES ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY")

# ================== STORE ORDERS ==================
users_orders = {}

# ================== TELEGRAM SEND ==================
def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        res = requests.post(url, json={
            "chat_id": chat_id,
            "text": text
        }, timeout=10)

        print("📤 Telegram:", res.text)

    except Exception as e:
        print("❌ Telegram Error:", e)


# ================== CREATE CASHFREE ORDER ==================
def create_order(order_id, amount, chat_id):
    try:
        url = "https://api.cashfree.com/pg/orders"

        headers = {
            "x-client-id": CASHFREE_APP_ID,
            "x-client-secret": CASHFREE_SECRET_KEY,
            "Content-Type": "application/json",
            "x-api-version": "2022-09-01"
        }

        data = {
            "order_id": order_id,
            "order_amount": amount,
            "order_currency": "INR",
            "customer_details": {
                "customer_id": str(chat_id),
                "customer_phone": "9876543210"
            },
            "order_meta": {
                "return_url": "https://t.me/Running_MoviesBot",
                "notify_url": "https://telegram-paid-bot-production-fbf8.up.railway.app/cashfree-webhook"
            }
        }

        res = requests.post(url, json=data, headers=headers, timeout=10)
        print("💰 Cashfree:", res.text)

        return res.json()

    except Exception as e:
        print("❌ Cashfree Error:", e)
        return {}


# ================== PROCESS ORDER ==================
def process_order(chat_id, movie_id):
    try:
        print("🔥 process_order started")

        order_id = f"order_{chat_id}_{movie_id}_{int(time.time())}"

        users_orders[order_id] = {
            "chat_id": chat_id,
            "movie_id": movie_id
        }

        order = create_order(order_id, 10, chat_id)

        session_id = order.get("payment_session_id")

        if session_id:
            link = f"https://payments.cashfree.com/order/#/{session_id}"
            send_message(chat_id, f"💳 Pay ₹10:\n{link}")
        else:
            send_message(chat_id, f"❌ Payment Error:\n{order}")

    except Exception as e:
        print("❌ process_order Error:", e)


# ================== TELEGRAM WEBHOOK ==================
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    try:
        print("🔥 TELEGRAM HIT")

        data = request.get_json(force=True)
        print("📩 Incoming:", data)

        if "message" in data:
            message = data["message"]
            text = message.get("text", "")
            chat_id = message["chat"]["id"]

            if text.startswith("/start"):
                parts = text.split(" ")

                if len(parts) < 2:
                    send_message(chat_id, "❌ Use: /start 17")
                    return "ok"

                movie_id = parts[1]

                # 🚀 THREAD
                threading.Thread(
                    target=process_order,
                    args=(chat_id, movie_id)
                ).start()

                return "ok"

        return "ok"

    except Exception as e:
        print("❌ Webhook Error:", e)
        return "ok"


# ================== CASHFREE WEBHOOK ==================
@app.route("/cashfree-webhook", methods=["POST"])
def cashfree_webhook():
    try:
        data = request.json
        print("💥 Cashfree Webhook:", data)

        if data.get("type") == "PAYMENT_SUCCESS_WEBHOOK":
            order_id = data["data"]["order"]["order_id"]

            if order_id in users_orders:
                chat_id = users_orders[order_id]["chat_id"]
                movie_id = users_orders[order_id]["movie_id"]

                send_message(chat_id, f"✅ Payment Success!\n🎬 Movie ID: {movie_id}")

        return "ok"

    except Exception as e:
        print("❌ Webhook Error:", e)
        return "ok"


# ================== HOME ==================
@app.route("/")
def home():
    return "Bot Running 🚀"


# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Server running on", port)
    app.run(host="0.0.0.0", port=port)
