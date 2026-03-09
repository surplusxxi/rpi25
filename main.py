import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Archivo de credenciales descargado desde Google Cloud Console
CREDENTIALS_FILE = "credentials.json"

# Permisos para todas las APIs
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",       # Google Sheets
    "https://www.googleapis.com/auth/drive",              # Google Drive
    "https://www.googleapis.com/auth/gmail.modify",       # Gmail
    "https://www.googleapis.com/auth/calendar",           # Google Calendar
    "https://www.googleapis.com/auth/docs",               # Google Docs
    "https://www.googleapis.com/auth/forms",              # Google Forms
    "https://www.googleapis.com/auth/youtube",            # YouTube
    "https://www.googleapis.com/auth/cloud-platform",     # Google Cloud
]

# IDs de recursos (editar según tu proyecto)
SPREADSHEET_ID = "TU_SPREADSHEET_ID"
CALENDAR_ID = "primary"
FOLDER_ID_DRIVE = "TU_FOLDER_ID"


def get_service(api, version):
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return build(api, version, credentials=creds)


# ─── GOOGLE SHEETS ────────────────────────────────────────────────────────────

def sheets_leer(rango="Hoja1!A1:Z100"):
    service = get_service("sheets", "v4")
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=rango
    ).execute()
    return result.get("values", [])


def sheets_escribir(rango, datos):
    service = get_service("sheets", "v4")
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=rango,
        valueInputOption="RAW",
        body={"values": datos},
    ).execute()
    print("Sheets: datos escritos.")


# ─── GOOGLE DRIVE ─────────────────────────────────────────────────────────────

def drive_listar_archivos():
    service = get_service("drive", "v3")
    results = service.files().list(pageSize=20, fields="files(id, name, mimeType)").execute()
    archivos = results.get("files", [])
    for f in archivos:
        print(f"{f['name']} ({f['id']})")
    return archivos


def drive_subir_archivo(ruta_local, nombre_en_drive):
    from googleapiclient.http import MediaFileUpload
    service = get_service("drive", "v3")
    metadata = {"name": nombre_en_drive, "parents": [FOLDER_ID_DRIVE]}
    media = MediaFileUpload(ruta_local)
    file = service.files().create(body=metadata, media_body=media, fields="id").execute()
    print(f"Drive: archivo subido con ID {file.get('id')}")
    return file


# ─── GMAIL ────────────────────────────────────────────────────────────────────

def gmail_enviar(destinatario, asunto, cuerpo):
    import base64
    from email.mime.text import MIMEText
    service = get_service("gmail", "v1")
    mensaje = MIMEText(cuerpo)
    mensaje["to"] = destinatario
    mensaje["subject"] = asunto
    raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"Gmail: correo enviado a {destinatario}")


def gmail_leer_inbox(max_resultados=5):
    service = get_service("gmail", "v1")
    results = service.users().messages().list(userId="me", maxResults=max_resultados).execute()
    mensajes = results.get("messages", [])
    for m in mensajes:
        msg = service.users().messages().get(userId="me", id=m["id"], format="metadata").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        print(f"De: {headers.get('From')} | Asunto: {headers.get('Subject')}")
    return mensajes


# ─── GOOGLE CALENDAR ──────────────────────────────────────────────────────────

def calendar_listar_eventos(max_resultados=10):
    from datetime import datetime, timezone
    service = get_service("calendar", "v3")
    ahora = datetime.now(timezone.utc).isoformat()
    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=ahora,
        maxResults=max_resultados,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    for e in events.get("items", []):
        inicio = e["start"].get("dateTime", e["start"].get("date"))
        print(f"{inicio} - {e['summary']}")
    return events.get("items", [])


def calendar_crear_evento(titulo, inicio, fin, descripcion=""):
    service = get_service("calendar", "v3")
    evento = {
        "summary": titulo,
        "description": descripcion,
        "start": {"dateTime": inicio, "timeZone": "America/Bogota"},
        "end": {"dateTime": fin, "timeZone": "America/Bogota"},
    }
    result = service.events().insert(calendarId=CALENDAR_ID, body=evento).execute()
    print(f"Calendar: evento creado -> {result.get('htmlLink')}")
    return result


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Google APIs Automation ===")

    # Sheets
    datos = sheets_leer("Hoja1!A1:D5")
    print("Sheets:", datos)

    # Drive
    print("\nArchivos en Drive:")
    drive_listar_archivos()

    # Gmail
    print("\nInbox:")
    gmail_leer_inbox()

    # Calendar
    print("\nPróximos eventos:")
    calendar_listar_eventos()
