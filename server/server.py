from flask import Flask, request
import requests, json, os

app = Flask(__name__)

# CONFIG
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
UPI_ID = os.getenv("UPI_ID")

MOVIE_FILE = "movies.json"

# LOAD
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

# TELEGRAM API
def send_message(chat_id, text, reply_markup=None):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "reply_markup": reply_markup
    })

def send_photo(chat_id, file_id, caption="", keyboard=None):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", json={
        "chat_id": chat_id,
        "photo": file_id,
        "caption": caption,
        "reply_markup": keyboard
    })

def send_payment(chat_id, movie_name):
    text = f"""🎬 {movie_name}

💰 Payment करा
UPI: {UPI_ID}

📸 Payment केल्यानंतर screenshot पाठवा"""
    send_message(chat_id, text)

def send_movie(user_id, msg_id):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage", json={
        "chat_id": user_id,
        "from_chat_id": CHANNEL_ID,
        "message_id": msg_id
    })

# WEBHOOK
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print(data)

    # ================= MESSAGE =================
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # ---------- ADMIN ADD ----------
        if chat_id == ADMIN_ID and text.startswith("/add"):
            try:
                # format: /add kgf1 10
                _, name, msg_id = text.split()
                name = name.lower()

                if name not in movie_map:
                    movie_map[name] = []

                movie_map[name].append(int(msg_id))
                save_movies(movie_map)

                send_message(chat_id, f"✅ Added {name}")
            except:
                send_message(chat_id, "❌ Use: /add name msg_id")

        # ---------- USER START ----------
        if text.startswith("/start"):
            send_message(chat_id, "🎬 Send Movie ID or Name")

        # ---------- USER SEARCH ----------
        elif text:
            query = text.lower()

            # FLOW 1: exact match (ID-like)
            if query in movie_map and len(movie_map[query]) == 1:
                msg_id = movie_map[query][0]
                pending_users[chat_id] = msg_id
                send_payment(chat_id, query)

            else:
                # FLOW 2: show buttons
                buttons = []
                for name in movie_map:
                    if query in name:
                        buttons.append([{
                            "text": name,
                            "callback_data": f"select_{name}"
                        }])

                if buttons:
                    send_message(chat_id, "🎬 Select Movie:", {
                        "inline_keyboard": buttons
                    })
                else:
                    send_message(chat_id, "❌ Movie not found")

        # ---------- SCREENSHOT ----------
        if "photo" in msg:
            user_id = chat_id
            msg_id = pending_users.get(user_id)

            keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ Verify", "callback_data": f"ok_{user_id}_{msg_id}"},
                    {"text": "❌ Reject", "callback_data": f"no_{user_id}"}
                ]]
            }

            send_photo(
                ADMIN_ID,
                msg["photo"][-1]["file_id"],
                f"User: {user_id}",
                keyboard
            )

            send_message(user_id, "⏳ Waiting for admin approval...")

    # ================= BUTTON =================
    if "callback_query" in data:
        query = data["callback_query"]
        data_val = query["data"]
        user_id = query["from"]["id"]

        # SELECT MOVIE
        if data_val.startswith("select_"):
            name = data_val.split("_")[1]
            msg_id = movie_map[name][0]

            pending_users[user_id] = msg_id
            send_payment(user_id, name)

        # VERIFY
        elif data_val.startswith("ok_"):
            _, uid, msg_id = data_val.split("_")
            send_movie(int(uid), int(msg_id))
            send_message(int(uid), "✅ Payment Verified 🎬")

        # REJECT
        elif data_val.startswith("no_"):
            uid = int(data_val.split("_")[1])
            send_message(uid, "❌ Payment Rejected")

    return "ok"

# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
