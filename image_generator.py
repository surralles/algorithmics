from PIL import Image, ImageDraw, ImageFont
import os

def create_quiz_image(quiz_data, output_path):
    # --- CONFIGURACIÓN ---
    IMG_SIZE = 1080 
    BG_COLOR = (15, 20, 30) 
    TEXT_COLOR = (240, 240, 240) 
    ACCENT_COLOR = (0, 255, 150) 

    img = Image.new('RGB', (IMG_SIZE, IMG_SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- CARGAR FUENTES ---
    font_folder = os.path.join(os.path.dirname(__file__), 'static', 'fonts')
    # Intenta usar la fuente que subiste, si no, usa una de sistema de Render
    try:
        title_font = ImageFont.truetype(os.path.join(font_folder, "Montserrat-Bold.ttf"), 65)
        code_font = ImageFont.truetype(os.path.join(font_folder, "JetBrainsMono-Medium.ttf"), 50)
        option_font = ImageFont.truetype(os.path.join(font_folder, "Montserrat-Bold.ttf"), 55)
    except:
        # Plan B para Render (Linux)
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            code_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 45)
            option_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        except:
            title_font = code_font = option_font = ImageFont.load_default()

    # --- DIBUJAR CONTENIDO ---
    
    # 1. Título principal (Centrado)
    title_text = "¿Cuál es la salida?"
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    w = bbox[2] - bbox[0]
    draw.text(((IMG_SIZE - w) / 2, 80), title_text, fill=ACCENT_COLOR, font=title_font)

    # 2. Bloque de código
    code_text = quiz_data.get('codigo', 'print("Error")')
    margin = 80
    y_text = 250
    draw.text((margin, y_text), code_text, fill=TEXT_COLOR, font=code_font)

    # 3. Opciones A, B, C
    options_y = 620
    gap = 100
    draw.text((margin, options_y), f"A) {quiz_data.get('respuesta_a', '')}", fill=TEXT_COLOR, font=option_font)
    draw.text((margin, options_y + gap), f"B) {quiz_data.get('respuesta_b', '')}", fill=TEXT_COLOR, font=option_font)
    draw.text((margin, options_y + gap*2), f"C) {quiz_data.get('respuesta_c', '')}", fill=TEXT_COLOR, font=option_font)

    # 4. Marca de agua (Centrada abajo)
    footer_text = "@nextskillz_"
    bbox_f = draw.textbbox((0, 0), footer_text, font=title_font)
    wf = bbox_f[2] - bbox_f[0]
    draw.text(((IMG_SIZE - wf) / 2, IMG_SIZE - 120), footer_text, fill=ACCENT_COLOR, font=title_font)

    img.save(output_path, quality=95)
