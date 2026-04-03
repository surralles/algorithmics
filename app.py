import os, json, sys, requests
from flask import Flask, request
from dotenv import load_dotenv
from openai import OpenAI
import httpx
from utils.pdf_tools import extract_text_from_pdf
import uuid  # Para generar nombres únicos de archivo
from flask import url_for
from flask import request, jsonify
from flask import send_from_directory
from image_generator import create_quiz_image


load_dotenv()

# --- CONFIGURACIÓN ---
app = Flask(__name__)
# Esto fuerza a Flask a entender que 'static' es una carpeta de archivos accesibles
app = Flask(__name__, static_folder="static")
# 1. Limpieza absoluta de variables de entorno de red
for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY"]:
    os.environ.pop(var, None)

# 2. Creamos un cliente HTTP manual vacío de proxies
http_client = httpx.Client(proxies=None)

# 3. Se lo pasamos a OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), http_client=http_client)

# Instagram Config
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
INSTAGRAM_ACCESS_TOKEN_ = os.getenv("INSTAGRAM_ACCESS_TOKEN_")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mi_token_secreto_3892")
DEBUG_DISCORD_WEBHOOK = os.getenv("DEBUG_DISCORD_WEBHOOK")

@app.route('/static/<path:filename>')
def custom_static(filename):
    # Esto fuerza a que el navegador (e Instagram) reconozcan que es una imagen JPEG
    return send_from_directory('static', filename, mimetype='image/jpeg')
    
# 1. Esta es la función lógica
def logic_publish_to_instagram(image_url, caption):
   # Forzamos limpieza absoluta
    clean_id = str(os.getenv("INSTAGRAM_BUSINESS_ID", "")).strip()
    clean_token = str(os.getenv("INSTAGRAM_ACCESS_TOKEN_", "")).strip()
    
    # IMPORTANTE: Mira esto en los logs de Render después de lanzar el curl
    print(f"--- DEBUG START ---")
    print(f"URL: https://graph.facebook.com/v19.0/{clean_id}/media")
    print(f"Token (primeros 10): {clean_token[:10]}...")
    
    post_url = f"https://graph.facebook.com/v19.0/{clean_id}/media"
    
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": clean_token,
        "media_type": "IMAGE"  # <-- AÑADE ESTA LÍNEA para forzar el tipo
    }
    
    r = requests.post(post_url, json=payload)
    res_data = r.json()
    
    if "id" not in res_data:
        return res_data # Devuelve el error para ver qué pasa
    creation_id = res_data["id"]
    
    print(f"RESPONSE FROM META: {res_data}")
    print(f"--- DEBUG END ---")
    
    # Si falla aquí, el log de Render nos dirá EXACTAMENTE qué respondió Meta
    if "error" in res_data:
        print(f"❌ Error de Meta: {res_data['error']['message']}")
        return res_data
    
    container_id = res_data["id"]
    

    # Paso 2: Publicar el contenedor
    publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_BUSINESS_ID}/media_publish"

    publish_payload = {
        "creation_id": creation_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    final_res = requests.post(publish_url, json=publish_payload)
    return final_res.json()
    

# 2. Esta es la RUTA (el endpoint que recibe el curl)
@app.route('/publish_to_instagram', methods=['POST'])
def route_handler():
    # Extraemos los datos del JSON que envías en el curl
    data = request.get_json()
    
    if not data or 'image_url' not in data:
        return jsonify({"error": "Falta image_url en el JSON"}), 400
        
    img = data.get('image_url')
    txt = data.get('caption', 'Post automático')

    # Llamamos a la función lógica con los datos extraídos
    resultado = logic_publish_to_instagram(img, txt)
    
    return jsonify(resultado)


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


@app.route("/")
def hello_world():
    return "<h1>Servidor Algorithmics Activo</h1><p>El bot está esperando PDFs...</p>"


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

    # Creamos un nombre único y una ruta segura en /tmp
    filename = f"{uuid.uuid4().hex}.pdf"
    filepath = os.path.join("/tmp", filename)

    # ¡ESTO ES LO IMPORTANTE!: Guardar el archivo físicamente
    file.save(filepath)

    try:
        text = extract_text_from_pdf(filepath)
        # 2. Generar pregunta con GPT
        quiz_data = generate_quiz_data(text)

        # 3. Pillow genera la imagen en la carpeta static
        img_filename = f"quiz_{uuid.uuid4().hex[:8]}.jpg"
        GENERATED_DIR = "static"
        os.makedirs(GENERATED_DIR, exist_ok=True)
        local_img_path = os.path.join(GENERATED_DIR, img_filename)
        create_quiz_image(quiz_data, local_img_path)

        # 4. Construir URL PÚBLICA para Instagram
        # Render nos da automáticamente la URL base en la variable RENDER_EXTERNAL_URL
        base_url = os.getenv("RENDER_EXTERNAL_URL")
        public_url = f"{base_url}/static/{img_filename}"

        url_prueba = "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg"
        
        print(f"🌍 URL enviada a Instagram: {public_url}")

        # 5. Publicar en Instagram

        caption = (
            f"🧠 ¡Desafío de hoy!\n\n{quiz_data['pregunta']}\n\n👇 Comenta A, B o C."
        )
        result = logic_publish_to_instagram(url_prueba, caption)
        
        return {
            "status": "Post publicado",
            "image_url": url_prueba,
            "instagram_response": result,
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
