import os
import json
import gspread
from google.oauth2.service_account import Credentials


def get_gspread_client():
    # 1. Intentar leer la variable de entorno que pegamos en Render
    creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if creds_json_str:
        # Estamos en Render (o tenemos la variable configurada)
        creds_info = json.loads(creds_json_str)
    else:
        # Local: Si no hay variable, intentamos leer el archivo físico por si acaso
        # Pero lo ideal es que también uses el .env localmente
        with open("autoclass-assistant-36ed907c340c.json") as f:
            creds_info = json.load(f)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)


def append_result_to_sheet(phone, score, total, test_name):
    client = get_gspread_client()
    sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1
    sheet.append_row([phone, score, total, test_name])
