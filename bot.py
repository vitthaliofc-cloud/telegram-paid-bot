import telebot
from flask import Flask, request
import os
import qrcode
from io import BytesIO

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))  # तुझा Telegram ID
UPI_ID = os.environ.get("UPI_ID")
CHANNEL_ID = os.environ.get("CHANNEL_ID")  # -100xxxx format

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

pending = {}  # user_id: movie_id

# -------- START --------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    parts = message.text.split()

    if len(parts) == 2:
        movie_id = parts[1]
        pending[user_id] = movie_id

        # QR generate
        qr = qrcode.make(f"upi://pay?pa={UPI_ID}&pn=Movie&am=50&cu=INR")
        bio = BytesIO()
        bio.name = "qr.png"
        qr.save(bio, "PNG")
        bio.seek(0)

        caption = f"""
🎬 Movie ID: {movie_id}

💰 Amount: ₹50
📲 UPI ID: {UPI_ID}

👉 Pay & send screenshot here
"""

        bot.send_photo(user_id, bio, caption=caption)

    else:
        bot.reply_to(message, "Use: /start <movie_id>")

# -------- SCREENSHOT --------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id

    if user_id in pending:
        movie_id = pending[user_id]

        # Forward to admin
        bot.forward_message(ADMIN_ID, user_id, message.message_id)

        bot.send_message(
            ADMIN_ID,
            f"User ID: {user_id}\nMovie ID: {movie_id}\n\nReply: ok {user_id} OR no {user_id}"
        )

        bot.reply_to(message, "✅ Screenshot sent for verification")

# -------- ADMIN VERIFY --------
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID)
def admin_verify(message):
    text = message.text.lower().split()

    if len(text) == 2:
        action, user_id = text
        user_id = int(user_id)

        if user_id in pending:
            movie_id = pending[user_id]

            if action == "ok":
                # SEND MOVIE
                bot.copy_message(user_id, CHANNEL_ID, int(movie_id))
                bot.send_message(user_id, "✅ Payment verified! Movie sent 🎬")

                del pending[user_id]

            elif action == "no":
                bot.send_message(user_id, "❌ Payment rejected")
                del pending[user_id]

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
