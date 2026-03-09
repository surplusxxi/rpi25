"""
Google OAuth2 Authentication Module
Maneja autenticación para Google Calendar y Gmail APIs.
"""

import os
import json
import pickle
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
]

TOKEN_FILE = Path("token.pickle")
CREDENTIALS_FILE = Path("credentials.json")


def get_credentials() -> Credentials:
    """
    Obtiene o refresca las credenciales OAuth2.
    - Si existe token.pickle válido, lo usa.
    - Si existe credentials.json, lanza el flujo OAuth.
    - Si existen variables de entorno, construye credenciales desde ahí.
    """
    creds = None

    # 1. Intentar cargar token guardado
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    # 2. Refrescar si expirado
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception as e:
            print(f"[AUTH] No se pudo refrescar token: {e}")
            creds = None

    if creds and creds.valid:
        return creds

    # 3. Intentar desde variables de entorno
    env_token = os.environ.get("GOOGLE_TOKEN_JSON")
    if env_token:
        try:
            token_data = json.loads(env_token)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception as e:
            print(f"[AUTH] Error con GOOGLE_TOKEN_JSON: {e}")

    # 4. Flujo OAuth desde credentials.json
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "No se encontró credentials.json ni token válido.\n"
            "Por favor:\n"
            "  1. Ve a https://console.cloud.google.com/\n"
            "  2. Crea un proyecto y habilita Calendar API y Gmail API.\n"
            "  3. Crea credenciales OAuth 2.0 (tipo: Desktop App).\n"
            "  4. Descarga credentials.json y colócalo en este directorio.\n"
            "  5. Vuelve a ejecutar el script."
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_FILE), SCOPES
    )
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    return creds


def _save_token(creds: Credentials) -> None:
    with open(TOKEN_FILE, "wb") as f:
        pickle.dump(creds, f)
    print("[AUTH] Token guardado correctamente.")
