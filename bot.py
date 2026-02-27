import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Must be -100XXXXXXXXXX
UPI_ID = os.getenv("UPI_ID")

# In-memory storage for approvals
approved_videos = {}  # user_id -> set(video_ids)

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check if video ID is provided
    if not context.args:
        await update.message.reply_text("❌ Video ID missing")
        return

    video_id = context.args[0]  # Keep as string

    # Check if user has approved access
    if user_id not in approved_videos or video_id not in approved_videos[user_id]:
        # Payment message
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

    # Send only approved video
    try:
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_ID,
            message_id=int(video_id)  # Telegram message_id must be int
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Video send failed: {e}")

# ---------------- PAID COMMAND ----------------
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: /paid VIDEO_ID TXN_ID")
        return

    user_id = update.effective_user.id
    video_id = context.args[0]
    txn_id = context.args[1]

    # Send payment request to admin
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💰 New Payment Request\n\n"
            f"👤 User ID: {user_id}\n"
            f"🎥 Video ID: {video_id}\n"
            f"💵 Amount: ₹10\n"
            f"🧾 TXN: {txn_id}"
        )
    )
    await update.message.reply_text("✅ Request sent. Approval pending.")

# ---------------- APPROVE COMMAND ----------------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: /approve USER_ID VIDEO_ID")
        return

    user_id = int(context.args[0])
    video_id = context.args[1]

    # Approve only this video for this user
    approved_videos.setdefault(user_id, set()).add(video_id)

    # Notify user
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 Payment confirmed!\n\n👉 Video मिळवण्यासाठी /start {video_id} पाठवा"
    )

    # Notify admin
    await update.message.reply_text(
        f"✅ Approved user {user_id} for video {video_id}"
    )

# ---------------- BOT SETUP ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CommandHandler("approve", approve))

print("🤖 Bot is running...")
app.run_polling()
