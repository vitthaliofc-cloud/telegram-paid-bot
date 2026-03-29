from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

# 🔑 CONFIG
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 1206664080   # 👉 तुझा Telegram ID टाक
CHANNEL_ID = -1003786486534
UPI_ID = "mp0089@ybl"

MOVIE_FILE = "movies.json"

# ---------------- MOVIE DB ----------------

def load_movies():
    if not os.path.exists(MOVIE_FILE):
        return {}
    with open(MOVIE_FILE, "r") as f:
        return json.load(f)

def save_movies(data):
    with open(MOVIE_FILE, "w") as f:
        json.dump(data, f)

movie_map = load_movies()
pending_users = {}

# ---------------- TELEGRAM ----------------

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    res = requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })

    print("📤 SEND MSG RESPONSE:", res.text)

def send_payment(chat_id):
    text = f"💰 Pay ₹10\nUPI: {UPI_ID}\n\n📸 Payment screenshot पाठवा"
    send_message(chat_id, text)

def send_movie(user_id, movie_input):

    msg_id = None

    # 🎬 ID SYSTEM
    if str(movie_input).isdigit():
        msg_id = int(movie_input)

    # 🎬 NAME SYSTEM
    else:
        msg_id = movie_map.get(str(movie_input).lower())

    if msg_id:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"

        requests.post(url, json={
            "chat_id": user_id,
            "from_chat_id": CHANNEL_ID,
            "message_id": msg_id
        })
    else:
        send_message(user_id, "❌ Movie not found")

# ---------------- WEBHOOK ----------------

@app.route("/", methods=["POST"])
def webhook():
    data = request.json

    print("🔥 FULL DATA:", data)

    # ---------- MESSAGE ----------
    if "message" in data:
    msg = data["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text")

    print("🔥 TEXT:", text)
    print("🔥 CHAT:", chat_id)

    # ---------------- ADMIN COMMANDS ----------------
    if chat_id == ADMIN_ID and text:

        if text.startswith("/add"):
            try:
                _, name, msg_id = text.split()
                movie_map[name.lower()] = int(msg_id)
                save_movies(movie_map)
                send_message(chat_id, f"✅ Added {name}")
            except:
                send_message(chat_id, "❌ Use: /add name id")

        elif text.startswith("/delete"):
            try:
                _, name = text.split()
                movie_map.pop(name.lower(), None)
                save_movies(movie_map)
                send_message(chat_id, f"🗑 Deleted {name}")
            except:
                send_message(chat_id, "❌ Use: /delete name")

        elif text == "/list":
            if movie_map:
                msg_text = "\n".join([f"{k} → {v}" for k,v in movie_map.items()])
                send_message(chat_id, msg_text)
            else:
                send_message(chat_id, "❌ No movies")

    # ---------------- USER COMMANDS ----------------
    if text:

        if text.startswith("/start"):
            parts = text.split()
            movie_input = parts[1] if len(parts) > 1 else ""

            pending_users[chat_id] = movie_input
            print("🔥 Sending payment...")
            send_payment(chat_id)

        elif not text.startswith("/"):
            pending_users[chat_id] = text.lower()
            send_payment(chat_id)

    # ---------- SCREENSHOT ----------
    if "message" in data and "photo" in data["message"]:
        msg = data["message"]
        user_id = msg["chat"]["id"]

        movie_input = pending_users.get(user_id)

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Verified", "callback_data": f"ok_{user_id}"},
                {"text": "❌ Reject", "callback_data": f"no_{user_id}"}
            ]]
        }

        requests.post(url, json={
            "chat_id": ADMIN_ID,
            "photo": msg["photo"][-1]["file_id"],
            "caption": f"User: {user_id}\nMovie: {movie_input}",
            "reply_markup": keyboard
        })

    # ---------- BUTTON ----------
    if "callback_query" in data:
        query = data["callback_query"]
        data_val = query["data"]

        if data_val.startswith("ok_"):
            user_id = int(data_val.split("_")[1])
            movie_input = pending_users.get(user_id)

            send_movie(user_id, movie_input)
            send_message(user_id, "✅ Payment Verified")

        elif data_val.startswith("no_"):
            user_id = int(data_val.split("_")[1])
            send_message(user_id, "❌ Payment Failed")

    return "ok"

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
