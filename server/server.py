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
        "order_amount": 10.0,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(user_id),
            "customer_phone": "9999999999"
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        res = response.json()

        if "payment_session_id" not in res:
            return jsonify({"error": res})

        payment_session_id = res["payment_session_id"]

        payment_link = f"https://sandbox.cashfree.com/pg/view/checkout?payment_session_id={payment_session_id}"

        return jsonify({"payment_link": payment_link})

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Webhook:", data)

    try:
        if data.get("type") in ["PAYMENT_SUCCESS_WEBHOOK", "PAYMENT_SUCCESS"]:
            order = data["data"]["order"]
            order_id = order["order_id"]

            user_id, video_id = order_id.split("_")

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
                data={
                    "chat_id": user_id,
                    "from_chat_id": CHANNEL_ID,
                    "message_id": int(video_id)
                }
            )
    except Exception as e:
        print("Webhook Error:", e)

    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
