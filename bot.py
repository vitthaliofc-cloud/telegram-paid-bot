import telebot
from telebot import types
from flask import Flask, request
import os
import qrcode
from io import BytesIO

# 🔐 CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
app = Flask(__name__)

ADMIN_ID = 1206664080

user_data = {}

# -------- GET MOVIE NAME --------
def get_movie_name(msg_id):
    try:
        msg = bot.forward_message(ADMIN_ID, CHANNEL_ID, msg_id)

        movie_name = msg.caption or msg.text or f"Movie #{msg_id}"

        # 🧹 Auto delete forwarded movie
        bot.delete_message(ADMIN_ID, msg.message_id)

        return movie_name
    except:
        return f"Movie #{msg_id}"
# -------- START --------
@bot.message_handler(commands=['start'])
def start(message):
    try:
        message_id = int(message.text.split()[1])
    except:
        bot.reply_to(message, "❌ Invalid link")
        return

    movie_name = get_movie_name(message_id)

    user_data[message.chat.id] = {
        "message_id": message_id,
        "movie_name": movie_name
    }

    qr = qrcode.make("upi://pay?pa=mp0089@ybl&pn=MovieBot&am=10&cu=INR")
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    bot.send_photo(
        message.chat.id,
        bio,
        caption=f"""🎬 {movie_name}

💰 Price: ₹10

QR scan करून payment करा 📲

📸 Screenshot किंवा 🧾 UTR पाठवा
"""
    )

# -------- PAYMENT --------
def send_to_admin(message, user_id):
    data = user_data.get(user_id, {})
    msg_id = data.get("message_id")
    movie_name = data.get("movie_name", "Movie")
    username = message.from_user.username or "NoUsername"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    if message.content_type == "photo":
        bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"""💰 New Payment Request

👤 User ID: {user_id}
📛 Username: @{username}

🎬 Movie: {movie_name}
🆔 Movie ID: {msg_id}
""",
            reply_markup=markup
        )
    else:
        bot.send_message(
            ADMIN_ID,
            f"""💰 New Payment Request

👤 User ID: {user_id}
📛 Username: @{username}

🎬 Movie: {movie_name}
🆔 Movie ID: {msg_id}

🧾 Details:
{message.text}
""",
            reply_markup=markup
        )

# -------- HANDLERS --------
@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    send_to_admin(message, message.chat.id)
    bot.reply_to(message, "✅ Sent for approval")

@bot.message_handler(func=lambda m: True)
def text_handler(message):
    if message.text.startswith("/start"):
        return
    send_to_admin(message, message.chat.id)
    bot.reply_to(message, "✅ Sent for approval")

# -------- CALLBACK --------
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    data = call.data

    if data.startswith("approve_"):
        user_id = int(data.split("_")[1])
        msg_id = user_data.get(user_id, {}).get("message_id")

        try:
            bot.copy_message(user_id, CHANNEL_ID, msg_id)
            bot.send_message(user_id, "🎉 Approved! Enjoy 🎬")
        except Exception as e:
            bot.send_message(user_id, "⚠️ Error sending movie")
            print(e)

        bot.answer_callback_query(call.id, "Approved ✅")

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        bot.send_message(user_id, "❌ Rejected")
        bot.answer_callback_query(call.id, "Rejected ❌")

# -------- WEBHOOK --------
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# -------- HEALTH CHECK --------
@app.route("/", methods=["GET"])
def home():
    return "Bot Running 🚀", 200

# -------- RUN --------
if __name__ == "__main__":
    print("🚀 Bot running (Webhook Mode)")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
