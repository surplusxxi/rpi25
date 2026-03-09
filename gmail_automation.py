"""
Gmail Automation - Usando Gmail API con OAuth2
Requiere: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import os
import base64
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Permisos requeridos (scopes)
# Si cambias los scopes, borra el token.pickle para re-autenticar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

CREDENTIALS_FILE = 'credentials/client_secret.json'
TOKEN_FILE = 'credentials/token.pickle'


def autenticar():
    """Autentica con Gmail API y retorna el servicio."""
    creds = None

    # Cargar token existente si hay uno
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # Si no hay credenciales válidas, pedir login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"No se encontró {CREDENTIALS_FILE}\n"
                    "Copia tu archivo client_secret_*.json a credentials/client_secret.json"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Guardar token para la próxima vez
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def enviar_email(servicio, destinatario, asunto, cuerpo, html=False):
    """Envía un email."""
    mensaje = MIMEMultipart('alternative')
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    tipo = 'html' if html else 'plain'
    mensaje.attach(MIMEText(cuerpo, tipo))

    raw = base64.urlsafe_b64encode(mensaje.as_bytes()).decode()
    result = servicio.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()

    print(f"Email enviado. ID: {result['id']}")
    return result


def leer_emails(servicio, max_resultados=10, query='is:unread'):
    """Lee emails de la bandeja de entrada."""
    resultados = servicio.users().messages().list(
        userId='me',
        maxResults=max_resultados,
        q=query
    ).execute()

    mensajes = resultados.get('messages', [])
    emails = []

    for msg in mensajes:
        detalle = servicio.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()

        headers = {h['name']: h['value'] for h in detalle['payload']['headers']}
        emails.append({
            'id': msg['id'],
            'de': headers.get('From', ''),
            'asunto': headers.get('Subject', ''),
            'fecha': headers.get('Date', ''),
        })

    return emails


def marcar_como_leido(servicio, mensaje_id):
    """Marca un email como leído."""
    servicio.users().messages().modify(
        userId='me',
        id=mensaje_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()


# ─── Ejemplo de uso ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Autenticando con Gmail...")
    servicio = autenticar()
    print("Autenticado correctamente.\n")

    # Ejemplo 1: Leer emails no leídos
    print("=== Emails no leídos ===")
    emails = leer_emails(servicio, max_resultados=5, query='is:unread')
    if emails:
        for email in emails:
            print(f"De: {email['de']}")
            print(f"Asunto: {email['asunto']}")
            print(f"Fecha: {email['fecha']}")
            print("---")
    else:
        print("No hay emails no leídos.")

    # Ejemplo 2: Enviar un email (descomenta para usar)
    # enviar_email(
    #     servicio,
    #     destinatario='destino@ejemplo.com',
    #     asunto='Prueba desde rpi25',
    #     cuerpo='Hola! Este email fue enviado automáticamente desde el script.',
    # )
