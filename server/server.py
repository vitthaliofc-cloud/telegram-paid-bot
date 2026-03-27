import os
import requests
import threading
from flask import Flask, request

app = Flask(__name__)

# ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY")

# STORE ORDERS
users_orders = {}

# ✅ SEND MESSAGE TO TELEGRAM
def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        res = requests.post(url, json={
            "chat_id": chat_id,
            "text": text
        }, timeout=10)

        print("📤 Telegram response:", res.text)

    except Exception as e:
        print("❌ Telegram send error:", e)


# ✅ CREATE CASHFREE ORDER
def create_order(order_id, amount, chat_id):
    try:
        print("🔥 create_order called")

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
                "customer_phone": "9999999999"
            }
        }

        res = requests.post(url, json=data, headers=headers, timeout=10)
        print("💰 Cashfree response:", res.text)

        return res.json()

    except Exception as e:
        print("❌ create_order error:", e)
        return {}


# ✅ BACKGROUND PROCESS
def process_order(chat_id, movie_id):
    try:
        print("🔥 process_order running")

        order_id = f"order_{chat_id}_{movie_id}"

        users_orders[order_id] = {
            "chat_id": chat_id,
            "movie_id": movie_id
        }

        order = create_order(order_id, 10, chat_id)

        print("ORDER:", order)

        if "payment_session_id" in order:
            link = f"https://payments.cashfree.com/order/#/{order['payment_session_id']}"
            send_message(chat_id, f"💳 Pay ₹10:\n{link}")
        else:
            send_message(chat_id, "❌ Payment error")

    except Exception as e:
        print("❌ process_order error:", e)


# ✅ TELEGRAM WEBHOOK
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

                # 🚀 THREAD START
                threading.Thread(
                    target=process_order,
                    args=(chat_id, movie_id)
                ).start()

                # ⚡ INSTANT RESPONSE
                return "ok"

        return "ok"

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e)
        return "ok"


# ✅ HOME ROUTE (TEST)
@app.route("/")
def home():
    return "Bot Running 🚀"


# ✅ RUN SERVER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Server started on port", port)
    app.run(host="0.0.0.0", port=port)
