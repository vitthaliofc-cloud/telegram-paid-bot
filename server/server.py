from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET = os.getenv("CASHFREE_SECRET")

@app.route("/")
def home():
    return "Server running ✅"

# 🔥 CREATE PAYMENT LINK
@app.route("/pay")
def pay():
    user_id = request.args.get("user_id")
    video_id = request.args.get("video_id")

    url = "https://api.cashfree.com/pg/orders"

    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET,
        "Content-Type": "application/json"
    }

    data = {
        "order_id": f"{user_id}_{video_id}",
        "order_amount": 10,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": user_id,
            "customer_phone": "9999999999"
        }
    }

    res = requests.post(url, json=data, headers=headers).json()

    return jsonify({"payment_link": res["payment_link"]})

# 🔥 AUTO VERIFY
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data["type"] == "PAYMENT_SUCCESS_WEBHOOK":
        order_id = data["data"]["order"]["order_id"]

        user_id, video_id = order_id.split("_")

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
            data={
                "chat_id": user_id,
                "from_chat_id": CHANNEL_ID,
                "message_id": int(video_id)
            }
        )

    return "OK"
