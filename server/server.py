from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # -100XXXXXXXXX

CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET = os.getenv("CASHFREE_SECRET")

# ✅ Payment link endpoint
@app.route("/pay")
def pay():
    user_id = request.args.get("user_id")
    video_id = request.args.get("video_id")

    url = "https://sandbox.cashfree.com/pg/orders"  # Sandbox / Live

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
            "customer_id": str(user_id),
            "customer_phone": "9999999999"
        }
    }

    res = requests.post(url, json=data, headers=headers).json()

    return jsonify({
        "payment_link": res.get("payment_link")
    })

# ✅ Webhook for auto verify
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    try:
        if data["type"] == "PAYMENT_SUCCESS_WEBHOOK":
            order = data["data"]["order"]
            order_id = order["order_id"]
            user_id, video_id = order_id.split("_")

            # 🎬 Send movie from channel
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
                data={
                    "chat_id": user_id,
                    "from_chat_id": CHANNEL_ID,
                    "message_id": int(video_id)
                }
            )
    except Exception as e:
        print("Webhook error:", e)

    return "OK"

if __name__ == "__main__":
    print("🔥 Server started…")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
