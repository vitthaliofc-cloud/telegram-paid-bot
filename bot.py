import telebot
from flask import Flask, request
import os
import qrcode
from io import BytesIO

# 🔐 CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

ADMIN_ID = 1206664080  # 🔥 तुझा admin ID

# -------- START COMMAND (QR SEND) --------
@bot.message_handler(commands=['start'])
def start(message):
    try:
        movie_id = message.text.split()[1]
    except:
        bot.reply_to(message, "❌ Invalid link")
        return

    price = 10
    upi_id = "mp0089@ybl"

    # UPI Link
    upi_link = f"upi://pay?pa={upi_id}&pn=MovieBot&am={price}&cu=INR"

    # QR Generate
    qr = qrcode.make(upi_link)
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    caption = f"""🎬 Movie ID: {movie_id}

💰 Price: ₹{price}

👉 UPI: {upi_id}

QR scan करून payment करा 📲

Payment केल्यावर:
📸 Screenshot पाठवा
किंवा
🧾 UTR ID पाठवा
"""

    bot.send_photo(message.chat.id, bio, caption=caption)


# -------- HANDLE SCREENSHOT --------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Admin ला forward
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

    # User ला reply
    bot.reply_to(message, "✅ Screenshot received! Please wait for verification.")


# -------- HANDLE UTR / TEXT --------
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith("/start"):
        return

    # Admin ला send
    bot.send_message(
        ADMIN_ID,
        f"🧾 New UTR / Message\n\n👤 User ID: {message.chat.id}\n\n{message.text}"
    )

    # User ला reply
    bot.reply_to(message, "✅ Details received! Please wait for verification.")


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
