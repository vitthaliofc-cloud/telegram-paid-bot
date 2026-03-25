import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_URL = os.getenv("SERVER_URL")  # Server URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("❌ Video ID missing")
        return

    video_id = context.args[0]

    try:
        res = requests.get(f"{SERVER_URL}/pay?user_id={user_id}&video_id={video_id}", timeout=10)
        res.raise_for_status()
        data = res.json()
        payment_link = data.get("payment_link")

        if not payment_link:
            await update.message.reply_text("⚠️ Payment link not generated")
            return

        await update.message.reply_text(
            f"🎬 Video #{video_id}\n💰 Price: ₹10\n👉 Pay here:\n{payment_link}"
        )

    except Exception as e:
        print("Payment server error:", e)
        await update.message.reply_text("⚠️ Payment server error, try later")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("🤖 Bot running…")
app.run_polling()
