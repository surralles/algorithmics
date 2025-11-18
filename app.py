from flask import Flask, request
import requests, json, sys, os
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "autoclass2025")
DEBUG_DISCORD_WEBHOOK = os.getenv("DEBUG_DISCORD_WEBHOOK")


app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


def send_debug_to_discord(title: str, payload):
    """
    Envía payload (objeto Python o string) a Discord via webhook.
    Si el payload es muy largo, lo envía como archivo adjunto (payload.json).
    title: texto corto que describe el mensaje, p.ej. "Incoming webhook" o "WA response"
    """
    if not DEBUG_DISCORD_WEBHOOK:
        # no hay webhook configurado, nothing to do
        return

    try:
        # Normalizar payload a cadena con indentado
        if isinstance(payload, (dict, list)):
            text = json.dumps(payload, indent=2, ensure_ascii=False)
        else:
            text = str(payload)

        # Discord tiene límite ~2000 chars en content; si es más, envia archivo
        if len(text) <= 1800:
            data = {"content": f"**{title}**\n```json\n{text}\n```"}
            resp = requests.post(DEBUG_DISCORD_WEBHOOK, json=data, timeout=10)
        else:
            # enviar como archivo adjunto para no truncar
            files = {"file": ("payload.json", text.encode("utf-8"), "application/json")}
            # también mandar un pequeño mensaje con título
            params = {
                "payload_json": json.dumps(
                    {"content": f"**{title}** — payload adjunto"}
                )
            }
            resp = requests.post(
                DEBUG_DISCORD_WEBHOOK, data=params, files=files, timeout=15
            )

        # log local para saber si Discord aceptó
        print(
            "📥 Debug -> Discord response:",
            resp.status_code,
            resp.text,
            file=sys.stdout,
        )
        sys.stdout.flush()
    except Exception as e:
        # no queremos que el fallo de logging interrumpa la app
        print("⚠️ Error enviando debug a Discord:", e, file=sys.stdout)
        sys.stdout.flush()


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Verificación del webhook
        # mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            print("✅ Webhook verificado correctamente", file=sys.stdout)
            sys.stdout.flush()
            return challenge, 200
        return "Error de verificación", 403

    if request.method == "POST":
        # Recepción de mensajes
        data = request.get_json()
        print("📩 Mensaje recibido:", json.dumps(data, indent=2), file=sys.stdout)
        sys.stdout.flush()

        # 2) enviar a Discord (compacto / archivo si muy grande)
        send_debug_to_discord("Webhook recibido (Meta -> Render)", data)

        try:
            entry = data["entry"][0]["changes"][0]["value"]
            if "messages" in entry:
                phone_number_id = entry["metadata"]["phone_number_id"]
                from_number = entry["messages"][0]["from"]
                text = entry["messages"][0].get("text", {}).get("body", "")

                print(f"ID del Número de WABA: {phone_number_id}", file=sys.stdout)

                # 🟢 Enviar respuesta automática
                send_whatsapp_message(
                    from_number,
                    "¡Hola! Tu mensaje fue recibido correctamente 👋",
                    phone_number_id,
                )
        except Exception as e:
            print("⚠️ Error procesando mensaje:", e, file=sys.stdout)
            sys.stdout.flush()
            send_debug_to_discord(
                "Error procesando webhook", {"error": str(e), "raw": data}
            )

        return "EVENT_RECEIVED", 200


def send_whatsapp_message(to_number, text, waba_id):
    """Envía un mensaje de texto a través de la API de WhatsApp"""
    url = f"https://graph.facebook.com/v19.0/{waba_id}/messages"
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
    try:
        j = response.json()
    except Exception:
        j = {"status_code": response.status_code, "text": response.text}
    print("📤 Respuesta enviada:", response.text, file=sys.stdout)
    sys.stdout.flush()
    send_debug_to_discord("WhatsApp API response", j)
    return j


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
