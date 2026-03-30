import telebot
from telebot import types
import os
import qrcode
from io import BytesIO

# 🔐 CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

ADMIN_ID = 1206664080

# 🧠 Memory DB
user_data = {}

# -------- GET MOVIE NAME --------
def get_movie_name(msg_id):
    try:
        msg = bot.forward_message(ADMIN_ID, CHANNEL_ID, msg_id)
        return msg.caption or msg.text or f"Movie #{msg_id}"
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

    price = 10
    upi_id = "mp0089@ybl"

    upi_link = f"upi://pay?pa={upi_id}&pn=MovieBot&am={price}&cu=INR"

    qr = qrcode.make(upi_link)
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    bot.send_photo(
        message.chat.id,
        bio,
        caption=f"""🎬 {movie_name}

💰 Price: ₹10
👉 UPI: {upi_id}

QR scan करून payment करा 📲

Payment केल्यावर:
📸 Screenshot किंवा 🧾 UTR पाठवा

━━━━━━━━━━━━━━━
📞 Contact: @Owner_Of_Groups
"""
    )

# -------- SCREENSHOT --------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id

    data = user_data.get(user_id, {})
    msg_id = data.get("message_id")
    movie_name = data.get("movie_name", "Movie")

    username = message.from_user.username or "NoUsername"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

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

    bot.reply_to(message, "✅ Screenshot received! Waiting for approval.")

# -------- TEXT (UTR) --------
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith("/start"):
        return

    user_id = message.chat.id

    data = user_data.get(user_id, {})
    msg_id = data.get("message_id")
    movie_name = data.get("movie_name", "Movie")

    username = message.from_user.username or "NoUsername"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

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

    bot.reply_to(message, "✅ Details received! Waiting for approval.")

# -------- CALLBACK --------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data

    if data.startswith("approve_"):
        user_id = int(data.split("_")[1])

        user = user_data.get(user_id, {})
        msg_id = user.get("message_id")

        try:
            bot.copy_message(
                chat_id=user_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )

            bot.send_message(user_id, "🎉 Payment Approved! Enjoy your movie 🎬")

        except Exception as e:
            bot.send_message(user_id, "⚠️ Error sending movie")
            print(e)

        bot.answer_callback_query(call.id, "Approved ✅")

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])

        bot.send_message(user_id, "❌ Payment Rejected")

        bot.answer_callback_query(call.id, "Rejected ❌")

# -------- RUN (FAST) --------
if __name__ == "__main__":
    print("🤖 Bot Running Fast...")
    bot.infinity_polling()
