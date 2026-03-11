#!/usr/bin/env python3
"""
Prompt Maestro — Organizador de Google Drive
Reorganización segura, incremental y retomable entre sesiones.
Owner objetivo: laureanoalimenti@gmail.com
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ─── CONSTANTES ────────────────────────────────────────────────────────────────

OWNER_EMAIL = "laureanoalimenti@gmail.com"
CHECKPOINT_FILENAME = "drive_organizer_checkpoint.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Carpetas de terceros: nunca tocar
THIRD_PARTY_OWNERS = {
    "ateneonksexta", "rosmarcoli", "dpcomunicacionms", "sgamminijuliana",
    "vacunadoreseventualesrs1", "regsanuno", "prensaregionsanitariauno",
    "saludcampora", "flor.reising", "nelsongimenez.8", "comunicacionpennabb",
}

# Carpetas ya bien organizadas: respetar
PROTECTED_FOLDERS = {
    "1. Documentación Personal",
    "2. Títulos y Certificados",
    "3. Antecedentes profesionales y docentes",
}

# Estructura destino
DESTINATION_FOLDERS = [
    "_REVISAR",
    "_ARCHIVO_HISTORICO",
    "2020_Salud_Publica", "2021_Salud_Publica", "2022_Salud_Publica",
    "2023_Salud_Publica", "2024_Salud_Publica", "2025_Salud_Publica",
    "2026_Salud_Publica",
]

YEAR_THEMES = ["Docencia_UNS", "Municipio_BBca", "Politica", "Personal", "Musica", "Proyectos_Tech"]
YEARS = list(range(2014, 2027))

CHECKPOINT_TEMPLATE = {
    "ultima_actualizacion": "",
    "fase_actual": 1,
    "fase_descripcion": "Mapeo completo",
    "carpetas_procesadas": [],
    "carpetas_pendientes": [],
    "archivos_movidos": [],
    "archivos_en_revisar": [],
    "permisos_revocados": [],
    "permisos_pendientes_revision": [],
    "notas": "",
}


# ─── AUTENTICACIÓN ─────────────────────────────────────────────────────────────

def authenticate() -> object:
    """Autentica con Google Drive API usando OAuth2."""
    creds = None
    token_path = "token.json"
    credentials_path = "credentials.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                print("\n[ERROR] No se encontró credentials.json")
                print("  1. Ir a https://console.cloud.google.com/")
                print("  2. Crear un proyecto → habilitar Google Drive API")
                print("  3. Crear credenciales OAuth 2.0 (Desktop app)")
                print("  4. Descargar como 'credentials.json' en este directorio")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# ─── CHECKPOINT ────────────────────────────────────────────────────────────────

class CheckpointManager:
    def __init__(self, service):
        self.service = service
        self.checkpoint_id: Optional[str] = None
        self.data = dict(CHECKPOINT_TEMPLATE)

    def find_checkpoint_in_drive(self) -> Optional[str]:
        """Busca el archivo checkpoint en la raíz de Drive."""
        try:
            results = self.service.files().list(
                q=f"name='{CHECKPOINT_FILENAME}' and 'root' in parents and trashed=false",
                fields="files(id, name)",
                spaces="drive",
            ).execute()
            files = results.get("files", [])
            return files[0]["id"] if files else None
        except HttpError as e:
            print(f"[WARN] No se pudo buscar checkpoint: {e}")
            return None

    def load(self) -> bool:
        """Carga el checkpoint desde Drive. Retorna True si existe."""
        file_id = self.find_checkpoint_in_drive()
        if not file_id:
            return False

        try:
            content = self.service.files().get_media(fileId=file_id).execute()
            self.data = json.loads(content.decode("utf-8"))
            self.checkpoint_id = file_id
            return True
        except (HttpError, json.JSONDecodeError) as e:
            print(f"[WARN] Checkpoint encontrado pero no se pudo leer: {e}")
            return False

    def save(self):
        """Guarda el checkpoint en Drive (crea o actualiza)."""
        self.data["ultima_actualizacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        content = json.dumps(self.data, ensure_ascii=False, indent=2).encode("utf-8")

        from googleapiclient.http import MediaInMemoryUpload
        media = MediaInMemoryUpload(content, mimetype="application/json")

        try:
            if self.checkpoint_id:
                self.service.files().update(
                    fileId=self.checkpoint_id,
                    media_body=media,
                ).execute()
            else:
                file_meta = {
                    "name": CHECKPOINT_FILENAME,
                    "parents": ["root"],
                }
                result = self.service.files().create(
                    body=file_meta,
                    media_body=media,
                    fields="id",
                ).execute()
                self.checkpoint_id = result["id"]
            print(f"\n[✓] Checkpoint guardado ({self.data['ultima_actualizacion']})")
        except HttpError as e:
            print(f"[ERROR] No se pudo guardar checkpoint: {e}")


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def confirm(prompt: str) -> bool:
    """Pide confirmación al usuario."""
    while True:
        resp = input(f"\n{prompt} [s/n]: ").strip().lower()
        if resp in ("s", "si", "sí", "y", "yes"):
            return True
        if resp in ("n", "no"):
            return False


def paginate_files(service, query: str, fields: str = "files(id,name,mimeType,owners,modifiedTime,parents)") -> list:
    """Recupera todos los archivos de una query con paginación."""
    all_files = []
    page_token = None
    while True:
        kwargs = dict(q=query, fields=f"nextPageToken,{fields}", spaces="drive", pageSize=1000)
        if page_token:
            kwargs["pageToken"] = page_token
        try:
            result = service.files().list(**kwargs).execute()
        except HttpError as e:
            print(f"[ERROR] Error al listar archivos: {e}")
            break
        all_files.extend(result.get("files", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return all_files


def is_owner(file_item: dict) -> bool:
    """Verifica que el owner del archivo sea el correo configurado."""
    owners = file_item.get("owners", [])
    return any(o.get("emailAddress", "").lower() == OWNER_EMAIL.lower() for o in owners)


def detect_year(name: str, modified: str) -> Optional[int]:
    """Intenta detectar el año a partir del nombre o fecha de modificación."""
    import re
    match = re.search(r"(20[1-2][0-9])", name)
    if match:
        return int(match.group(1))
    if modified:
        try:
            return int(modified[:4])
        except ValueError:
            pass
    return None


def suggest_folder(name: str, modified: str) -> str:
    """Sugiere carpeta destino basada en nombre y fecha."""
    name_lower = name.lower()
    year = detect_year(name, modified)

    # Temas
    theme = None
    if any(k in name_lower for k in ["docencia", "uns", "moodle", "tpi", "catedra", "materia"]):
        theme = "Docencia_UNS"
    elif any(k in name_lower for k in ["dengue", "municipio", "bbca", "bahia", "medio ambiente"]):
        theme = "Municipio_BBca"
    elif any(k in name_lower for k in ["rs1", "ministerio", "politica", "region sanitaria"]):
        theme = "Politica"
    elif any(k in name_lower for k in ["personal", "cv", "titulo", "certificado", "dni"]):
        theme = "Personal"
    elif any(k in name_lower for k in ["musica", "sauce", "sonoro", "composicion"]):
        theme = "Musica"
    elif any(k in name_lower for k in ["tech", "app", "codigo", "full power", "python", "js", "web"]):
        theme = "Proyectos_Tech"
    elif any(k in name_lower for k in ["salud", "enfermeria", "domiciliaria", "paciente", "epidemio"]):
        theme = "Salud_Publica"

    if year and year < 2020:
        return "_ARCHIVO_HISTORICO"
    if year and theme:
        return f"{year}_{theme}"
    if year and not theme:
        return f"{year}_Salud_Publica"  # default temático

    return "_REVISAR"


# ─── FASE 1: MAPEO ─────────────────────────────────────────────────────────────

def fase1_mapeo(service, checkpoint: CheckpointManager):
    """Lista todos los archivos propios y genera reporte."""
    print("\n" + "=" * 60)
    print("FASE 1 — MAPEO COMPLETO (no se toca nada)")
    print("=" * 60)
    print("Buscando todos tus archivos en Drive...")

    own_files = paginate_files(
        service,
        query=f"'{OWNER_EMAIL}' in owners and trashed=false",
    )

    folders = [f for f in own_files if f.get("mimeType") == "application/vnd.google-apps.folder"]
    files = [f for f in own_files if f.get("mimeType") != "application/vnd.google-apps.folder"]

    # Detectar años y temas
    years_found: dict[int, int] = {}
    themes_found: dict[str, int] = {}
    name_counts: dict[str, int] = {}

    for f in own_files:
        name = f.get("name", "")
        modified = f.get("modifiedTime", "")
        year = detect_year(name, modified)
        if year:
            years_found[year] = years_found.get(year, 0) + 1
        suggested = suggest_folder(name, modified)
        theme = suggested.split("_", 1)[-1] if "_" in suggested else suggested
        themes_found[theme] = themes_found.get(theme, 0) + 1
        name_counts[name] = name_counts.get(name, 0) + 1

    duplicates = {n: c for n, c in name_counts.items() if c > 1}

    print(f"\n📊 REPORTE DE MAPEO")
    print(f"  Total archivos propios:  {len(files)}")
    print(f"  Total carpetas propias:  {len(folders)}")
    print(f"  Años detectados:         {sorted(years_found.keys())}")
    print(f"\n  Distribución por tema (estimada):")
    for theme, count in sorted(themes_found.items(), key=lambda x: -x[1]):
        print(f"    {theme:<30} {count} items")
    print(f"\n  Posibles duplicados de nombre: {len(duplicates)}")
    if duplicates:
        for name, count in list(duplicates.items())[:10]:
            print(f"    '{name}' aparece {count} veces")
        if len(duplicates) > 10:
            print(f"    ... y {len(duplicates)-10} más")

    # Guardar en checkpoint
    checkpoint.data["fase_actual"] = 1
    checkpoint.data["fase_descripcion"] = "Mapeo completo"
    checkpoint.data["carpetas_pendientes"] = [f["id"] for f in folders]
    checkpoint.data["notas"] = (
        f"Total archivos: {len(files)}, carpetas: {len(folders)}, "
        f"años: {sorted(years_found.keys())}"
    )
    checkpoint.save()

    print(f"\nMapeo guardado en checkpoint.")
    if not confirm("¿Continuar con FASE 2 (Propuesta)?"):
        print("Ok. Retomá en cualquier momento con: python drive_organizer.py")
        sys.exit(0)

    return own_files, folders, files


# ─── FASE 2: PROPUESTA ─────────────────────────────────────────────────────────

def fase2_propuesta(service, checkpoint: CheckpointManager, own_files: list):
    """Genera propuesta de reorganización sin ejecutar nada."""
    print("\n" + "=" * 60)
    print("FASE 2 — PROPUESTA DE REORGANIZACIÓN")
    print("=" * 60)

    plan: dict[str, list] = {}
    revisar: list[dict] = []

    for f in own_files:
        name = f.get("name", "")
        modified = f.get("modifiedTime", "")
        dest = suggest_folder(name, modified)
        if dest == "_REVISAR":
            revisar.append({"id": f["id"], "name": name, "reason": "Año o tema ambiguo"})
        plan.setdefault(dest, []).append(name)

    print("\n📋 PROPUESTA DE MOVIMIENTOS:")
    for dest, items in sorted(plan.items()):
        print(f"\n  📁 {dest}/  ({len(items)} items)")
        for item in items[:5]:
            print(f"      - {item}")
        if len(items) > 5:
            print(f"      ... y {len(items)-5} más")

    print(f"\n  📁 _REVISAR/  ({len(revisar)} items — sin contexto claro)")
    for item in revisar[:10]:
        print(f"      - {item['name']}")
    if len(revisar) > 10:
        print(f"      ... y {len(revisar)-10} más")

    checkpoint.data["fase_actual"] = 2
    checkpoint.data["fase_descripcion"] = "Propuesta generada"
    checkpoint.data["archivos_en_revisar"] = [r["id"] for r in revisar]
    checkpoint.save()

    print("\n[!] No se ejecutó ningún movimiento todavía.")
    resp = input('\nEscribí "APROBADO" para continuar con la ejecución: ').strip().upper()
    if resp != "APROBADO":
        print("Entendido. Guardé la propuesta. Volvé cuando quieras continuar.")
        sys.exit(0)

    return plan, revisar


# ─── FASE 3: EJECUCIÓN INCREMENTAL ─────────────────────────────────────────────

def get_or_create_folder(service, name: str, parent_id: str = "root") -> str:
    """Obtiene o crea una carpeta en Drive."""
    query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def move_file(service, file_id: str, dest_folder_id: str, current_parents: list) -> bool:
    """Mueve un archivo a la carpeta destino."""
    try:
        service.files().update(
            fileId=file_id,
            addParents=dest_folder_id,
            removeParents=",".join(current_parents),
            fields="id, parents",
        ).execute()
        return True
    except HttpError as e:
        print(f"  [ERROR] No se pudo mover: {e}")
        return False


def fase3_ejecucion(service, checkpoint: CheckpointManager, own_files: list):
    """Ejecuta movimientos de a una carpeta fuente por vez."""
    print("\n" + "=" * 60)
    print("FASE 3 — EJECUCIÓN INCREMENTAL")
    print("=" * 60)

    # Agrupar archivos por carpeta fuente (parent)
    by_parent: dict[str, list] = {}
    for f in own_files:
        parents = f.get("parents", [])
        parent_key = parents[0] if parents else "root"
        by_parent.setdefault(parent_key, []).append(f)

    processed = set(checkpoint.data.get("carpetas_procesadas", []))
    pending = [p for p in by_parent.keys() if p not in processed]

    print(f"\nCarpetas fuente a procesar: {len(pending)}")

    for parent_id in pending:
        files_in_folder = by_parent[parent_id]
        print(f"\n{'─'*50}")
        print(f"Procesando carpeta: {parent_id} ({len(files_in_folder)} items)")

        moved = []
        sent_to_revisar = []

        for f in files_in_folder:
            name = f.get("name", "")
            modified = f.get("modifiedTime", "")
            file_id = f["id"]
            current_parents = f.get("parents", [])

            # No tocar carpetas ya protegidas
            if name in PROTECTED_FOLDERS:
                print(f"  [SKIP] '{name}' — carpeta protegida")
                continue

            dest = suggest_folder(name, modified)
            dest_folder_id = get_or_create_folder(service, dest)

            print(f"  → '{name}'  →  {dest}/")

            ok = move_file(service, file_id, dest_folder_id, current_parents)
            if ok:
                if dest == "_REVISAR":
                    sent_to_revisar.append(name)
                    if file_id not in checkpoint.data["archivos_en_revisar"]:
                        checkpoint.data["archivos_en_revisar"].append(file_id)
                else:
                    moved.append(name)
                    checkpoint.data["archivos_movidos"].append({"id": file_id, "name": name, "dest": dest})

        print(f"\n  Movidos: {len(moved)}, enviados a _REVISAR: {len(sent_to_revisar)}")

        checkpoint.data["carpetas_procesadas"].append(parent_id)
        if parent_id in checkpoint.data["carpetas_pendientes"]:
            checkpoint.data["carpetas_pendientes"].remove(parent_id)
        checkpoint.data["fase_actual"] = 3
        checkpoint.data["fase_descripcion"] = f"Ejecución — último procesado: {parent_id}"
        checkpoint.save()

        if not confirm("¿Continuar con la siguiente carpeta?"):
            remaining = len(pending) - len(checkpoint.data["carpetas_procesadas"])
            print(f"Pausado. Quedan ~{remaining} carpetas. Retomá cuando quieras.")
            sys.exit(0)

    print("\n[✓] FASE 3 completada. Todos los archivos propios fueron procesados.")
    checkpoint.data["fase_actual"] = 4
    checkpoint.data["fase_descripcion"] = "Ejecución completada"
    checkpoint.save()


# ─── FASE 4: REVISIÓN DE _REVISAR ──────────────────────────────────────────────

def fase4_revisar(service, checkpoint: CheckpointManager):
    """Muestra archivos en _REVISAR de a grupos de 10 para decisión manual."""
    print("\n" + "=" * 60)
    print("FASE 4 — REVISIÓN DE _REVISAR/")
    print("=" * 60)

    revisar_files = paginate_files(
        service,
        query=f"'{OWNER_EMAIL}' in owners and trashed=false",
        fields="files(id,name,mimeType,owners,modifiedTime,parents)",
    )

    # Filtrar solo los que están en _REVISAR
    revisar_folder_results = service.files().list(
        q=f"name='_REVISAR' and '{OWNER_EMAIL}' in owners and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id)",
    ).execute()
    revisar_folders = [f["id"] for f in revisar_folder_results.get("files", [])]

    in_revisar = [
        f for f in revisar_files
        if any(p in revisar_folders for p in f.get("parents", []))
    ]

    if not in_revisar:
        print("No hay archivos en _REVISAR. ¡Todo en orden!")
        return

    print(f"\nArchivos en _REVISAR: {len(in_revisar)}")
    print("Se mostrarán de a 10. Para cada uno podés: mover a una carpeta específica o dejar.")

    for i in range(0, len(in_revisar), 10):
        batch = in_revisar[i:i+10]
        print(f"\n--- Grupo {i//10 + 1} ---")
        for j, f in enumerate(batch, start=i+1):
            name = f.get("name", "?")
            modified = f.get("modifiedTime", "?")[:10]
            suggested = suggest_folder(name, modified)
            print(f"  {j}. '{name}' (mod: {modified}) → sugerido: {suggested}")

        if not confirm("¿Continuar con el siguiente grupo?"):
            print("Pausado en FASE 4. Retomá cuando quieras.")
            sys.exit(0)

    checkpoint.data["fase_actual"] = 5
    checkpoint.data["fase_descripcion"] = "Revisión _REVISAR completada"
    checkpoint.save()


# ─── FASE 5: LIMPIEZA DE PERMISOS ──────────────────────────────────────────────

def fase5_permisos(service, checkpoint: CheckpointManager):
    """Lista y permite revocar permisos de archivos propios compartidos con externos."""
    print("\n" + "=" * 60)
    print("FASE 5 — LIMPIEZA DE PERMISOS COMPARTIDOS")
    print("=" * 60)
    print("Buscando archivos propios con acceso externo...")

    own_files = paginate_files(
        service,
        query=f"'{OWNER_EMAIL}' in owners and trashed=false",
        fields="files(id,name,permissions)",
    )

    shared: list[dict] = []
    for f in own_files:
        perms = f.get("permissions", [])
        external = [
            p for p in perms
            if p.get("emailAddress", "").lower() != OWNER_EMAIL.lower()
            and p.get("type") != "anyone"
        ]
        if external:
            shared.append({"file": f, "external_perms": external})

    if not shared:
        print("No se encontraron archivos propios con acceso externo.")
        return

    print(f"\nArchivos propios con acceso externo: {len(shared)}")

    for i in range(0, len(shared), 10):
        batch = shared[i:i+10]
        print(f"\n--- Grupo {i//10 + 1} ---")
        for item in batch:
            name = item["file"].get("name", "?")
            print(f"  📄 '{name}'")
            for p in item["external_perms"]:
                email = p.get("emailAddress", "?")
                role = p.get("role", "?")
                print(f"      → {email} ({role})")

        if confirm("¿Revocar permisos de ESTE grupo?"):
            for item in batch:
                file_id = item["file"]["id"]
                for p in item["external_perms"]:
                    perm_id = p.get("id")
                    email = p.get("emailAddress", "?")
                    try:
                        service.permissions().delete(fileId=file_id, permissionId=perm_id).execute()
                        print(f"  [✓] Revocado: '{item['file']['name']}' — {email}")
                        checkpoint.data["permisos_revocados"].append(
                            {"file": item["file"]["name"], "email": email}
                        )
                    except HttpError as e:
                        print(f"  [ERROR] No se pudo revocar: {e}")
            checkpoint.save()
        else:
            for item in batch:
                for p in item["external_perms"]:
                    checkpoint.data["permisos_pendientes_revision"].append(
                        {"file": item["file"]["name"], "email": p.get("emailAddress")}
                    )
            checkpoint.save()

        if i + 10 < len(shared):
            if not confirm("¿Continuar con el siguiente grupo?"):
                print("Pausado en FASE 5.")
                sys.exit(0)

    checkpoint.data["fase_actual"] = 5
    checkpoint.data["fase_descripcion"] = "Limpieza de permisos completada"
    checkpoint.save()
    print("\n[✓] FASE 5 completada.")


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("\n╔══════════════════════════════════════════════════╗")
    print("║       PROMPT MAESTRO — Organizador Drive         ║")
    print(f"║       Owner: {OWNER_EMAIL:<35}║")
    print("╚══════════════════════════════════════════════════╝")

    service = authenticate()
    checkpoint = CheckpointManager(service)

    # Verificar checkpoint previo
    if checkpoint.load():
        print(f"\n[✓] Checkpoint encontrado:")
        print(f"    Última actualización:  {checkpoint.data['ultima_actualizacion']}")
        print(f"    Fase actual:           {checkpoint.data['fase_actual']} — {checkpoint.data['fase_descripcion']}")
        print(f"    Carpetas procesadas:   {len(checkpoint.data['carpetas_procesadas'])}")
        print(f"    Carpetas pendientes:   {len(checkpoint.data['carpetas_pendientes'])}")
        print(f"    Archivos movidos:      {len(checkpoint.data['archivos_movidos'])}")
        print(f"    En _REVISAR:           {len(checkpoint.data['archivos_en_revisar'])}")
        if checkpoint.data.get("notas"):
            print(f"    Notas:                 {checkpoint.data['notas']}")

        fase = checkpoint.data["fase_actual"]
        if not confirm(f"\nRetomar desde FASE {fase} — {checkpoint.data['fase_descripcion']}?"):
            if not confirm("¿Empezar desde FASE 1 (mapeo completo)?"):
                print("Saliendo. Hasta pronto.")
                sys.exit(0)
            checkpoint.data = dict(CHECKPOINT_TEMPLATE)
            fase = 1
    else:
        print("\n[i] No se encontró checkpoint previo. Iniciando desde FASE 1.")
        fase = 1

    # Ejecutar fases según estado
    own_files = None

    if fase <= 1:
        own_files, _, _ = fase1_mapeo(service, checkpoint)
        fase = 2

    if fase <= 2:
        if own_files is None:
            own_files = paginate_files(service, f"'{OWNER_EMAIL}' in owners and trashed=false")
        fase2_propuesta(service, checkpoint, own_files)
        fase = 3

    if fase <= 3:
        if own_files is None:
            own_files = paginate_files(service, f"'{OWNER_EMAIL}' in owners and trashed=false")
        fase3_ejecucion(service, checkpoint, own_files)
        fase = 4

    if fase <= 4:
        fase4_revisar(service, checkpoint)
        fase = 5

    if fase <= 5:
        fase5_permisos(service, checkpoint)

    print("\n[✓] ¡Todas las fases completadas! Tu Drive está organizado.")
    checkpoint.data["fase_actual"] = 6
    checkpoint.data["fase_descripcion"] = "Proceso completo"
    checkpoint.save()


if __name__ == "__main__":
    main()
