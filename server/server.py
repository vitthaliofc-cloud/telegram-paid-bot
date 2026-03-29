import os
import requests
import qrcode
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

UPI_ID = "mp0089@ybl"

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

        # START
        if text.startswith("/start"):
            parts = text.split()
            movie_id = parts[1] if len(parts) > 1 else "1"

            pending_users[chat_id] = movie_id

            # generate QR
            qr_path = generate_qr(chat_id)

            send_qr(chat_id, qr_path, movie_id)

        # SCREENSHOT
        if "photo" in data["message"]:
            file_id = data["message"]["photo"][-1]["file_id"]
            movie_id = pending_users.get(chat_id, "1")

            send_to_admin(chat_id, movie_id, file_id, "photo")
            send_message(chat_id, "⏳ Verification चालू आहे...")

        # UTR
        elif text and not text.startswith("/"):
            movie_id = pending_users.get(chat_id, "1")

            send_to_admin(chat_id, movie_id, text, "text")
            send_message(chat_id, "⏳ Verification चालू आहे...")

    # BUTTON
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


# ================= QR GENERATE =================
def generate_qr(chat_id):
    upi_link = f"upi://pay?pa={UPI_ID}&pn=MovieBot&am=10&cu=INR"

    img = qrcode.make(upi_link)
    path = f"/tmp/qr_{chat_id}.png"
    img.save(path)

    return path


# ================= SEND QR =================
def send_qr(chat_id, qr_path, movie_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    caption = (
        f"🎬 Movie ID: {movie_id}\n"
        f"💰 Price: ₹10\n\n"
        f"👉 UPI: {UPI_ID}\n\n"
        f"QR scan करून payment करा 📲\n\n"
        f"Payment केल्यावर:\n"
        f"📸 Screenshot पाठवा\n"
        f"किंवा\n"
        f"🧾 UTR ID पाठवा"
    )

    with open(qr_path, "rb") as photo:
        requests.post(url, files={"photo": photo}, data={
            "chat_id": chat_id,
            "caption": caption
        })


# ================= ADMIN =================
def send_to_admin(user_id, movie_id, content, type_):
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
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": ADMIN_ID,
            "text": f"{caption}\nUTR: {content}",
            "reply_markup": keyboard
        })


# ================= SEND MOVIE =================
def send_movie(user_id, movie_id):

    CHANNEL_ID = -1003786486534  # तुझा channel id

    movie_map = {
        "31": 31,
        "32": 32,
        "33": 33
    }

    msg_id = movie_map.get(movie_id)

    if msg_id:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"

        requests.post(url, json={
            "chat_id": user_id,
            "from_chat_id": CHANNEL_ID,
            "message_id": msg_id
        })
    else:
        send_message(user_id, "❌ Movie not available")


# ================= TELEGRAM =================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
