import os, json, sys, requests
from flask import Flask, request
from dotenv import load_dotenv
from openai import OpenAI
from utils.pdf_tools import extract_text_from_pdf
import uuid  # Para generar nombres únicos de archivo
from flask import url_for
from image_generator import create_quiz_image


load_dotenv()

# --- CONFIGURACIÓN ---
app = Flask(__name__)
# Borramos temporalmente las variables de proxy que Render inyecta
# y que confunden a la librería de OpenAI
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Instagram Config
IG_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
INSTAGRAM_ACCESS_TOKEN_ = os.getenv("INSTAGRAM_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mi_token_secreto_3892")
DEBUG_DISCORD_WEBHOOK = os.getenv("DEBUG_DISCORD_WEBHOOK")

# Carpeta para las imágenes (Render la servirá por /static/generated/...)
GENERATED_DIR = os.path.join("static", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)


def publish_to_instagram(image_url, caption):
    """
    Publica una imagen en el feed de Instagram (Proceso de 2 pasos)
    """
    # Paso 1: Crear el contenedor de la media
    post_url = f"https://graph.facebook.com/v19.0/{IG_BUSINESS_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN_,
    }
    r = requests.post(post_url, data=payload)
    res_data = r.json()
    container_id = r.json().get("id")

    if not container_id:
        return {"Error": "No se pudo crear el contenedor", "details": res_data}

    # Paso 2: Publicar el contenedor
    publish_url = f"https://graph.facebook.com/v19.0/{IG_BUSINESS_ID}/media_publish"
    r = requests.post(
        publish_url,
        data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN_},
    )
    return r.json()


# --- LÓGICA DE IA ---


def generate_quiz_data(text):
    """Genera la pregunta y la respuesta correcta usando GPT"""
    prompt = f"Basado en este texto: {text}. Genera 1 pregunta de test con 3 opciones (A, B, C). Responde SOLO en JSON: {{'pregunta': '...', 'opciones': {{'A': '...', 'B': '...', 'C': '...'}}, 'correcta': 'A'}}"

    response = client.chat.completions.create(
        model="gpt-4o",  # O el que prefieras
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


# --- ENDPOINT PRINCIPAL ---


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Verificación de Meta
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Error", 403

    if request.method == "POST":
        data = request.get_json()

        # Lógica para detectar comentarios en Instagram
        try:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "comments":
                        comment_data = change["value"]
                        comment_text = comment_data.get("text", "").upper().strip()
                        user_id = comment_data.get("from", {}).get("id")
                        media_id = comment_data.get("media", {}).get("id")

                        # Aquí filtrarías si el comentario es "A", "B" o "C"
                        # Y lo compararías con la respuesta correcta guardada en tu DB o Sheets
                        process_answer(user_id, comment_text, media_id)
        except Exception as e:
            print(f"Error en webhook: {e}")

        return "OK", 200


def process_answer(user_id, text, media_id):
    """Aquí manejas el ranking y validación de la respuesta"""
    if text in ["A", "B", "C"]:
        print(f"Usuario {user_id} respondió {text} en el post {media_id}")
        # 1. Buscar respuesta correcta del post en tu DB
        # 2. Si es correcta, sumar puntos en Google Sheets


# --- ENDPOINT PRINCIPAL ---


@app.route("/process_daily_pdf", methods=["POST"])
def process_daily_pdf():
    if "file" not in request.files:
        return {"error": "Falta el archivo PDF"}, 400
    # 1. Extraer PDF
    file = request.files["file"]
    temp_pdf = f"/tmp/{uuid.uuid4().hex}.pdf"
    file.save("temp.pdf")

    try:
        pdf_text = extract_text_from_pdf(temp_pdf)
        # 2. Generar pregunta con GPT
        quiz_data = generate_quiz_data(pdf_text)

        # 3. Pillow genera la imagen en la carpeta static
        img_filename = f"quiz_{uuid.uuid4().hex}.jpg"
        local_img_path = os.path.join(GENERATED_DIR, img_filename)
        create_quiz_image(quiz_data, local_img_path)

        # 4. Construir URL PÚBLICA para Instagram
        # Render nos da automáticamente la URL base en la variable RENDER_EXTERNAL_URL
        base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:5000")
        public_url = f"{base_url}/static/generated/{img_filename}"

        print(f"🌍 URL enviada a Instagram: {public_url}")

        # 5. Publicar en Instagram

        caption = (
            f"🧠 ¡Desafío de hoy!\n\n{quiz_data['pregunta']}\n\n👇 Comenta A, B o C."
        )
        result = publish_to_instagram(public_url, caption)

        return {
            "status": "Post publicado",
            "image_url": public_url,
            "instagram_response": result,
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        # Limpiar el PDF temporal
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
