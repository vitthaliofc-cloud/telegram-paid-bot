import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER = os.getenv("SERVER_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("❌ Video ID missing")
        return

    video_id = context.args[0]

    res = requests.get(
        f"{SERVER}/pay?user_id={user_id}&video_id={video_id}"
    ).json()

    payment_link = res["payment_link"]

    await update.message.reply_text(
        f"🎬 Video #{video_id}\n\n"
        f"💰 Pay ₹10:\n{payment_link}"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("🤖 Bot running...")
app.run_polling()
