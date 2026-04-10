from PIL import Image, ImageDraw, ImageFont
import os

def create_quiz_image(quiz_data, output_path):
    # --- CONFIGURACIÓN ESTÉTICA ---
    IMG_SIZE = 1080 
    BG_COLOR = (15, 20, 30)       # Azul muy oscuro (profesional)
    TITLE_COLOR = (0, 255, 150)   # Verde neón (Título y Marca)
    CODE_COLOR = (200, 220, 240)  # Blanco azulado para el código
    OPTIONS_COLOR = (240, 240, 240) # Blanco roto para opciones A,B,C

    img = Image.new('RGB', (IMG_SIZE, IMG_SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- SISTEMA DE FUENTES INTELIGENTE ---
    fonts_dir = os.path.join(os.path.dirname(__file__), 'static', 'fonts')
    
    # Intenta cargar tus fuentes, si no, usa las de sistema de Linux (Render)
    try:
        title_font = ImageFont.truetype(os.path.join(fonts_dir, "Montserrat-Bold.ttf"), 65)
        # Fuente Monoespaciada específica para el código
        code_font = ImageFont.truetype(os.path.join(fonts_dir, "JetBrainsMono-Medium.ttf"), 45)
        option_font = ImageFont.truetype(os.path.join(fonts_dir, "Montserrat-SemiBold.ttf"), 50)
    except:
        # PLAN B (Fuentes de sistema en Render/Linux)
        print("⚠️ Fuentes personalizadas no encontradas, usando DejaVu (Render).")
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            code_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 40)
            option_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
        except:
            title_font = code_font = option_font = ImageFont.load_default()

    # --- DIBUJAR ELEMENTOS CON CÁLCULO DE ESPACIO ---
    margin = 80
    current_y = 100

    # 1. TÍTULO (Centrado)
    title_text = quiz_data.get('pregunta', '¿Cuál es la salida?')
    bbox_t = draw.textbbox((0, 0), title_text, font=title_font)
    wt = bbox_t[2] - bbox_t[0]
    draw.text(((IMG_SIZE - wt) / 2, current_y), title_text, fill=TITLE_COLOR, font=title_font)
    
    current_y += 120 # Espacio bajo el título

    # 2. BLOQUE DE CÓDIGO (Calculamos su altura real)
    code_text = quiz_data.get('codigo', '# Código no disponible')
    # Calculamos el bounding box para ver cuánto ocupa
    bbox_c = draw.textbbox((0, 0), code_text, font=code_font)
    code_height = bbox_c[3] - bbox_c[ top ] # Altura total del código
    
    print(f"DEBUG: Altura del código generada: {code_height}px")
    
    # Dibujamos el código
    draw.text((margin, current_y), code_text, fill=CODE_COLOR, font=code_font)

    # 3. OPCIONES A, B, C (DINÁMICAS)
    # Colocamos las opciones 80px por DEBAJO del final real del código
    current_y += code_height + 80
    
    draw.text((margin, current_y), f"A) {quiz_data.get('respuesta_a', '')}", fill=OPTIONS_COLOR, font=option_font)
    current_y += 75
    draw.text((margin, current_y), f"B) {quiz_data.get('respuesta_b', '')}", fill=OPTIONS_COLOR, font=option_font)
    current_y += 75
    draw.text((margin, current_y), f"C) {quiz_data.get('respuesta_c', '')}", fill=OPTIONS_COLOR, font=option_font)

    # 4. MARCA DE AGUA (Centrada abajo)
    footer_text = "@nextskillz_"
    bbox_f = draw.textbbox((0, 0), footer_text, font=title_font)
    wf = bbox_f[2] - bbox_f[0]
    # Dibujamos en verde neón, cerca del borde inferior
    draw.text(((IMG_SIZE - wf) / 2, IMG_SIZE - 150), footer_text, fill=TITLE_COLOR, font=title_font)

    # Guardar con alta calidad
    img.save(output_path, format="JPEG", quality=90)
    print(f"✅ Imagen profesional cuadrada creada y guardada en: {output_path}")
