import os
import qrcode
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes, CallbackQueryHandler, MessageHandler, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
UPI_ID = "mp0089@ybl"

# user_id -> {"video_id": str, "utr": str}
pending_approvals = {}
waiting_for_utr = {}  # user_id -> video_id

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ifimport requests

SERVER = "https://yourproject.up.railway.app"  # Railway URL

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

# ---------------- BUTTON CLICK ----------------
async def paid_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    video_id = query.data.split("_")[1]

    waiting_for_utr[user_id] = video_id

    await query.message.reply_text(
        "📌 कृपया तुमचा UTR / TXN ID पाठवा\n\n"
        "Example: 123456789"
    )

# ---------------- RECEIVE UTR ----------------
async def receive_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in waiting_for_utr:
        return

    video_id = waiting_for_utr[user_id]

    pending_approvals[user_id] = {
        "video_id": video_id,
        "utr": text
    }

    del waiting_for_utr[user_id]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💰 New Payment Request\n\n"
            f"👤 User: {user_id}\n"
            f"🎬 Video: {video_id}\n"
            f"🧾 UTR: {text}\n\n"
            f"Approve: /approve {user_id}"
        )
    )

    await update.message.reply_text("✅ Request sent. Waiting for approval.")

# ---------------- APPROVE ----------------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 1:
        await update.message.reply_text("❌ Use: /approve USER_ID")
        return

    user_id = int(context.args[0])

    if user_id not in pending_approvals:
        await update.message.reply_text("❌ No request found")
        return

    video_id = pending_approvals[user_id]["video_id"]

    try:
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=CHANNEL_ID,
            message_id=int(video_id)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return

    del pending_approvals[user_id]

    await context.bot.send_message(
        chat_id=user_id,
        text="🎉 Payment verified! Video delivered."
    )

    await update.message.reply_text("✅ Approved & sent")

# ---------------- BOT SETUP ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(paid_button, pattern="^paid_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_utr))
app.add_handler(CommandHandler("approve", approve))

print("🤖 UTR Verification Bot Running...")
app.run_polling()
