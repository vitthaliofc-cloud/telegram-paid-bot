import telebot
from telebot import types
from flask import Flask, request
import os
import qrcode
from io import BytesIO

# 🔐 CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

ADMIN_ID = 1206664080

# 🔥 Private Channel ID (IMPORTANT)
CHANNEL_ID = -1001234567890  # 👉 इथे तुझा real channel id टाक

# 🧠 Temporary Memory DB
user_data = {}

# 🎬 Movie mapping (movie_id → message_id)
movie_map = {
    "29": 45,
    "31": 46,
    "32": 47
}

# -------- START (QR SEND) --------
@bot.message_handler(commands=['start'])
def start(message):
    try:
        movie_id = message.text.split()[1]
    except:
        bot.reply_to(message, "❌ Invalid link")
        return

    price = 10
    upi_id = "mp0089@ybl"

    # Save user data
    user_data[message.chat.id] = {"movie_id": movie_id}

    # UPI link
    upi_link = f"upi://pay?pa={upi_id}&pn=MovieBot&am={price}&cu=INR"

    # Generate QR
    qr = qrcode.make(upi_link)
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    caption = f"""🎬 Movie ID: {movie_id}

💰 Price: ₹10

👉 UPI: {upi_id}

QR scan करून payment करा 📲

Payment केल्यावर:
📸 Screenshot पाठवा
किंवा
🧾 UTR ID पाठवा

━━━━━━━━━━━━━━━
📞 Contact us: @Owner_Of_Groups
"""

    bot.send_photo(message.chat.id, bio, caption=caption)

# -------- HANDLE SCREENSHOT --------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    movie_id = user_data.get(user_id, {}).get("movie_id", "Unknown")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"📸 Payment Screenshot\n\n👤 User: {user_id}\n🎬 Movie: {movie_id}",
        reply_markup=markup
    )

    bot.reply_to(message, "✅ Screenshot received! Waiting for approval.")

# -------- HANDLE UTR --------
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith("/start"):
        return

    user_id = message.chat.id
    movie_id = user_data.get(user_id, {}).get("movie_id", "Unknown")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    bot.send_message(
        ADMIN_ID,
        f"🧾 UTR Received\n\n👤 User: {user_id}\n🎬 Movie: {movie_id}\n\n{message.text}",
        reply_markup=markup
    )

    bot.reply_to(message, "✅ Details received! Waiting for approval.")

# -------- APPROVE / REJECT --------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data

    if data.startswith("approve_"):
        user_id = int(data.split("_")[1])

        movie_id = user_data.get(user_id, {}).get("movie_id")
        message_id = movie_map.get(movie_id)

        if message_id:
            try:
                bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=CHANNEL_ID,  # 🔥 private channel id
                    message_id=message_id
                )

                bot.send_message(user_id, "🎉 Payment Approved! Enjoy your movie 🎬")

            except Exception as e:
                bot.send_message(user_id, "⚠️ Error sending movie. Please contact admin.")
                print(e)
        else:
            bot.send_message(user_id, "❌ Movie not found!")

        bot.answer_callback_query(call.id, "Approved ✅")

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])

        bot.send_message(
            user_id,
            "❌ Payment Rejected.\n\nContact: @Owner_Of_Groups"
        )

        bot.answer_callback_query(call.id, "Rejected ❌")

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
