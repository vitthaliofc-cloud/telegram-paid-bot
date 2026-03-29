from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "YOUR_BOT_TOKEN"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    res = requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })
    print(res.text)

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("DATA:", data)

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        # 🔥 FORCE RESPONSE
        send_message(chat_id, "🔥 Bot Working 100%")

    return "ok"

if __name__ == "__main__":
    print("Bot Started...")
