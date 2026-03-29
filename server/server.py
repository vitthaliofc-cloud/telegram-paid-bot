import json
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = "YOUR_NEW_TOKEN"
ADMIN_ID = 1206664080

movie_map = {}
pending_users = {}

# -----------------------
# LOAD / SAVE MOVIES
# -----------------------
def load_movies():
    global movie_map
    try:
        with open("movies.json", "r") as f:
            movie_map = json.load(f)
    except:
        movie_map = {}

def save_movies(data):
    with open("movies.json", "w") as f:
        json.dump(data, f)

# -----------------------
# TELEGRAM FUNCTIONS
# -----------------------
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_movie(chat_id, msg_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "from_chat_id": chat_id,
        "message_id": msg_id
    })

def send_payment(chat_id):
    send_message(chat_id, "💰 Pay ₹10 to get movie")

# -----------------------
# MAIN WEBHOOK
# -----------------------
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    print("DATA:", data)

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        print("TEXT:", text)

        # ADMIN ADD MOVIE
        if chat_id == ADMIN_ID:
            if text.startswith("/add"):
                try:
                    _, name, msg_id = text.split()
                    movie_map[name.lower()] = int(msg_id)
                    save_movies(movie_map)
                    send_message(chat_id, f"✅ Added {name}")
                except:
                    send_message(chat_id, "❌ Use: /add name id")

        # START COMMAND
        if text.startswith("/start"):
            parts = text.split()

            if len(parts) > 1:
                movie_input = parts[1].lower()

                if movie_input in movie_map:
                    pending_users[chat_id] = movie_input
                    send_payment(chat_id)
                else:
                    send_message(chat_id, "❌ Movie not found")
            else:
                send_message(chat_id, "🎬 Send /start movie_name")

        # NORMAL SEARCH (movie name)
        elif text.lower() in movie_map:
            pending_users[chat_id] = text.lower()
            send_payment(chat_id)

    return "OK"

# -----------------------
# RUN SERVER
# -----------------------
if __name__ == "__main__":
    load_movies()
    app.run(host="0.0.0.0", port=5000)
