from pypdf import PdfReader


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extrae texto de un archivo PDF usando PyPDF2.
    Devuelve un string con el texto concatenado de todas las páginas.
    """
    text = ""
    reader = PdfReader(filepath)

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text
