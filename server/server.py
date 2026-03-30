from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789   # Admin Telegram ID
CHANNEL_ID = -100XXXXXXXXXX  # Your private channel ID
UPI_ID = "mp0089@ybl"

pending_users = {}  # user_id -> movie_id

# ---------------- TELEGRAM ----------------
def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def send_payment(chat_id, movie_id):
    text = f"""
🎬 Movie ID: {movie_id}
💰 Payment करा

UPI: {UPI_ID}

📸 Payment केल्यानंतर screenshot पाठवा
"""
    send_message(chat_id, text)

def send_movie(user_id, movie_id):
    try:
        # Direct copy from channel using movie_id
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
            json={
                "chat_id": user_id,
                "from_chat_id": CHANNEL_ID,
                "message_id": int(movie_id)
            }
        )
    except:
        send_message(user_id, "❌ Movie not found or invalid ID")

# ---------------- WEBHOOK ----------------
@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # ADMIN ADD
        if chat_id == ADMIN_ID and text:
            send_message(chat_id, f"Admin Msg: {text}")
            return "ok"

        # USER START
        if text.startswith("/start"):
            parts = text.split()
            if len(parts) > 1:
                movie_id = parts[1]
                pending_users[chat_id] = movie_id
                send_payment(chat_id, movie_id)
            else:
                send_message(chat_id, "Use: /start <movie_id>")

        # PAYMENT SCREENSHOT
        if "photo" in msg:
            user_id = chat_id
            movie_id = pending_users.get(user_id)
            if movie_id:
                # Send to admin for verification
                keyboard = {
                    "inline_keyboard": [[
                        {"text": "✅ Verify", "callback_data": f"ok_{user_id}"},
                        {"text": "❌ Reject", "callback_data": f"no_{user_id}"}
                    ]]
                }
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    json={
                        "chat_id": ADMIN_ID,
                        "photo": msg["photo"][-1]["file_id"],
                        "caption": f"User: {user_id}\nMovie: {movie_id}",
                        "reply_markup": keyboard
                    }
                )

    # BUTTON CALLBACK
    if "callback_query" in data:
        query = data["callback_query"]
        data_val = query["data"]
        if data_val.startswith("ok_"):
            user_id = int(data_val.split("_")[1])
            movie_id = pending_users.get(user_id)
            send_movie(user_id, movie_id)
            send_message(user_id, "✅ Payment Verified")
        elif data_val.startswith("no_"):
            user_id = int(data_val.split("_")[1])
            send_message(user_id, "❌ Payment Failed")

    return "ok"

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
