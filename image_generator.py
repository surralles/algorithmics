from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# --- CONFIGURACIÓN ---
IMG_SIZE = (1080, 1080)  # Formato cuadrado Instagram
FONT_PATH = "assets/fonts/Montserrat-SemiBold.ttf"  # ¡Ruta a tu fuente .ttf!
BG_IMAGE_PATH = "assets/images/fondo_quiz.png"  # ¡Ruta a tu fondo!
OUTPUT_DIR = "static/generated"

# Colores (RGB)
COLOR_TITULO = (255, 255, 255)  # Blanco
COLOR_PREGUNTA = (255, 255, 255)
COLOR_OPCIONES = (230, 230, 230)  # Gris claro


def draw_multiline_text(draw, text, position, font, max_width, color):
    """
    Función auxiliar para dibujar texto que salta de línea automáticamente.
    Devuelve la coordenada Y donde terminó de dibujar.
    """
    x, y = position
    # Calcula altura aproximada de la línea basado en la fuente
    # bbox devuelve (left, top, right, bottom)
    line_height = font.getbbox("hg")[3] - font.getbbox("hg")[1] + 15

    # textwrap divide el texto en una lista de líneas
    lines = textwrap.wrap(text, width=max_width)

    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += line_height

    return y  # Devuelve la nueva posición Y


def create_quiz_image(quiz_data, output_filename):
    """
    Recibe los datos del quiz (JSON de GPT) y genera una imagen cuadrada.
    Devuelve la ruta local del archivo generado.
    """

    # 1. Crear lienzo base (Cargar fondo o color sólido)
    try:
        base_image = Image.open(BG_IMAGE_PATH).resize(IMG_SIZE)
        # Oscurecer un poco el fondo para que se lea el texto
        overlay = Image.new("RGBA", IMG_SIZE, (0, 0, 0, 100))
        base_image = Image.alpha_composite(base_image.convert("RGBA"), overlay)
    except Exception as e:
        print(f"⚠️ No se encontró fondo en {BG_IMAGE_PATH}, usando color sólido. {e}")
        base_image = Image.new("RGB", IMG_SIZE, color=(50, 50, 100))

    draw = ImageDraw.Draw(base_image)

    # 2. Cargar Fuentes (Tamaños diferentes)
    try:
        # Ajusta los tamaños según tu fuente
        font_titulo = ImageFont.truetype(FONT_PATH, size=70)
        font_pregunta = ImageFont.truetype(FONT_PATH, size=55)
        font_opciones = ImageFont.truetype(FONT_PATH, size=45)
    except IOError:
        print("❌ ERROR: No se encontró la fuente TTF. Usando default (feo).")
        font_titulo = font_pregunta = font_opciones = ImageFont.load_default()

    # --- DIBUJAR ELEMENTOS ---

    current_y = 100  # Margen superior inicial
    margin_x = 80  # Margen lateral

    # A) Título
    draw.text(
        (margin_x, current_y), "🧠 Desafío Diario", font=font_titulo, fill=COLOR_TITULO
    )
    current_y += 150  # Espacio después del título

    # B) Pregunta (con salto de línea)
    # El width en textwrap es caracteres aproximados, ajústalo según tu fuente
    current_y = draw_multiline_text(
        draw,
        quiz_data["pregunta"],
        (margin_x, current_y),
        font_pregunta,
        max_width=35,
        color=COLOR_PREGUNTA,
    )

    current_y += 80  # Espacio entre pregunta y opciones

    # C) Opciones
    opciones = quiz_data["opciones"]
    for letra in ["A", "B", "C"]:
        texto_opcion = f"{letra}) {opciones[letra]}"
        # Dibujamos cada opción
        current_y = draw_multiline_text(
            draw,
            texto_opcion,
            (margin_x, current_y),
            font_opciones,
            max_width=40,
            color=COLOR_OPCIONES,
        )
        current_y += 30  # Espacio extra entre opciones

    # 4. Guardar imagen
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    base_image = base_image.convert("RGB").save(output_path, quality=95)

    print(f"🖼️ Imagen generada: {output_path}")
    return output_path


# --- EJEMPLO DE PRUEBA LOCAL ---
if __name__ == "__main__":
    # Datos de prueba como los que vendrían de GPT
    ejemplo_gpt = {
        "pregunta": "¿Cuál es la función principal de las mitocondrias en la célula animal según el texto estudiado?",
        "opciones": {
            "A": "Realizar la fotosíntesis para generar energía.",
            "B": "Producir energía a través de la respiración celular.",
            "C": "Almacenar la información genética del organismo.",
        },
        "correcta": "B",
    }
    create_quiz_image(ejemplo_gpt, "prueba_local.jpg")
