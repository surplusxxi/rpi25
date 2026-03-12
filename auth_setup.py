#!/usr/bin/env python3
"""Script de autenticacion one-shot para drive_organizer."""
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
flow.autogenerate_code_verifier = False
flow.code_verifier = None

if len(sys.argv) == 1:
    # Paso 1: generar URL
    auth_url, _ = flow.authorization_url(prompt="consent")
    print("\n1. Abri este enlace en tu navegador:\n")
    print(f"   {auth_url}\n")
    print("2. Inicia sesion con laureanoalimenti@gmail.com")
    print("3. Acepta los permisos")
    print("4. Copia el codigo y ejecuta:")
    print(f"   python3 auth_setup.py <CODIGO>\n")
else:
    # Paso 2: canjear codigo por token
    code = sys.argv[1].strip()
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open("token.json", "w") as f:
        f.write(creds.to_json())
    print("token.json guardado correctamente. Ya podes correr drive_organizer.py")
