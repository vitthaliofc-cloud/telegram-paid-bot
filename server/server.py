from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "YOUR_NEW_TOKEN"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })

@app.route("/", methods=["GET"])
def home():
    return "Bot Running", 200

@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("UPDATE:", data)

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            # 🔥 SIMPLE REPLY
            if text:
                send_message(chat_id, f"🔥 You said: {text}")

        return "ok", 200

    except Exception as e:
        print("ERROR:", e)
        return "ok", 200
