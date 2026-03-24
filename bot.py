import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔥 Railway server URL (IMPORTANT)
SERVER = "https://worker-production-7e26.up.railway.app"

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("❌ Video ID missing")
        return

    video_id = context.args[0]

    try:
        res = requests.get(
            f"{SERVER}/pay?user_id={user_id}&video_id={video_id}"
        ).json()

        payment_link = res["payment_link"]

        await update.message.reply_text(
            f"🎬 Video #{video_id}\n\n"
            "💰 Price: ₹10\n\n"
            f"👉 Pay here:\n{payment_link}"
        )

    except Exception as e:
        await update.message.reply_text("❌ Payment link error, try again")

# ---------------- BOT SETUP ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

print("🤖 Cashfree Auto Bot Running...")
app.run_polling()
