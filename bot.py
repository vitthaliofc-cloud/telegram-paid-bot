import os
import qrcode
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # -100XXXXXXXXXX
UPI_ID = "mp0089@ybl"  # Fixed UPI ID

# Keep track of pending approvals
pending_approvals = {}  # user_id -> set(video_ids)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Video ID missing")
        return

    video_id = context.args[0]

    # Generate UPI QR code
    upi_link = f"upi://pay?pa={UPI_ID}&pn=Mangesh%20Kamble&am=10&cu=INR"
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    bio = BytesIO()
    bio.name = "upi_qr.png"
    img.save(bio, format="PNG")
    bio.seek(0)

    caption_text = (
    "🔒 Paid Video\n\n"
    "🎥 Price: ₹10 per video\n"
    f"💳 Pay via UPI: {UPI_ID}\n\n"

    "📌 Payment करने के बाद क्या करना है?\n\n"
    "1️⃣ UPI से ₹10 payment करें\n"
    "2️⃣ Payment complete होने के बाद\n"
    "3️⃣ इसी chat में नीचे दिया हुआ message भेजें 👇\n\n"
    f"👉 /paid {video_id} TXN_ID\n\n"

    "🧾 TXN_ID क्या होता है?\n"
    "• Payment करने के बाद आपको जो\n"
    "  Transaction / Reference / UTR नंबर मिलता है\n"
    "  वही TXN_ID होता है\n\n"

    "📌 Example:\n"
    "अगर आपका Transaction ID = 456789123\n"
    "तो message ऐसे भेजें:\n\n"
    f"👉 /paid {video_id} 456789123\n\n"

    "⏳ उसके बाद:\n"
    "• आपका payment verify हो जाएगा.\n"
    "• Approval मिलने के बाद video भेजा जाएगा.\n"
    "• Video केवल एक बार ही मिलेगा\n"
    "• दोबारा देखने के लिए फिर से payment करना होगा\n\n"
    "🙏 धन्यवाद!"
    )
    await update.message.reply_photo(
        photo=bio,
        caption=caption_text
    )

# ---------------- PAID ----------------
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: /paid VIDEO_ID TXN_ID")
        return

    user_id = update.effective_user.id
    video_id = context.args[0]
    txn_id = context.args[1]

    pending_approvals.setdefault(user_id, set()).add(video_id)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"💰 New Payment Request\n\n"
            f"👤 User ID: {user_id}\n"
            f"🎥 Video ID: {video_id}\n"
            f"💵 Amount: ₹10\n"
            f"🧾 TXN: {txn_id}"
        )
    )

    await update.message.reply_text("✅ Request sent. Approval pending.")

# ---------------- APPROVE ----------------
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ Use: /approve USER_ID VIDEO_ID")
        return

    user_id = int(context.args[0])
    video_id = context.args[1]

    if user_id not in pending_approvals or video_id not in pending_approvals[user_id]:
        await update.message.reply_text("❌ No pending payment request for this video")
        return

    try:
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=CHANNEL_ID,
            message_id=int(video_id)
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Video send failed: {e}")
        return

    pending_approvals[user_id].remove(video_id)
    if not pending_approvals[user_id]:
        del pending_approvals[user_id]

    await context.bot.send_message(
        chat_id=user_id,
        text="🎉 Payment confirmed! Video delivered.\n\n"
             "⚠️ Note: Video एक ही बार मिलेगा.\n"
             "दोबारा देखने के लिए फिर से payment करना होगा."
    )
    await update.message.reply_text(f"✅ Video sent to user {user_id}")

# ---------------- BOT SETUP ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("paid", paid))
app.add_handler(CommandHandler("approve", approve))

from telegram import Update

print("🤖 QR Payment bot is running...")

app.run_polling(
    allowed_updates=Update.ALL_TYPES,
    drop_pending_updates=True,
    close_loop=False
)
