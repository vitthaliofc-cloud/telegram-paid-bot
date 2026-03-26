import os
import requests
from flask import Flask, request
from telegram import Bot

# 🔑 ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET = os.getenv("CASHFREE_SECRET_KEY")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# 🧠 Temporary DB
users_orders = {}

# 🎬 Movie links
movies = {
    "17": "https://yourdomain.com/movie17.mp4"
}

# 🔹 Create Payment Order
def create_order(order_id, amount, user_id):
    print("🔥 create_order function called")

    url = "https://api.cashfree.com/pg/orders"

    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET,
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

    print("📤 Sending request to Cashfree...")

    try:
        res = requests.post(url, json=data, headers=headers)

        print("✅ STATUS:", res.status_code)
        print("✅ RESPONSE:", res.text)

        return res.json()

    except Exception as e:
        print("❌ Request error:", e)
        return {}

# 🔹 Telegram Webhook (MAIN FIX)
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json()

    print("📩 Incoming:", data)

    if "message" in data:
        message = data["message"]
        text = message.get("text", "")
        chat_id = message["chat"]["id"]

        print("User text:", text)

        if text.startswith("/start"):
            print("✅ Start command detected")

            parts = text.split(" ")

            if len(parts) < 2:
                bot.send_message(chat_id, "❌ Use: /start 17")
                return "ok"

            movie_id = parts[1]

            order_id = f"order_{chat_id}_{movie_id}"

            users_orders[order_id] = {
                "chat_id": chat_id,
                "movie_id": movie_id
            }

            order = create_order(order_id, 10, chat_id)

            print("ORDER RESPONSE:", order)

            # 🔥 FIX: payment_link safe access
            payment_link = order.get("payment_link")

            if payment_link:
                bot.send_message(chat_id, f"💳 Pay ₹10:\n{payment_link}")
            else:
                bot.send_message(chat_id, "⚠️ Payment server error, try later")

    return "ok"

# 🔔 Cashfree Webhook
@app.route("/webhook", methods=["POST"])
def cashfree_webhook():
    data = request.get_json()

    print("💰 Cashfree webhook:", data)

    try:
        if data.get("type") == "PAYMENT_SUCCESS":
            order_id = data["data"]["order"]["order_id"]

            if order_id in users_orders:
                chat_id = users_orders[order_id]["chat_id"]
                movie_id = users_orders[order_id]["movie_id"]

                movie_link = movies.get(movie_id, "❌ Movie not found")

                bot.send_message(chat_id, f"🎬 Here is your movie:\n{movie_link}")

    except Exception as e:
        print("❌ Webhook error:", e)

    return "OK"

# 🌐 Home
@app.route("/")
def home():
    return "Bot Running 🚀"

# 🚀 Run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
