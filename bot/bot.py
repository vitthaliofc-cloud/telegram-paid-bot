import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔥 तुझा Railway webhook server URL
SERVER = "https://your-server.up.railway.app"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("❌ Video ID missing")
        return

    video_id = context.args[0]

    res = requests.get(
        f"{SERVER}/pay?user_id={user_id}&video_id={video_id}"
    ).json()

    await update.message.reply_text(
        f"🎬 Video #{video_id}\n\n"
        f"💰 Pay ₹10:\n{res['payment_link']}"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("Bot running...")
app.run_polling()
