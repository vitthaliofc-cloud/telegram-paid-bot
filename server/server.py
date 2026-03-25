from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET = os.getenv("CASHFREE_SECRET")


@app.route("/")
def home():
    return "Server running"


@app.route("/pay")
def pay():
    user_id = request.args.get("user_id")
    video_id = request.args.get("video_id")

    url = "https://sandbox.cashfree.com/pg/orders"

    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET,
        "Content-Type": "application/json",
        "x-api-version": "2022-09-01"
    }

    order_id = f"{user_id}_{video_id}_{int(time.time())}"

    data = {
        "order_id": order_id,
        "order_amount": 10,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": user_id,
            "customer_phone": "9999999999"
        }
    }

    res = requests.post(url, json=data, headers=headers).json()

    # 🔍 DEBUG PRINT
    print("FULL RESPONSE:", res)

    payment_session_id = res.get("payment_session_id")

    # 🔥 CLEAN SESSION ID
    if payment_session_id:
        payment_session_id = str(payment_session_id).strip()

    print("CLEAN SESSION ID:", payment_session_id)

    # ❌ अगर invalid असेल तर error return
    if not payment_session_id or "None" in payment_session_id:
        return jsonify({
            "error": "Invalid session id",
            "full_response": res
        })

    # ✅ SAFE LINK GENERATION (NO CORRUPTION)
    payment_link = "https://payments.cashfree.com/pg/view/checkout?payment_session_id=" + payment_session_id

    return jsonify({"payment_link": payment_link})


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook Data:", data)

    try:
        if data.get("type") in ["PAYMENT_SUCCESS_WEBHOOK", "PAYMENT_SUCCESS"]:
            order = data["data"]["order"]
            order_id = order["order_id"]

            user_id, video_id = order_id.split("_")

            # 🎬 Send Movie
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
                data={
                    "chat_id": user_id,
                    "from_chat_id": CHANNEL_ID,
                    "message_id": int(video_id)
                }
            )
