import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ HOME ROUTE (TEST)
@app.route("/")
def home():
    return "Bot Running 🚀"


# ✅ TELEGRAM WEBHOOK
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json(force=True)

        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")

            if text == "/start":
                send_message(chat_id, "Bot is working ✅")

        return "ok"

    except Exception as e:
        print("Error:", e)
        return "ok"


# ✅ SEND MESSAGE
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })


# ✅ RUN SERVER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Server running on {port}")
    app.run(host="0.0.0.0", port=port)
