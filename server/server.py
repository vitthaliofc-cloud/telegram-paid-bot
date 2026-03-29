from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

# 🔑 CONFIG
BOT_TOKEN = "8752129214:AAF1me2PL3T6tNQIf6k_LmBD8cIn-iLLTAk"
ADMIN_ID = 1206664080
CHANNEL_ID = -100XXXXXXXXXX   # तुझा private channel id
UPI_ID = "mp0089@ybl"

MOVIE_FILE = "movies.json"

# ---------------- LOAD ----------------
def load_movies():
    try:
        if not os.path.exists(MOVIE_FILE):
            return {}
        with open(MOVIE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_movies(data):
    with open(MOVIE_FILE, "w") as f:
        json.dump(data, f)

movie_map = load_movies()
pending_users = {}

# ---------------- TELEGRAM ----------------
def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def send_payment(chat_id):
    text = f"""💰 Payment करा

UPI: {UPI_ID}

📸 Payment केल्यानंतर screenshot पाठवा"""
    send_message(chat_id, text)

def send_movie(user_id, movie_input):
    msg_id = movie_map.get(movie_input)

    if msg_id:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
            json={
                "chat_id": user_id,
                "from_chat_id": CHANNEL_ID,
                "message_id": msg_id
            }
        )
    else:
        send_message(user_id, "❌ Movie not found")

# ---------------- WEBHOOK ----------------
@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("DATA:", data)

        # ---------- MESSAGE ----------
        if "message" in data:
            msg = data["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text")

            # ADMIN ADD
            if chat_id == ADMIN_ID and text:
                if text.startswith("/add"):
                    try:
                        _, name, msg_id = text.split()
                        movie_map[name.lower()] = int(msg_id)
                        save_movies(movie_map)
                        send_message(chat_id, f"✅ Added {name}")
                    except:
                        send_message(chat_id, "❌ Use: /add name id")

            # USER COMMAND
            if text:
                if text.startswith("/start"):
                    parts = text.split()
                    movie_input = parts[1] if len(parts) > 1 else ""

                    pending_users[chat_id] = movie_input.lower()
                    send_payment(chat_id)

                elif not text.startswith("/"):
                    pending_users[chat_id] = text.lower()
                    send_payment(chat_id)

            # 📸 SCREENSHOT HANDLE
            if "photo" in msg:
                user_id = chat_id
                movie_input = pending_users.get(user_id, "")

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
                        "caption": f"User: {user_id}\nMovie: {movie_input}",
                        "reply_markup": keyboard
                    }
                )

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

    except Exception as e:
        print("ERROR:", e)
        return "ok"

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
