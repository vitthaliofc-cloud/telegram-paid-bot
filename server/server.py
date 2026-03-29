from flask import Flask, request
import requests, json, os, qrcode
from io import BytesIO

app = Flask(__name__)

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
UPI_ID = os.getenv("UPI_ID")
MERCHANT_NAME = "MovieBot"

MOVIE_FILE = "movies.json"

# ===== LOAD =====
def load_movies():
    if not os.path.exists(MOVIE_FILE):
        return {}
    with open(MOVIE_FILE) as f:
        return json.load(f)

def save_movies(data):
    with open(MOVIE_FILE, "w") as f:
        json.dump(data, f)

movie_map = load_movies()
pending_users = {}

# ===== TELEGRAM =====
def send_message(chat_id, text, keyboard=None):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard
    })

def send_qr(chat_id, amount, movie_id):
    upi_link = f"upi://pay?pa={UPI_ID}&pn={MERCHANT_NAME}&am={amount}&cu=INR"

    qr = qrcode.make(upi_link)
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    files = {"photo": bio}
    data = {
        "chat_id": chat_id,
        "caption": f"""🎬 Movie ID: {movie_id}

💰 Pay ₹{amount}
UPI: {UPI_ID}

📸 Payment केल्यानंतर screenshot पाठवा"""
    }

    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data=data, files=files)

def send_movie(user_id, msg_id):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage", json={
        "chat_id": user_id,
        "from_chat_id": CHANNEL_ID,
        "message_id": msg_id
    })

# ===== HOME =====
@app.route("/", methods=["GET"])
def home():
    return "Bot Running ✅"

# ===== WEBHOOK =====
@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return "ok"

        # ===== MESSAGE =====
        if "message" in data:
            msg = data["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")

            # ===== AUTO MAPPING =====
            if chat_id == ADMIN_ID and "forward_from_chat" in msg:
                if msg["forward_from_chat"]["id"] == CHANNEL_ID:
                    msg_id = msg["forward_from_message_id"]

                    movie_id = str(len(movie_map) + 101)  # auto id
                    movie_map[movie_id] = msg_id
                    save_movies(movie_map)

                    send_message(chat_id, f"✅ Movie Added ID: {movie_id}")

            # ===== START =====
            if text.startswith("/start"):
                parts = text.split()
                if len(parts) > 1:
                    movie_id = parts[1]

                    if movie_id in movie_map:
                        pending_users[chat_id] = movie_id
                        send_qr(chat_id, 30, movie_id)
                    else:
                        send_message(chat_id, "❌ Movie not found")
                else:
                    send_message(chat_id, "Send: /start 101")

            # ===== SCREENSHOT =====
            if "photo" in msg:
                user_id = chat_id
                movie_id = pending_users.get(user_id)

                if not movie_id:
                    return "ok"

                msg_id = movie_map.get(movie_id)

                keyboard = {
                    "inline_keyboard": [[
                        {"text": "✅ Verify", "callback_data": f"ok_{user_id}_{msg_id}"},
                        {"text": "❌ Reject", "callback_data": f"no_{user_id}"}
                    ]]
                }

                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", json={
                    "chat_id": ADMIN_ID,
                    "photo": msg["photo"][-1]["file_id"],
                    "caption": f"User: {user_id}\nMovie ID: {movie_id}",
                    "reply_markup": keyboard
                })

                send_message(user_id, "⏳ Waiting for admin approval...")

        # ===== BUTTON =====
        if "callback_query" in data:
            query = data["callback_query"]
            data_val = query["data"]

            if data_val.startswith("ok_"):
                _, uid, msg_id = data_val.split("_")
                send_movie(int(uid), int(msg_id))
                send_message(int(uid), "✅ Payment Verified 🎬")

            elif data_val.startswith("no_"):
                uid = int(data_val.split("_")[1])
                send_message(uid, "❌ Payment Rejected")

        return "ok"

    except Exception as e:
        print("ERROR:", str(e))
        return "ok"

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
