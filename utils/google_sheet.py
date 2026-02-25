from __future__ import print_function
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")
# Ruta de credenciales JSON

# ID de tu Google Sheet (copiar de la URL)
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
creds = service_account.Credentials.from_service_account_file(
    "autoclass-assistant-36ed907c340c.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)


service = build("sheets", "v4", credentials=creds)
sheets = service.spreadsheets().get(spreadsheetId=GOOGLE_SHEET_ID).execute()
print("🔍 Hojas disponibles:", [s["properties"]["title"] for s in sheets["sheets"]])


def append_result_to_sheet(phone, score, total, test_name):
    print("🔎 GOOGLE_SHEET_ID =", GOOGLE_SHEET_ID)
    sheet = service.spreadsheets().values()

    data = [phone, score, total, f"{score}/{total}", test_name]

    result = sheet.append(
        spreadsheetId=GOOGLE_SHEET_ID,  # ← ESTO ES CLAVE
        range="Results!A1",
        valueInputOption="USER_ENTERED",
        body={"values": [data]},
    ).execute()

    print("✔ Guardado en Google Sheet:", result)
    return result
