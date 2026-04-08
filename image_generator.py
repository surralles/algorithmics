from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def create_quiz_image(quiz_data, output_path):
    '''
    # --- CONFIGURACIÓN DE COLORES Y ESTILO ---
    BG_COLOR = (10, 15, 25) # Azul casi negro
    BOX_COLOR = (25, 30, 45) # Caja de código un poco más clara
    TEXT_MAIN = (240, 240, 240) # Texto título
    TEXT_CODE = (160, 210, 255) # Texto de código por defecto (azul claro)
    # Sintaxis de código
    COLOR_KEYWORD = (235, 110, 180) # Rosa/Violeta para 'def', 'for'
    COLOR_STRING = (255, 180, 100) # Naranja claro para texto "ejemplo"
    COLOR_OPT_A = (120, 240, 160) # Verde para la opción A
    COLOR_OPT_B = (255, 230, 130) # Amarillo para la opción B
    COLOR_OPT_C = (255, 120, 120) # Rojo para la opción C

    # --- TAMAÑOS ---
    IMG_W, IMG_H = 1080, 1920 # Formato Reel Vertical
    BOX_W, BOX_H = 900, 1000 # Caja central
    CORNER_RADIUS = 30
    logo_size = 80 # Tamaño de los logos de tecnología
    ig_icon_size = 40 # Tamaño del icono de Instagram

    # 1. CREAR EL FONDO CON UN GRADIENTE SUTIL (efecto profundidad)
    # Para simplicidad, usaremos un color sólido para empezar, pero el estilo será el mismo.
    img = Image.new('RGB', (IMG_W, IMG_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 2. DIBUJAR LA CAJA CENTRAL CON BORDES REDONDEADOS Y BRILLO
    box_x = (IMG_W - BOX_W) // 2
    box_y = 400 # Dejamos espacio arriba para el título
    
    # Dibujamos la caja central con Pillow
    draw.rounded_rectangle([box_x, box_y, box_x + BOX_W, box_y + BOX_H], 
                          radius=CORNER_RADIUS, fill=BOX_COLOR)
    
    # --- CARGAR FUENTES (Necesitas los archivos .ttf) ---
    # Tienes que tener estas fuentes descargadas en una carpeta 'fonts'
    # Montserrat para títulos, JetBrainsMono para código.
    font_folder = os.path.join(os.path.dirname(__file__), 'static', 'fonts')
    print(f"Buscando fuentes en: {font_folder}")

    try:
        title_font = ImageFont.truetype(os.path.join(font_folder, "Montserrat-Bold.ttf"), 60)
        print("✅ Fuente Título cargada")
        tech_font = ImageFont.truetype(os.path.join(font_folder, "Montserrat-Regular.ttf"), 45)
        code_font = ImageFont.truetype(os.path.join(font_folder, "JetBrainsMono-Medium.ttf"), 40)
        brand_font = ImageFont.truetype(os.path.join(font_folder, "Montserrat-Regular.ttf"), 35)
        print("✅ Fuente Código cargada")
    except OSError as e:
        print(f"❌ ERROR DE FUENTE: {e}")
        # Plan B: Cargar la fuente por defecto del sistema para que no se detenga el programa
        title_font = tech_font = brand_font = ImageFont.load_default()
        code_font = ImageFont.load_default()

    # 3. TEXTO SUPERIOR (FUERA DE LA CAJA)
    title_text = f"Módulo: {quiz_data.get('nombre_modulo', 'Algoritmos')}"
    draw.text((IMG_W // 2, 200), title_text, fill=TEXT_MAIN, font=title_font, anchor="ms")

    # 4. HEADER DE LA CAJA (Logo Tech + Nombre Tech)
    tech_name = quiz_data.get('tecnologia', 'Python').strip() # OpenAI debería darnos la tecnología
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logos', f"{tech_name.lower()}_logo.png")

    # Así el código no explota si OpenAI olvida mandar la tecnología
    tech_text = quiz_data.get('tecnologia', 'Coding').strip()

    draw.text(
        (box_x + 50 + logo_size + 20, box_y + 40 + (logo_size // 2)), 
        tech_text, 
        fill=TEXT_MAIN, 
        font=tech_font, 
        anchor="lm"
    )
    
    print(f"DEBUG: Buscando logo en esta ruta exacta: '{logo_path}'")

    # Comprobamos si el archivo existe ANTES de intentar abrirlo
    if not os.path.exists(logo_path):
        print(f"❌ ERROR: El archivo de logo NO EXISTE en: {logo_path}")
        # Puedes decidir si saltar el logo o usar uno por defecto
    else:
        print(f"✅ Archivo de logo encontrado. Intentando abrir...")
        tech_logo = Image.open(logo_path).convert("RGBA").resize((logo_size, logo_size))
        
        # Pegamos el logo con transparencia
        img.paste(tech_logo, (box_x + 50, box_y + 40), tech_logo)
        # Nombre de la tecnología al lado del logo
        draw.text((box_x + 50 + logo_size + 20, box_y + 40 + (logo_size // 2)), tech_name, fill=TEXT_MAIN, font=tech_font, anchor="lm")

    # 5. EL CÓDIGO (CON RESALTADO DE SINTAXIS SIMPLE)
    # OpenAI nos dará el código como una cadena. Usamos sintaxis básica.
    code_text = quiz_data['codigo']
    code_start_y = box_y + 180
    
    draw.text((box_x + 50, code_start_y), code_text, fill=TEXT_CODE, font=code_font)
    
    # --- PRO-TIP: Resaltado de Sintaxis Dinámico ---
    # Esto es complejo. Para empezar, el texto será de un solo color.
    # Pero el efecto 'caja de vidrio' ya le da el toque.
    
    # 6. LAS OPCIONES A, B, C (Abajo del código, fuera de la caja de código pero dentro de la central si quieres)
    # Lo mejor es ponerlas separadas y con colores diferentes para incentivar a,b,c
    opt_y = box_y + BOX_H - 250
    # Usamos colores diferentes para que destaquen como botones
    draw.text((box_x + 50, opt_y), f"A: {quiz_data['respuesta_a']}", fill=COLOR_OPT_A, font=code_font)
    draw.text((box_x + 50, opt_y + 60), f"B: {quiz_data['respuesta_b']}", fill=COLOR_OPT_B, font=code_font)
    draw.text((box_x + 50, opt_y + 120), f"C: {quiz_data['respuesta_c']}", fill=COLOR_OPT_C, font=code_font)

    # 7. EL FOOTER: Instagram Icon + Username
    ig_path = os.path.join(os.path.dirname(__file__), 'static', 'logos', 'ig_logo.png')
    footer_text = "Instagram: @nextskillz_"
    footer_y = IMG_H - 150 # Cerca del final del Reel
    
    if os.path.exists(ig_path):
        ig_logo = Image.open(ig_path).convert("RGBA").resize((ig_icon_size, ig_icon_size))
        # Pegamos el icono de IG
        img.paste(ig_logo, (box_x + 50, footer_y), ig_logo)
        # Nombre de usuario al lado del icono
        draw.text((box_x + 50 + ig_icon_size + 15, footer_y + (ig_icon_size // 2)), footer_text, fill=TEXT_MAIN, font=brand_font, anchor="lm")

    # 8. GUARDAR Y LISTO
    img.save(output_path)
    print(f"✅ Imagen de Reel Ultra-Estilizada creada: {output_path}")
    '''
    # --- CONFIGURACIÓN DE ESTILO ---
    BG_COLOR = (10, 15, 25) # Azul casi negro (estilo código oscuro)
    TEXT_MAIN = (240, 240, 240) # Texto principal (blanco roto)
    TEXT_CODE = (160, 210, 255) # Texto de código por defecto (azul claro)
    COLOR_KEYWORD = (235, 110, 180) # Rosa/Violeta para palabras clave
    COLOR_STRING = (255, 180, 100) # Naranja claro para strings
    COLOR_OPT_A = (120, 240, 160) # Verde para la opción A
    COLOR_OPT_B = (255, 230, 130) # Amarillo para la opción B
    COLOR_OPT_C = (255, 120, 120) # Rojo para la opción C

    # --- TAMAÑO CUADRADO ---
    IMG_SIZE = 1080 # Tamaño estándar para posts cuadrados

    img = Image.new('RGB', (IMG_SIZE, IMG_SIZE), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # --- CARGAR FUENTES (Usa fuentes preinstaladas en Linux para evitar 'cannot open resource') ---
    try:
        # En Render (Linux), CourierNew suele estar preinstalada para el código
        code_font = ImageFont.truetype("CourierNew.ttf", 45)
        # Y DejaVuSans para el texto normal
        text_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 55)
        brand_font = ImageFont.truetype("DejaVuSans.ttf", 35)
    except OSError:
        # Si fallan, cargamos la de serie (menos bonita, pero funcional)
        print("⚠️ Fuentes personalizadas no encontradas, usando las por defecto.")
        code_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()

    # --- DIBUJAR ELEMENTOS ---
    
    # 1. TÍTULO
    title_text = "¿Cuál es la salida de este código?"
    draw.text((IMG_SIZE // 2, 120), title_text, fill=TEXT_MAIN, font=text_font, anchor="ms")

    # 2. EL CÓDIGO (Resaltado de Sintaxis Simple)
    code_text = quiz_data.get('codigo', 'print("Prueba de Código")')
    code_start_y = 250
    # Dibujamos el código con el color por defecto
    draw.text((100, code_start_y), code_text, fill=TEXT_CODE, font=code_font)
    
    # PRO-TIP: Resaltado de sintaxis súper básico (palabras clave 'def' y 'print')
    keywords = ["def ", "print("]
    # (Este resaltado es muy básico, lo ideal es una librería, pero para probar sirve)
    # Por ahora, para evitar complejidades, lo dejaremos en un solo color.

    # 3. LAS OPCIONES A, B, C
    opt_y = 650
    draw.text((100, opt_y), f"A: {quiz_data.get('respuesta_a', 'Opción A')}", fill=COLOR_OPT_A, font=code_font)
    draw.text((100, opt_y + 80), f"B: {quiz_data.get('respuesta_b', 'Opción B')}", fill=COLOR_OPT_B, font=code_font)
    draw.text((100, opt_y + 160), f"C: {quiz_data.get('respuesta_c', 'Opción C')}", fill=COLOR_OPT_C, font=code_font)

    # 4. EL FOOTER: Marca de Agua
    footer_text = "Instagram: @nextskillz_"
    footer_y = IMG_SIZE - 100
    draw.text((IMG_SIZE // 2, footer_y), footer_text, fill=TEXT_MAIN, font=brand_font, anchor="ms")

    # 5. GUARDAR Y LISTO
    img.save(output_path)
    print(f"✅ Imagen de Post Cuadrado creada: {output_path}")
