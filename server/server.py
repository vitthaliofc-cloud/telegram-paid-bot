from flask import Flask, request
import requests
import os
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)

# 🔑 CONFIG
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 1234567890             # तुमचा Telegram ID
CHANNEL_ID = -1001234567890       # Private channel ID (negative number)
UPI_ID = "mp0089@ybl"

# ---------------- HELPER ----------------
pending_users = {}  # user_id -> movie_id

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=data)

def send_qr(chat_id, movie_id):
    """Generate QR for UPI payment"""
    upi_text = f"upi://pay?pa={UPI_ID}&pn=Movie+Bot&tn=Movie+Payment&am=10&cu=INR"
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(upi_text)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)

    files = {"photo": ("qr.png", bio, "image/png")}
    data = {"chat_id": chat_id, "caption": f"💰 Please pay ₹10 for Movie ID: {movie_id}"}
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data=data, files=files)

def send_movie(user_id, movie_msg_id):
    """Forward movie from private channel"""
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
        json={
            "chat_id": user_id,
            "from_chat_id": CHANNEL_ID,
            "message_id": movie_msg_id
        }
    )

# ---------------- WEBHOOK ----------------
@@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("WEBHOOK RECEIVED:", data)
    ...

    # --------- MESSAGE HANDLER ---------
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # /start <movie_id> flow
        if text.startswith("/start"):
            parts = text.split()
            movie_id = parts[1] if len(parts) > 1 else None
            if movie_id and movie_id.isdigit():
                movie_msg_id = int(movie_id)
                pending_users[chat_id] = movie_msg_id
                send_message(chat_id, f"🎬 You selected Movie ID: {movie_id}")
                send_qr(chat_id, movie_id)
            else:
                send_message(chat_id, "❌ Invalid Movie ID")

        # Photo/screenshot from user
        if "photo" in msg:
            user_id = chat_id
            movie_msg_id = pending_users.get(user_id)
            if movie_msg_id:
                # send to admin with verification buttons
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Verify", "callback_data": f"ok_{user_id}"},
                            {"text": "❌ Reject", "callback_data": f"no_{user_id}"}
                        ]
                    ]
                }
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    json={
                        "chat_id": ADMIN_ID,
                        "photo": msg["photo"][-1]["file_id"],
                        "caption": f"User: {user_id}\nMovie ID: {movie_msg_id}",
                        "reply_markup": keyboard
                    }
                )

    # --------- CALLBACK HANDLER ---------
    if "callback_query" in data:
        query = data["callback_query"]
        user_id = int(query["data"].split("_")[1])
        movie_msg_id = pending_users.get(user_id)

        if query["data"].startswith("ok_"):
            send_movie(user_id, movie_msg_id)
            send_message(user_id, "✅ Payment Verified. Enjoy your movie!")
            pending_users.pop(user_id, None)

        elif query["data"].startswith("no_"):
            send_message(user_id, "❌ Payment Rejected. Try again.")
            pending_users.pop(user_id, None)

    return "ok"

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
