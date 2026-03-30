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
import qrcode
from io import BytesIO

@bot.message_handler(commands=['start'])
def start(message):
    try:
        movie_id = message.text.split()[1]
    except:
        bot.reply_to(message, "Invalid link ❌")
        return

    price = 10  # 🔥 Fixed price for all movies
    upi_id = "mp0089@ybl"

    # UPI Payment Link
    upi_link = f"upi://pay?pa={upi_id}&pn=MovieBot&am={price}&cu=INR"

    # QR Generate
    qr = qrcode.make(upi_link)
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    # Message
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
