from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "8752129214:AAF1me2PL3T6tNQIf6k_LmBD8cIn-iLLTAk"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })
    print("SEND STATUS:", res.text)  # 🔥 IMPORTANT DEBUG

@app.route("/", methods=["GET"])
def home():
    return "Bot Running", 200

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    print("UPDATE:", data)

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        send_message(chat_id, f"Reply: {text}")

    return "ok", 200
