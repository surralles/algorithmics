from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def create_quiz_image(quiz_data, output_path):
# --- CONFIGURACIÓN ---
    IMG_SIZE = 1080 # Cuadrado perfecto para Post
    BG_COLOR = (15, 20, 30) # Azul muy oscuro (profesional)
    TEXT_COLOR = (240, 240, 240) # Blanco roto
    ACCENT_COLOR = (0, 255, 150) # Verde neón para resaltar

    # Crear lienzo
    img = Image.new('RGB', (IMG_SIZE, IMG_SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- CARGAR FUENTES ---
    # Asumimos que has subido 'Montserrat-Bold.ttf' a static/fonts/
    font_path = os.path.join(os.path.dirname(__file__), 'static', 'fonts', 'Montserrat-Bold.ttf')
    
    try:
        # Fuentes GRANDES para máxima legibilidad
        title_font = ImageFont.truetype(font_path, 60) # Título
        code_font = ImageFont.truetype(font_path, 50)  # Bloque de código
        option_font = ImageFont.truetype(font_path, 55) # Opciones A,B,C
    except OSError:
        print("⚠️ Fuente personalizada no encontrada, usando predeterminada (se verá pequeña).")
        title_font = code_font = option_font = ImageFont.load_default()

    # --- DIBUJAR CONTENIDO ---
    
    # 1. Título principal
    title_text = "¿Cuál es la salida?"
    # Centrado horizontalmente
    w, h = draw.textsize(title_text, font=title_font)
    draw.text(((IMG_SIZE - w) / 2, 80), title_text, fill=ACCENT_COLOR, font=title_font)

    # 2. Bloque de código (centrado y con margen)
    code_text = quiz_data.get('codigo', 'print("Error al generar código")')
    # Ajuste básico de línea si es muy largo (esto es simplificado)
    margin = 100
    y_text = 250
    draw.text((margin, y_text), code_text, fill=TEXT_COLOR, font=code_font)

    # 3. Opciones A, B, C (Abajo, GRANDES)
    options_y = 650
    options_gap = 90
    
    draw.text((margin, options_y), f"A) {quiz_data.get('respuesta_a', '???')}", fill=TEXT_COLOR, font=option_font)
    draw.text((margin, options_y + options_gap), f"B) {quiz_data.get('respuesta_b', '???')}", fill=TEXT_COLOR, font=option_font)
    draw.text((margin, options_y + options_gap * 2), f"C) {quiz_data.get('respuesta_c', '???')}", fill=TEXT_COLOR, font=option_font)

    # 4. Marca de agua (Súper legible)
    footer_text = "@nextskillz_"
    fw, fh = draw.textsize(footer_text, font=title_font)
    draw.text(((IMG_SIZE - fw) / 2, IMG_SIZE - 120), footer_text, fill=ACCENT_COLOR, font=title_font)

    # Guardar
    img.save(output_path, quality=95) # Guardar con alta calidad
    print(f"✅ Imagen profesional cuadrada creada en: {output_path}")
