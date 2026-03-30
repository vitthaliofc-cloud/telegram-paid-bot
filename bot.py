import telebot
from telebot import types
from flask import Flask, request
import os
import qrcode
from io import BytesIO

# 🔐 CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

ADMIN_ID = 1206664080

# 🧠 Memory
user_data = {}

# -------- START --------
@bot.message_handler(commands=['start'])
def start(message):
    try:
        message_id = int(message.text.split()[1])  # 🔥 direct message_id
    except:
        bot.reply_to(message, "❌ Invalid link")
        return

    user_data[message.chat.id] = {"message_id": message_id}

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
        caption=f"""🎬 Movie Access

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
    msg_id = user_data.get(user_id, {}).get("message_id")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"📸 Payment Screenshot\n\n👤 User: {user_id}\n🎬 MsgID: {msg_id}",
        reply_markup=markup
    )

    bot.reply_to(message, "✅ Screenshot received!")

# -------- TEXT --------
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.startswith("/start"):
        return

    user_id = message.chat.id
    msg_id = user_data.get(user_id, {}).get("message_id")

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    bot.send_message(
        ADMIN_ID,
        f"🧾 Payment Info\n\n👤 User: {user_id}\n🎬 MsgID: {msg_id}\n\n{message.text}",
        reply_markup=markup
    )

# -------- CALLBACK --------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data

    if data.startswith("approve_"):
        user_id = int(data.split("_")[1])

        msg_id = user_data.get(user_id, {}).get("message_id")

        try:
            bot.copy_message(
                chat_id=user_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id  # 🔥 dynamic
            )

            bot.send_message(user_id, "🎉 Payment Approved! Enjoy 🎬")

        except Exception as e:
            bot.send_message(user_id, "⚠️ Error sending movie")
            print(e)

        bot.answer_callback_query(call.id, "Approved ✅")

    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])

        bot.send_message(user_id, "❌ Payment Rejected")

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
