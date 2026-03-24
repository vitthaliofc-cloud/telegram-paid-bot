from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

# ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID")
CASHFREE_SECRET = os.getenv("CASHFREE_SECRET")

# ---------------- CREATE ORDER ----------------
def create_order(user_id, video_id):
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
            "customer_id": str(user_id),
            "customer_phone": "9999999999"
        },
        "order_meta": {
            "return_url": f"https://t.me/YOUR_BOT?start={video_id}"
        }
    }

    res = requests.post(url, json=data, headers=headers).json()
    return res.get("payment_link")

# ---------------- API: GET PAYMENT LINK ----------------
@app.route("/pay", methods=["GET"])
def pay():
    user_id = request.args.get("user_id")
    video_id = request.args.get("video_id")

    link = create_order(user_id, video_id)

    return jsonify({"payment_link": link})

# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    try:
        if data["type"] == "PAYMENT_SUCCESS_WEBHOOK":
            order = data["data"]["order"]

            order_id = order["order_id"]
            user_id, video_id = order_id.split("_")

            send_movie(user_id, video_id)

    except Exception as e:
        print("Error:", e)

    return "OK", 200

# ---------------- SEND MOVIE ----------------
def send_movie(user_id, video_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"

    requests.post(url, data={
        "chat_id": user_id,
        "from_chat_id": CHANNEL_ID,
        "message_id": int(video_id)
    })

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "Cashfree Movie Bot Running 🚀"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
