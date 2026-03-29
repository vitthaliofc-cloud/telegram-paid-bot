from flask import Flask, request

app = Flask(__name__)

# ✅ Health check (important for Railway)
@app.route("/", methods=["GET"])
def home():
    return "Bot Running", 200

# ✅ Webhook
@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("UPDATE:", data)

        return "ok", 200

    except Exception as e:
        print("ERROR:", e)
        return "ok", 200
