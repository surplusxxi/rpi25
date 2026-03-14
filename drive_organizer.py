#!/usr/bin/env python3
"""
Prompt Maestro — Ordenador de archivos sueltos en la raíz de Drive
Mueve archivos sueltos a las carpetas correctas, uno por uno con confirmación.
Owner: laureanoalimenti@gmail.com
"""

import os
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

OWNER_EMAIL = "laureanoalimenti@gmail.com"
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Carpetas destino y sus palabras clave
CARPETAS = {
    "DOCENCIA": [
        "docencia", "uns", "moodle", "tpi", "catedra", "materia", "sueldo uns",
        "guarani", "aduns", "programa", "aula", "clase", "cursada", "docente",
        "diplomatura", "seminario", "evaluacion", "estudiante", "inscripto"
    ],
    "DOCUMENTACION": [
        "cv", "curriculum", "certificado", "titulo", "dni", "analitico",
        "constancia", "legajo", "ioma", "matricula", "defuncion", "nacimiento",
        "partida", "documento", "baja", "examen", "academico"
    ],
    "FAMILIA": [
        "familia", "familiar", "hugo", "hijo", "hija", "papa", "mama",
        "alimenti", "eliseo", "toledo"
    ],
    "MILITANCIA": [
        "rs1", "ministerio", "politica", "region sanitaria", "gestion",
        "coresa", "informe rs", "nomina rs", "hospitales rs"
    ],
    "PROMETEUS XXI": [
        "prometeus", "twitter", "troll", "raspberry", "campaña", "digital",
        "redes", "bot", "cuenta"
    ],
    "SALUD": [
        "salud", "enfermeria", "enfermería", "paciente", "epidemio", "historia clinica",
        "laboratorio", "ecografia", "ecg", "vacuna", "vacunatorio", "internado",
        "uti", "hospital", "posta", "turno", "aps", "colectiva", "comunitaria",
        "domiciliaria", "reporte", "escuela", "rs1 vacun"
    ],
    "SANEAMIENTO": [
        "dengue", "larvario", "ovitrampas", "saneamiento", "ambiental", "hugo gonzalez",
        "entomologico", "bahia blanca", "municipio", "bahia", "bbca", "control ambiental",
        "fiscalizacion"
    ],
    "SAUCE SONNORO": [
        "sauce", "sonnoro", "sonoro", "musica", "composicion", "cancion"
    ],
    "UNMA HISTORIA": [
        "unma", "historia", "profesorado", "madres de plaza", "plaza de mayo"
    ],
}


def authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("[ERROR] token.json inválido. Corré organizar.py primero.")
            sys.exit(1)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def get_folder_id(service, name):
    """Obtiene el ID de una carpeta por nombre en la raíz."""
    result = service.files().list(
        q=f"name='{name}' and 'root' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)"
    ).execute()
    files = result.get("files", [])
    return files[0]["id"] if files else None


def suggest_folder(name):
    """Sugiere la carpeta destino según el nombre del archivo."""
    name_lower = name.lower()
    scores = {}
    for carpeta, keywords in CARPETAS.items():
        score = sum(1 for kw in keywords if kw in name_lower)
        if score > 0:
            scores[carpeta] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


def move_file(service, file_id, dest_folder_id):
    try:
        service.files().update(
            fileId=file_id,
            addParents=dest_folder_id,
            removeParents="root",
            fields="id, parents",
        ).execute()
        return True
    except HttpError as e:
        print(f"  [ERROR] No se pudo mover: {e}")
        return False


def main():
    print("\n╔══════════════════════════════════════════════════╗")
    print("║   PROMPT MAESTRO — Ordenar archivos sueltos      ║")
    print("╚══════════════════════════════════════════════════╝\n")

    service = authenticate()

    # Buscar archivos sueltos en la raíz (no carpetas)
    print("Buscando archivos sueltos en la raíz de tu Drive...\n")
    result = service.files().list(
        q="'root' in parents and mimeType!='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name, mimeType, modifiedTime)",
        pageSize=1000,
    ).execute()
    archivos = result.get("files", [])

    if not archivos:
        print("No hay archivos sueltos en la raíz. Todo está ordenado.")
        return

    print(f"Se encontraron {len(archivos)} archivos sueltos.\n")

    # Cargar IDs de carpetas destino
    folder_ids = {}
    for nombre in CARPETAS:
        fid = get_folder_id(service, nombre)
        if fid:
            folder_ids[nombre] = fid
        else:
            print(f"  [AVISO] Carpeta '{nombre}' no encontrada en tu Drive, se omitirá.")

    print()

    movidos = 0
    omitidos = 0
    sin_sugerencia = []

    for i, archivo in enumerate(archivos, 1):
        nombre = archivo.get("name", "?")
        sugerida = suggest_folder(nombre)

        if not sugerida or sugerida not in folder_ids:
            sin_sugerencia.append(nombre)
            continue

        print(f"[{i}/{len(archivos)}] '{nombre}'")
        print(f"         → Sugerida: {sugerida}/")
        resp = input("         Mover? [s=sí / n=no / c=cambiar carpeta]: ").strip().lower()

        if resp in ("s", "si", "sí", "y"):
            ok = move_file(service, archivo["id"], folder_ids[sugerida])
            if ok:
                print("         [OK] Movido.\n")
                movidos += 1
            else:
                omitidos += 1

        elif resp == "c":
            print("\n  Carpetas disponibles:")
            opciones = list(folder_ids.keys())
            for j, c in enumerate(opciones, 1):
                print(f"    {j}. {c}")
            sel = input("  Número de carpeta: ").strip()
            try:
                carpeta_elegida = opciones[int(sel) - 1]
                ok = move_file(service, archivo["id"], folder_ids[carpeta_elegida])
                if ok:
                    print(f"  [OK] Movido a {carpeta_elegida}/.\n")
                    movidos += 1
                else:
                    omitidos += 1
            except (ValueError, IndexError):
                print("  Opción inválida, se omite.\n")
                omitidos += 1

        else:
            print("         Omitido.\n")
            omitidos += 1

    print("\n" + "=" * 50)
    print(f"  Movidos:  {movidos}")
    print(f"  Omitidos: {omitidos}")
    if sin_sugerencia:
        print(f"\n  Sin sugerencia ({len(sin_sugerencia)} archivos):")
        for n in sin_sugerencia:
            print(f"    - {n}")
        print("\n  Estos quedaron en la raíz. Podés moverlos a mano.")
    print("=" * 50)
    print("\nListo. Hasta la próxima.")


if __name__ == "__main__":
    main()
