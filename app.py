from flask import Flask, request
import requests, json, sys, os


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
        # Verificación del webhook
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verificado correctamente", file=sys.stdout)
            sys.stdout.flush()
            return challenge, 200
        return "Error de verificación", 403

    if request.method == "POST":
        # Recepción de mensajes
        data = request.get_json()
        print("📩 Mensaje recibido:", json.dumps(data, indent=2), file=sys.stdout)
        sys.stdout.flush()

        try:
            entry = data["entry"][0]["changes"][0]["value"]
            if "messages" in entry:
                phone_number_id = entry["metadata"]["phone_number_id"]
                from_number = entry["messages"][0]["from"]
                text = entry["messages"][0].get("text", {}).get("body", "")

                # 🟢 Enviar respuesta automática
                send_whatsapp_message(
                    from_number, "¡Hola! Tu mensaje fue recibido correctamente 👋"
                )
        except Exception as e:
            print("⚠️ Error procesando mensaje:", e, file=sys.stdout)
            sys.stdout.flush()

        return "EVENT_RECEIVED", 200


def send_whatsapp_message(to_number, text):
    """Envía un mensaje de texto a través de la API de WhatsApp"""
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Respuesta enviada:", response.text, file=sys.stdout)
    sys.stdout.flush()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
