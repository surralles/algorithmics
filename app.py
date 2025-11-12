from flask import Flask, request
import requests, json, sys, os
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "autoclass2025")

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Verificación inicial de Meta
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    if request.method == "POST":
        # Mensajes entrantes desde WhatsApp
        data = request.get_json()
        print("📩 Webhook recibido:", json.dumps(data, indent=2), file=sys.stdout)
        sys.stdout.flush()
        return "EVENT_RECEIVED", 200


if __name__ == "__main__":
    app.run(port=5000)
