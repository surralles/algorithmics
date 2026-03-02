from pypdf import PdfReader
import os


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extrae texto de un archivo PDF usando PyPDF2.
    Devuelve un string con el texto concatenado de todas las páginas.
    """
    # Verificación extra
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No encontré el archivo en: {filepath}")

    text = ""
    reader = PdfReader(filepath)

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text
