import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# store user requests
pending_users = {}

@app.route("/")
def home():
    return "Bot Running 🚀"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json()

    # ================= USER MESSAGE =================
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # START COMMAND
        if text.startswith("/start"):
            parts = text.split()
            movie_id = parts[1] if len(parts) > 1 else "1"

            pending_users[chat_id] = movie_id

            send_message(chat_id,
                f"🎬 Movie ID: {movie_id}\n💰 Price: ₹10\n\n"
                f"👉 UPI: yourupi@upi\n"
                f"👉 QR scan करा\n\n"
                f"Payment केल्यावर:\n"
                f"📸 Screenshot पाठवा\n"
                f"किंवा\n"
                f"🧾 UTR ID पाठवा"
            )

        # SCREENSHOT
        if "photo" in data["message"]:
            file_id = data["message"]["photo"][-1]["file_id"]
            movie_id = pending_users.get(chat_id, "1")

            send_to_admin(chat_id, movie_id, file_id, "photo")

            send_message(chat_id, "⏳ Verification चालू आहे...")

        # UTR / TEXT
        elif text and not text.startswith("/"):
            movie_id = pending_users.get(chat_id, "1")

            send_to_admin(chat_id, movie_id, text, "text")

            send_message(chat_id, "⏳ Verification चालू आहे...")

    # ================= BUTTON HANDLER =================
    if "callback_query" in data:
        query = data["callback_query"]
        data_btn = query["data"]
        admin_chat = query["message"]["chat"]["id"]

        if admin_chat == ADMIN_ID:
            action, user_id, movie_id = data_btn.split("|")
            user_id = int(user_id)

            if action == "verify":
                send_movie(user_id, movie_id)
            else:
                send_message(user_id, "❌ Payment Not Verified")

    return "ok"


# ================= SEND TO ADMIN =================
def send_to_admin(user_id, movie_id, content, type_):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Verified", "callback_data": f"verify|{user_id}|{movie_id}"},
            {"text": "❌ Reject", "callback_data": f"reject|{user_id}|{movie_id}"}
        ]]
    }

    caption = f"User: {user_id}\nMovie: {movie_id}"

    if type_ == "photo":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        requests.post(url, json={
            "chat_id": ADMIN_ID,
            "photo": content,
            "caption": caption,
            "reply_markup": keyboard
        })
    else:
        requests.post(url, json={
            "chat_id": ADMIN_ID,
            "text": f"{caption}\nUTR: {content}",
            "reply_markup": keyboard
        })


# ================= SEND MOVIE =================
def send_movie(user_id, movie_id):
    movie_links = {
        "1": "https://example.com/movie1.mp4",
        "5": "https://example.com/movie5.mp4"
    }

    link = movie_links.get(movie_id, "https://example.com/default.mp4")

    send_message(user_id, f"✅ Payment Verified!\n🎬 Movie Link:\n{link}")


# ================= TELEGRAM SEND =================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
