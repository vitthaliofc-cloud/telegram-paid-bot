import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789  # 👉 तुझा Telegram ID

# temporary store
pending_users = {}

@app.route("/")
def home():
    return "Bot Running 🚀"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # USER START
        if text.startswith("/start"):
            parts = text.split()
            movie_id = parts[1] if len(parts) > 1 else "1"

            pending_users[chat_id] = movie_id

            send_message(chat_id,
                f"🎬 Movie ID: {movie_id}\n💰 Price: ₹10\n\nUPI: yourupi@upi\n\nPayment करून screenshot पाठवा 📸"
            )

        # USER SCREENSHOT
        if "photo" in data["message"]:
            file_id = data["message"]["photo"][-1]["file_id"]
            movie_id = pending_users.get(chat_id, "1")

            # send to admin with buttons
            send_photo_with_buttons(
                ADMIN_ID,
                file_id,
                f"User: {chat_id}\nMovie: {movie_id}",
                chat_id,
                movie_id
            )

            send_message(chat_id, "⏳ Verification चालू आहे...")

    # BUTTON CLICK HANDLER
    if "callback_query" in data:
        query = data["callback_query"]
        data_btn = query["data"]
        admin_chat = query["message"]["chat"]["id"]

        if admin_chat == ADMIN_ID:
            action, user_id, movie_id = data_btn.split("|")
            user_id = int(user_id)

            if action == "verify":
                send_message(user_id, f"✅ Payment Verified!\n🎬 Movie: {movie_id}\nLink: https://your-movie-link.com")
            else:
                send_message(user_id, "❌ Payment Failed / Not Verified")

    return "ok"


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


def send_photo_with_buttons(chat_id, file_id, caption, user_id, movie_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Verified", "callback_data": f"verify|{user_id}|{movie_id}"},
                {"text": "❌ Not Verified", "callback_data": f"reject|{user_id}|{movie_id}"}
            ]
        ]
    }

    requests.post(url, json={
        "chat_id": chat_id,
        "photo": file_id,
        "caption": caption,
        "reply_markup": keyboard
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
