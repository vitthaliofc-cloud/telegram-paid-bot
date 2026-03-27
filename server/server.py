import os
import requests
from flask import Flask, request

# 🔑 ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY")

app = Flask(__name__)

print("🚀 Server started")

# 🧠 Temporary DB
users_orders = {}

# 🎬 Movie links
movies = {
    "17": "https://yourdomain.com/movie17.mp4"
}

# 📩 Send message to Telegram
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": text
        })
    except Exception as e:
        print("Telegram send error:", e)

# 💳 Create Cashfree Order
def create_order(order_id, amount, user_id):
    print("🔥 create_order function called")

    url = "https://api.cashfree.com/pg/orders"

    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-version": "2023-08-01"
    }

    data = {
        "order_id": order_id,
        "order_amount": amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user_id),
            "customer_phone": "9999999999",
            "customer_email": "test@gmail.com"
        }
    }

    try:
        res = requests.post(url, json=data, headers=headers)
        print("✅ STATUS:", res.status_code)
        print("✅ RESPONSE:", res.text)
        return res.json()
    except Exception as e:
        print("Cashfree error:", e)
        return {}

# 🤖 Telegram Webhook
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    try:
        print("🔥 TELEGRAM HIT")

        data = request.get_json(force=True)
        print("📩 Incoming:", data)

        if not data:
            return "ok"

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

        return "ok"

    except Exception as e:
        print("❌ WEBHOOK ERROR:", e)
        return "ok"

# 🔔 Cashfree Webhook (Payment Success)
@app.route("/webhook", methods=["POST"])
def cashfree_webhook():
    data = request.get_json()

    print("💰 Cashfree Webhook:", data)

    try:
        if data["type"] == "PAYMENT_SUCCESS":
            order_id = data["data"]["order"]["order_id"]

            if order_id in users_orders:
                chat_id = users_orders[order_id]["chat_id"]
                movie_id = users_orders[order_id]["movie_id"]

                movie_link = movies.get(movie_id, "❌ Movie not found")

                send_message(chat_id, f"🎬 Here is your movie:\n{movie_link}")

    except Exception as e:
        print("Webhook error:", e)

    return "OK"

# 🌐 Home
@app.route("/")
def home():
    return "Bot Running 🚀"

# 🚀 Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
