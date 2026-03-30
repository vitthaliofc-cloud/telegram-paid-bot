from flask import Flask, request
import requests
import qrcode
import io
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 1206664080
CHANNEL_ID = -100XXXXXXXXXX  # तुझा private channel id
UPI_ID = "mp0089@ybl"

# ---------------- HELPERS ----------------
def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

def send_qr(chat_id, upi_id, amount=1):
    """Generate UPI QR and send to user"""
    upi_text = f"upi://pay?pa={upi_id}&pn=Movie+Payment&am={amount}&cu=INR"
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(upi_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"photo": ("qr.png", buf, "image/png")}
    data = {"chat_id": chat_id, "caption": f"💰 Scan QR to pay ₹{amount}"}
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data=data, files=files)

def forward_movie(user_id, movie_id):
    """Forward movie from channel based on message_id = movie_id"""
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
        json={
            "chat_id": user_id,
            "from_chat_id": CHANNEL_ID,
            "message_id": int(movie_id)
        }
    )

# ---------------- WEBHOOK ----------------
pending_users = {}  # user_id: movie_id

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    try:
        # ---------- MESSAGE ----------
        if "message" in data:
            msg = data["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text")

            # ADMIN ADD (optional)
            # YOUR OWN ADMIN COMMANDS HERE

            # USER START COMMAND
            if text and text.startswith("/start"):
                parts = text.split()
                movie_id = parts[1] if len(parts) > 1 else None

                if movie_id:
                    pending_users[chat_id] = movie_id
                    send_qr(chat_id, UPI_ID, amount=1)  # ₹1 demo
                else:
                    send_message(chat_id, "❌ Use: /start <movie_id>")

            # SCREENSHOT / PAYMENT IMAGE
            if "photo" in msg:
                movie_id = pending_users.get(chat_id)
                if movie_id:
                    keyboard = {
                        "inline_keyboard": [[
                            {"text": "✅ Verify", "callback_data": f"ok_{chat_id}"},
                            {"text": "❌ Reject", "callback_data": f"no_{chat_id}"}
                        ]]
                    }
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                        json={
                            "chat_id": ADMIN_ID,
                            "photo": msg["photo"][-1]["file_id"],
                            "caption": f"User: {chat_id}\nMovie ID: {movie_id}",
                            "reply_markup": keyboard
                        }
                    )

        # ---------- BUTTON CALLBACK ----------
        if "callback_query" in data:
            query = data["callback_query"]
            data_val = query["data"]
            user_id = int(data_val.split("_")[1])
            movie_id = pending_users.get(user_id)

            if data_val.startswith("ok_") and movie_id:
                forward_movie(user_id, movie_id)
                send_message(user_id, "✅ Payment Verified! Movie sent 🎬")
                pending_users.pop(user_id, None)

            elif data_val.startswith("no_") and movie_id:
                send_message(user_id, "❌ Payment Failed / Rejected")
                pending_users.pop(user_id, None)

        return "ok"

    except Exception as e:
        print("ERROR:", e)
        return "ok"

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
