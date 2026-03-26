import os
import requests
from flask import Flask, request
from telegram import Bot

# 🔑 ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_ID = os.getenv("CASHFREE_APP_ID")
SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY")

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# 🧠 Temporary DB (replace with real DB later)
users_orders = {}

# 🎬 Movie links (example)
movies = {
    "17": "https://yourdomain.com/movie17.mp4"
}

# 🔹 Create Payment Order
def create_order(order_id, amount, user_id):
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
            "customer_phone": "9999999999"
        }
    }

    res = requests.post(url, json=data, headers=headers)
    return res.json()

# 🔹 Telegram Webhook (receive messages)
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text.startswith("/start"):
            try:
                movie_id = text.split(" ")[1]
            except:
                bot.send_message(chat_id, "❌ Use: /start 17")
                return "ok"

            order_id = f"order_{chat_id}_{movie_id}"

            users_orders[order_id] = {
                "chat_id": chat_id,
                "movie_id": movie_id
            }

            order = create_order(order_id, 10, chat_id)

            if "payment_link" in order:
                bot.send_message(chat_id, f"💳 Pay ₹10:\n{order['payment_link']}")
            else:
                bot.send_message(chat_id, f"❌ Error: {order}")

    return "ok"

# 🔔 Cashfree Webhook
@app.route("/webhook", methods=["POST"])
def cashfree_webhook():
    data = request.json

    try:
        if data["type"] == "PAYMENT_SUCCESS":
            order_id = data["data"]["order"]["order_id"]

            if order_id in users_orders:
                chat_id = users_orders[order_id]["chat_id"]
                movie_id = users_orders[order_id]["movie_id"]

                movie_link = movies.get(movie_id, "❌ Movie not found")

                bot.send_message(chat_id, f"🎬 Here is your movie:\n{movie_link}")

    except Exception as e:
        print("Webhook error:", e)

    return "OK"

# 🌐 Home
@app.route("/")
def home():
    return "Bot Running 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
