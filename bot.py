import telebot
from flask import Flask, request
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

# -------- START COMMAND --------
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot is working ✅")

# -------- WEBHOOK --------
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# -------- RUN --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
