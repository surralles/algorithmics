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
import base64
import cloudinary
import cloudinary.uploader


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

'''def upload_to_imgbb(image_path):
    """Sube la imagen de Render a ImgBB para obtener una URL pública estable"""
    api_key = os.getenv("IMGBB_API_KEY")
    if not api_key:
        print("❌ ERROR: No se encontró la variable IMGBB_API_KEY en Render")
        return None
    url = "https://api.imgbb.com/1/upload"
    
    with open(image_path, "rb") as file:
        # Convertimos la imagen a base64 (formato que pide ImgBB y Meta)
        image_data = base64.b64encode(file.read())
        payload = {
            "key": api_key,
            "image": image_data,
        }
        res = requests.post(url, data=payload)
        
        if res.status_code == 200:
            json_data = res.json()
            url_publica = json_data["data"]["url"]
            print(f"✅ Imagen subida a ImgBB: {url_publica}")
            return url_publica
            
        else:
            print(f"❌ Error subiendo a ImgBB: {res.text}")
            return None
'''


# 1. Esta es la función lógica
def logic_publish_to_instagram(image_url, caption):
   # Forzamos limpieza absoluta
    business_id = str(os.getenv("INSTAGRAM_BUSINESS_ID", "")).strip()
    access_token = str(os.getenv("INSTAGRAM_ACCESS_TOKEN_", "")).strip()
    
    # IMPORTANTE: Mira esto en los logs de Render después de lanzar el curl
    print(f"--- DEBUG START ---")
    print(f"URL: https://graph.facebook.com/v19.0/{business_id}/media")
    
    
    post_url = f"https://graph.facebook.com/v19.0/{business_id}/media"
    
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
        "media_type": "IMAGE"  # <-- AÑADE ESTA LÍNEA para forzar el tipo
    }
    
    r = requests.post(post_url, json=payload)
    res_data = r.json()
    
    if "id" not in res_data:
        print(f"❌ Error en Paso 1 (Contenedor): {res_data}")
        return res_data # Devuelve el error para ver qué pasa
    creation_id = res_data["id"]
    
    # Si falla aquí, el log de Render nos dirá EXACTAMENTE qué respondió Meta
    if "error" in res_data:
        print(f"❌ Error de Meta: {res_data['error']['message']}")
        return res_data
    
    container_id = res_data["id"]
    

    # Paso 2: Publicar el contenedor
    publish_url = f"https://graph.facebook.com/v19.0/{business_id}/media_publish"

    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    final_res = requests.post(publish_url, json=publish_payload)
    print(f"RESPONSE FROM META (Final): {final_res.json()}")
    print(f"--- DEBUG END ---")
    
    return final_res.json()
    
# --- LÓGICA DE IA ---

def generate_quiz_data(text):
    prompt = """
    Genera un quiz técnico en formato JSON con la siguiente estructura:
    {
      "nombre_modulo": "Nombre del tema (ej: Estructuras de Datos)",
      "tecnologia": "Lenguaje (ej: Python)",
      "codigo": "El bloque de código para el desafío",
      "pregunta": "¿Qué imprimirá este código?",
      "respuesta_a": "opción A",
      "respuesta_b": "opción B",
      "respuesta_c": "opción C",
      "respuesta_correcta": "A, B o C"
    }
    """

    response = client.chat.completions.create(
        model="gpt-4o",  # O el que prefieras
        messages=[{"role": "system", "content": "Eres un experto en programación."},
                  {"role": "user", "content": f"{prompt}\n\nTexto del PDF: {text}"}],
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
                        val = change["value"]
                        process_answer(val.get("from", {}).get("id"), 
                                       val.get("text", "").upper().strip(), 
                                       val.get("media", {}).get("id"))

                      
        except Exception as e:
            print(f"Error en webhook: {e}")

        return "OK", 200


def process_answer(user_id, text, media_id):
    """Aquí manejas el ranking y validación de la respuesta"""
    if text in ["A", "B", "C"]:
        print(f"Usuario {user_id} respondió {text} en el post {media_id}")
       


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
        img_filename = "current_quiz_post.jpg"
        local_img_path = os.path.join("static", img_filename)
        os.makedirs("static", exist_ok=True)
       
        create_quiz_image(quiz_data, local_img_path)

        # 4. Construir URL PÚBLICA para Instagram
        base_url = os.getenv("RENDER_EXTERNAL_URL")
        #public_url = upload_to_imgbb(local_img_path)
        if not base_url:
            return {"error": "Falta la variable de entorno RENDER_EXTERNAL_URL. Configúrala en Render."}, 500
        # 5. Publicar en Instagram
        public_url = f"{base_url}/static/{img_filename}"
        print(f"🌍 URL generada para Instagram: {public_url}")
        if public_url:
            
            caption = (f"🚨 DESAFÍO ALGORITHMICS 🚨\n\n"
                       f"¿Cuál es la respuesta correcta para este reto de {quiz_data.get('tecnologia', 'Código')}?\n"
                       f"Comenta A, B, o C abajo 👇\n\n"
                       f"#Algorithmics #NextSkillz #AprendeACodear")
            
            result = logic_publish_to_instagram(public_url, caption)
            if "id" in result: 
                if os.path.exists(local_img_path):
                    os.remove(local_img_path)
                    print(f"🗑️ Archivo temporal {local_img_path} eliminado con éxito.")
        else:
            result = {"error": "No se pudo subir la imagen a la nube"}
        
        return {
            "status": "Post publicado",
            "image_url": public_url,
            "instagram_response": result,
        }, 200

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/")
def index():
    return "<h1>Servidor Algorithmics Activo</h1>"    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
