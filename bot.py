import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
UPI_ID = os.getenv("UPI_ID")

# in-memory storage (simple)
approved_videos = {}  # user_id -> set(video_ids)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("❌ Video ID missing")
        return

    video_id = context.args[0]

    if user_id not in approved_videos or video_id not in approved_videos[user_id]:
        await update.message.reply_text(
            "🔒 Paid Video\n\n"
            "🎥 Price: ₹10 per video\n\n"
            f"💳 Pay ₹10 via UPI\n"
            f"📌 UPI ID: {UPI_ID}\n\n"
            "Payment नंतर असा message पाठवा:\n"
            f"`/paid {video_id} TXN_ID`",
            parse_mode="Markdown"
        )
        return

    await context.bot.copy_message(
        chat_id=update.effective_chat.id,
        from_chat_id=CHANNEL_ID,
        message_id=video_id
    )

async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: /paid VIDEO_ID TXN_ID")
        return

    user_id = update.effective_user.id
    video_id = context.args[0]
    txn = context.args[1]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💰 New Payment Request\n\n"
            f"👤 User ID: {user_id}\n"
            f"🎥 Video ID: {video_id}\n"
            f"💵 Amount: ₹10\n"
            f"🧾 TXN: {txn}"
        )
    )
    await update.message.reply_text("✅ Request sent. Approval pending.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: /approve USER_ID VIDEO_ID")
        return

    user_id = int(context.args[0])
    video_id = context.args[1]

    approved_videos.setdefault(user_id, set()).add(video_id)

    await update.message.reply_text(
        f"✅ Approved user {user_id} for video {video_id}"
    )
    await context.bot.send_message(
        chat_id=user_id,
        text="🎉 Payment confirmed! Video unlocked."
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CommandHandler("approve", approve))

print("🤖 Bot is running...")
app.run_polling()
