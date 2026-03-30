import telebot
from flask import Flask, request
import qrcode
from io import BytesIO

# -------------------- CONFIG --------------------
BOT_TOKEN = "YOUR_BOT_TOKEN"        # Telegram Bot Token
ADMIN_ID = 123456789                # Your Telegram ID (for admin verification)
UPI_ID = "yourupi@bank"             # Your UPI ID
MOVIE_CHANNEL = "@YourChannelName"  # Channel where movies are posted

# -------------------- INIT --------------------
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# In-memory user tracking (can use DB)
pending_payments = {}  # {user_id: movie_id}

# -------------------- /start handler --------------------
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    user_id = message.from_user.id

    if len(args) == 2:
        movie_id = args[1]
        pending_payments[user_id] = movie_id

        # Generate QR code
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(f"upi://pay?pa={UPI_ID}&pn=Movie+Payment&tn=MovieID{movie_id}&am=50")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        bio = BytesIO()
        bio.name = 'qr.png'
        img.save(bio, 'PNG')
        bio.seek(0)

        # Payment instructions
        text = f"🎬 Movie ID: {movie_id}\n💰 Amount: ₹50\n\n" \
               f"Scan the QR code or pay via UPI ID: {UPI_ID}\n" \
               f"After payment, send screenshot here for verification."

        bot.send_photo(user_id, bio, caption=text)
    else:
        bot.send_message(user_id, "Welcome! Use /start <movie_id> to pay and get the movie.")

# -------------------- Screenshot handler --------------------
@bot.message_handler(content_types=['photo'])
def payment_screenshot(message):
    user_id = message.from_user.id
    if user_id in pending_payments:
        movie_id = pending_payments[user_id]

        # Forward to admin
        bot.forward_message(ADMIN_ID, user_id, message.message_id)
        bot.send_message(ADMIN_ID, f"Verify payment for Movie ID {movie_id} from {message.from_user.first_name} (@{message.from_user.username})")

        bot.send_message(user_id, "✅ Screenshot received! Admin will verify shortly.")
    else:
        bot.send_message(user_id, "Please start with /start <movie_id> first.")

# -------------------- Admin confirm handler --------------------
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID)
def admin_reply(message):
    text = message.text.lower()
    if text.startswith("send "):
        parts = text.split()
        if len(parts) == 2:
            user_id = int(parts[1])
            if user_id in pending_payments:
                movie_id = pending_payments.pop(user_id)
                bot.send_message(user_id, f"🎬 Payment verified! Here is your movie: {MOVIE_CHANNEL}/{movie_id}")
                bot.send_message(ADMIN_ID, f"✅ Movie ID {movie_id} sent to user {user_id}")
            else:
                bot.send_message(ADMIN_ID, "User not found in pending payments.")

# -------------------- Flask Webhook --------------------
@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    if data:
        bot.process_new_updates([telebot.types.Update.de_json(data)])
    return "OK", 200

# -------------------- Run Flask --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
