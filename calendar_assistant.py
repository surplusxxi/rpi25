#!/usr/bin/env python3
"""
Asistente Académico – Gmail + Google Calendar
Zona horaria: America/Argentina/Buenos_Aires
"""

import os
import base64
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ── Configuración ────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
]
TIMEZONE = "America/Argentina/Buenos_Aires"
TZ = ZoneInfo(TIMEZONE)

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# ── Autenticación ─────────────────────────────────────────────────────────────

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"No se encontró '{CREDENTIALS_FILE}'. "
                    "Descargá las credenciales OAuth2 desde Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


# ── Helpers de Calendar ───────────────────────────────────────────────────────

def dt_to_iso(year, month, day, hour, minute, tz=TIMEZONE):
    """Devuelve un dict RFC3339 para Google Calendar."""
    dt = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz))
    return {"dateTime": dt.isoformat(), "timeZone": tz}


def reminder_minutes(label: str) -> int:
    """Convierte etiqueta legible a minutos."""
    mapping = {
        "1 semana antes":  7 * 24 * 60,
        "3 días antes":    3 * 24 * 60,
        "1 día antes":     1 * 24 * 60,
        "24 horas antes":  1 * 24 * 60,
        "2 horas antes":   2 * 60,
        "30 minutos antes": 30,
        "08:00 el mismo día": 0,   # se maneja aparte si es necesario
    }
    return mapping.get(label, 60)


def build_reminders(labels):
    overrides = []
    for lbl in labels:
        mins = reminder_minutes(lbl)
        if mins > 0:
            overrides.append({"method": "popup", "minutes": mins})
            overrides.append({"method": "email", "minutes": mins})
    # eliminar duplicados
    seen = set()
    unique = []
    for r in overrides:
        key = (r["method"], r["minutes"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return {"useDefault": False, "overrides": unique}


def find_existing_event(service, calendar_id, summary, date_str):
    """
    Busca un evento con el mismo título en la fecha indicada.
    date_str: 'YYYY-MM-DD'
    Devuelve el evento o None.
    """
    time_min = f"{date_str}T00:00:00-03:00"
    time_max = f"{date_str}T23:59:59-03:00"
    result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    for ev in result.get("items", []):
        if ev.get("summary", "").strip().lower() == summary.strip().lower():
            return ev
    return None


def create_or_update_event(service, calendar_id, event_body, summary, date_str):
    """
    Si ya existe un evento con el mismo título en esa fecha → actualiza.
    Si no → crea uno nuevo.
    Devuelve (acción, evento).
    """
    existing = find_existing_event(service, calendar_id, summary, date_str)
    if existing:
        updated = service.events().update(
            calendarId=calendar_id,
            eventId=existing["id"],
            body={**existing, **event_body},
        ).execute()
        return "actualizado", updated
    else:
        created = service.events().insert(
            calendarId=calendar_id,
            body=event_body,
        ).execute()
        return "creado", created


# ── Definición de eventos ─────────────────────────────────────────────────────

SEMINARIO_LINKS = (
    "YouTube principal: https://www.youtube.com/c/EscueladegobiernoensaludFlorealFerrara\n"
    "Canal alternativo: https://www.youtube.com/@escueladegobiernoensaludff/featured\n"
    "Formulario diplomatura: https://forms.gle/QmN9so4e5uPDxM2Q9"
)

EVENTS = [
    # ── PARTE 1 — Clases del Seminario ────────────────────────────────────────
    {
        "summary": "Seminario Políticas Públicas en Salud – Clase 1",
        "date": (2026, 3, 4),
        "start_hour": (14, 0),
        "end_hour": (16, 0),
        "location": "YouTube – Escuela de Gobierno en Salud Floreal Ferrara",
        "description": (
            "Seminario transversal introductorio de Políticas Públicas de Salud "
            "de la Provincia de Buenos Aires.\n\n"
            "ACTIVIDAD\n"
            "Clase introductoria del seminario requerido para diplomaturas y cursos superiores.\n\n"
            "IMPORTANTE\n"
            "- La clase se transmite por YouTube.\n"
            "- Si no puedo verla en vivo queda grabada.\n"
            "- Aprobar el seminario y completar la preinscripción es requisito para "
            "continuar el proceso.\n"
            "- Aprobar no garantiza vacante definitiva.\n\n"
            "CONTENIDO ORIENTATIVO\n"
            "- Integralidad de políticas de salud\n"
            "- Gobierno en salud\n"
            "- Salud mental en transformación\n"
            "- Recursos estratégicos\n"
            "- Red de servicios de salud\n"
            "- Igualdad y diversidad\n"
            "- Plan Quinquenal 2022–2027\n"
            "- Gestión de fuerza laboral\n\n"
            "LINKS\n"
            + SEMINARIO_LINKS + "\n\n"
            "Diplomatura objetivo: Salud Internacional"
        ),
        "reminders": ["1 día antes", "2 horas antes", "30 minutos antes"],
    },
    {
        "summary": "Seminario Políticas Públicas en Salud – Clase 2",
        "date": (2026, 3, 11),
        "start_hour": (14, 0),
        "end_hour": (16, 0),
        "location": "YouTube – Escuela de Gobierno en Salud Floreal Ferrara",
        "description": (
            "Segunda clase del Seminario Transversal de Políticas Públicas en Salud.\n\n"
            "INDICACIONES\n"
            "- Ver transmisión en YouTube.\n"
            "- Si no puedo verla en vivo, revisar grabación.\n"
            "- Tomar apuntes para la evaluación final.\n\n"
            "LINKS\n"
            + SEMINARIO_LINKS + "\n\n"
            "Diplomatura objetivo: Salud Internacional"
        ),
        "reminders": ["1 día antes", "2 horas antes", "30 minutos antes"],
    },
    {
        "summary": "Seminario Políticas Públicas en Salud – Clase 3",
        "date": (2026, 3, 18),
        "start_hour": (14, 0),
        "end_hour": (16, 0),
        "location": "YouTube – Escuela de Gobierno en Salud Floreal Ferrara",
        "description": (
            "Última clase del Seminario Transversal de Políticas Públicas en Salud.\n\n"
            "LUEGO DEL SEMINARIO\n"
            "- Revisar correo.\n"
            "- Llegará evaluación multiple choice.\n"
            "- Fecha límite para completarla: 29/03/2026.\n\n"
            "REQUISITOS\n"
            "Aprobar la evaluación para matriculación definitiva.\n\n"
            "LINKS\n"
            + SEMINARIO_LINKS + "\n\n"
            "Diplomatura objetivo: Salud Internacional"
        ),
        "reminders": ["1 día antes", "2 horas antes", "30 minutos antes"],
    },
    {
        "summary": "Recordatorio – Completar evaluación Seminario Políticas Públicas en Salud",
        "date": (2026, 3, 25),
        "start_hour": (10, 0),
        "end_hour": (10, 30),
        "location": "Revisar mail / Google Forms",
        "description": (
            "Recordatorio para completar la evaluación final del seminario.\n\n"
            "TAREAS\n"
            "- Revisar correo.\n"
            "- Localizar formulario de evaluación.\n"
            "- Completar la evaluación antes del 29/03/2026.\n\n"
            "IMPORTANTE\n"
            "- Evaluación obligatoria.\n"
            "- Fecha límite: 29/03/2026.\n\n"
            "LINKS\n"
            "Formulario: https://forms.gle/QmN9so4e5uPDxM2Q9\n"
            "YouTube: https://www.youtube.com/c/EscueladegobiernoensaludFlorealFerrara\n\n"
            "Diplomatura objetivo: Salud Internacional"
        ),
        "reminders": ["3 días antes", "1 día antes", "08:00 el mismo día"],
    },
    # ── PARTE 2 — Eventos de evaluación (estimados) ───────────────────────────
    {
        "summary": "Abrir evaluación – Seminario Políticas Públicas en Salud",
        "date": (2026, 3, 19),
        "start_hour": (9, 0),
        "end_hour": (9, 30),
        "location": "Revisar mail / Google Forms",
        "description": (
            "Apertura estimada de la evaluación multiple choice del Seminario "
            "Transversal de Políticas Públicas en Salud.\n\n"
            "TAREAS\n"
            "- Revisar correo para el enlace oficial de la evaluación.\n"
            "- Abrir el formulario y verificar instrucciones.\n\n"
            "IMPORTANTE\n"
            "Fecha límite: 29/03/2026.\n\n"
            "LINKS\n"
            + SEMINARIO_LINKS + "\n\n"
            "Diplomatura objetivo: Salud Internacional"
        ),
        "reminders": ["1 semana antes", "3 días antes", "1 día antes", "2 horas antes"],
    },
    {
        "summary": "Completar evaluación – Seminario Políticas Públicas en Salud",
        "date": (2026, 3, 24),
        "start_hour": (18, 0),
        "end_hour": (19, 0),
        "location": "Google Forms",
        "description": (
            "Sesión reservada para completar la evaluación multiple choice del seminario.\n\n"
            "TAREAS\n"
            "- Acceder al formulario de evaluación.\n"
            "- Completar todas las preguntas.\n"
            "- Verificar envío exitoso.\n\n"
            "IMPORTANTE\n"
            "Fecha límite: 29/03/2026.\n\n"
            "LINKS\n"
            "Formulario: https://forms.gle/QmN9so4e5uPDxM2Q9\n\n"
            "Diplomatura objetivo: Salud Internacional"
        ),
        "reminders": ["1 semana antes", "3 días antes", "1 día antes", "2 horas antes"],
    },
    {
        "summary": "ÚLTIMO DÍA – Evaluación Seminario Políticas Públicas en Salud",
        "date": (2026, 3, 29),
        "start_hour": (12, 0),
        "end_hour": (12, 30),
        "location": "Google Forms",
        "description": (
            "¡HOY ES EL ÚLTIMO DÍA para enviar la evaluación del seminario!\n\n"
            "TAREAS URGENTES\n"
            "- Verificar si la evaluación fue enviada correctamente.\n"
            "- Si no fue enviada: ingresar al formulario y completarla AHORA.\n\n"
            "CONSECUENCIAS\n"
            "No completar la evaluación implica no poder matricularse en la diplomatura.\n\n"
            "LINKS\n"
            "Formulario: https://forms.gle/QmN9so4e5uPDxM2Q9\n\n"
            "Diplomatura objetivo: Salud Internacional"
        ),
        "reminders": ["1 semana antes", "3 días antes", "1 día antes", "2 horas antes"],
    },
    # ── PARTE 3 — UPSO ────────────────────────────────────────────────────────
    {
        "summary": "Definir cronograma tentativo UPSO – Teoría Antropológica de la Salud",
        "date": (2026, 3, 13),
        "start_hour": (10, 0),
        "end_hour": (10, 30),
        "location": "SIRAD – UPSO Monte Hermoso",
        "description": (
            "Tarea previa al inicio de cursada.\n\n"
            "ACCIÓN\n"
            "Ingresar a SIRAD y definir/consultar el cronograma tentativo de la materia "
            "Teoría Antropológica de la Salud.\n\n"
            "MATERIA\n"
            "Teoría Antropológica de la Salud\n"
            "Carrera: Enfermería – UPSO Monte Hermoso\n\n"
            "EQUIPO DOCENTE\n"
            "- Juan Pablo Pardias\n"
            "- Lauriano Alimenti\n"
            "- Auxiliar: Fernando Sandoval"
        ),
        "reminders": ["1 día antes", "2 horas antes"],
    },
    {
        "summary": "Inicio de Teoría Antropológica de la Salud – UPSO Monte Hermoso",
        "date": (2026, 3, 16),
        "start_hour": (8, 0),
        "end_hour": (10, 0),
        "location": "UPSO Monte Hermoso",
        "description": (
            "Inicio de cursada del primer cuatrimestre.\n\n"
            "MATERIA\n"
            "Teoría Antropológica de la Salud\n"
            "Carrera: Enfermería – UPSO Monte Hermoso\n\n"
            "EQUIPO DOCENTE\n"
            "- Juan Pablo Pardias\n"
            "- Lauriano Alimenti\n"
            "- Auxiliar: Fernando Sandoval\n\n"
            "TAREAS EN ESTA FECHA\n"
            "- Confirmar cronograma y modalidad de cursada.\n"
            "- Consultar al docente sobre metodología de trabajo.\n"
            "- Verificar plataforma virtual utilizada."
        ),
        "reminders": ["24 horas antes", "2 horas antes", "30 minutos antes"],
    },
    {
        "summary": "Confirmar cronograma y modalidad – Teoría Antropológica de la Salud",
        "date": (2026, 3, 16),
        "start_hour": (10, 0),
        "end_hour": (10, 30),
        "location": "UPSO Monte Hermoso / SIRAD",
        "description": (
            "Confirmar cronograma definitivo y modalidad de cursada "
            "de Teoría Antropológica de la Salud.\n\n"
            "ACCIONES\n"
            "- Verificar horarios definitivos en SIRAD.\n"
            "- Confirmar modalidad: presencial / virtual / mixta.\n"
            "- Registrar datos en agenda.\n\n"
            "EQUIPO DOCENTE\n"
            "- Juan Pablo Pardias\n"
            "- Lauriano Alimenti\n"
            "- Auxiliar: Fernando Sandoval"
        ),
        "reminders": ["1 día antes"],
    },
]


# ── Búsqueda en Gmail ─────────────────────────────────────────────────────────

GMAIL_QUERIES = [
    "Seminario Transversal Políticas Públicas en Salud",
    "Escuela de Gobierno en Salud Floreal Ferrara evaluación",
    "cuestionario multiple choice diplomatura vacante",
    "19/03 OR 29/03 seminario salud evaluación",
]


def search_gmail(gmail_service):
    """
    Busca en Gmail los correos relacionados con el seminario.
    Devuelve lista de dicts con asunto, remitente, fecha, snippet y links.
    """
    found_messages = []
    query = " OR ".join([f'({q})' for q in GMAIL_QUERIES])
    combined_query = (
        "(\"Seminario Transversal\" OR \"Políticas Públicas en Salud\" OR "
        "\"Floreal Ferrara\" OR \"evaluación seminario\" OR "
        "\"multiple choice\" OR \"diplomatura vacante\") "
        "after:2026/01/01"
    )
    try:
        result = gmail_service.users().messages().list(
            userId="me",
            q=combined_query,
            maxResults=20,
        ).execute()
        messages = result.get("messages", [])
        for msg_ref in messages:
            msg = gmail_service.users().messages().get(
                userId="me",
                id=msg_ref["id"],
                format="full",
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            subject = headers.get("Subject", "(sin asunto)")
            sender = headers.get("From", "(remitente desconocido)")
            date = headers.get("Date", "(fecha desconocida)")
            snippet = msg.get("snippet", "")
            # Extraer links del body
            body_links = extract_links_from_message(msg)
            found_messages.append({
                "id": msg_ref["id"],
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": snippet,
                "links": body_links,
            })
    except HttpError as e:
        print(f"  [ERROR Gmail] {e}")
    return found_messages


def extract_links_from_message(msg):
    """Extrae URLs del cuerpo del mensaje."""
    links = set()
    url_pattern = re.compile(r'https?://[^\s\'"<>]+')

    def decode_part(part):
        data = part.get("body", {}).get("data", "")
        if data:
            try:
                decoded = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
                for url in url_pattern.findall(decoded):
                    links.add(url.rstrip(".,;)>"))
            except Exception:
                pass
        for sub in part.get("parts", []):
            decode_part(sub)

    decode_part(msg.get("payload", {}))
    return list(links)


# ── Ejecución principal ───────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  ASISTENTE ACADÉMICO – Google Calendar + Gmail")
    print(f"  Zona horaria: {TIMEZONE}")
    print("=" * 65)

    # Autenticar
    try:
        creds = get_credentials()
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("\nInstrucciones:")
        print("  1. Ir a https://console.cloud.google.com/")
        print("  2. Crear credenciales OAuth2 (tipo: aplicación de escritorio)")
        print("  3. Descargar el archivo JSON y guardarlo como 'credentials.json'")
        print("  4. Volver a ejecutar este script")
        return

    calendar_service = build("calendar", "v3", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)

    calendar_id = "primary"
    results = {
        "creados": [],
        "actualizados": [],
        "errores": [],
        "gmail_encontrados": [],
    }

    # ── Crear/actualizar eventos de Calendar ──────────────────────────────────
    print("\n── GOOGLE CALENDAR ─────────────────────────────────────────────")
    for ev_def in EVENTS:
        year, month, day = ev_def["date"]
        sh, sm = ev_def["start_hour"]
        eh, em = ev_def["end_hour"]
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        summary = ev_def["summary"]

        body = {
            "summary": summary,
            "location": ev_def.get("location", ""),
            "description": ev_def.get("description", ""),
            "start": dt_to_iso(year, month, day, sh, sm),
            "end": dt_to_iso(year, month, day, eh, em),
            "reminders": build_reminders(ev_def.get("reminders", [])),
        }

        try:
            action, event = create_or_update_event(
                calendar_service, calendar_id, body, summary, date_str
            )
            link = event.get("htmlLink", "")
            print(f"  [{action.upper()}] {summary}")
            print(f"           {date_str} {sh:02d}:{sm:02d}–{eh:02d}:{em:02d}")
            print(f"           {link}")
            results[f"{action}s"].append({
                "summary": summary,
                "date": date_str,
                "time": f"{sh:02d}:{sm:02d}–{eh:02d}:{em:02d}",
                "link": link,
            })
        except HttpError as e:
            msg = f"[ERROR] {summary} ({date_str}): {e}"
            print(f"  {msg}")
            results["errores"].append(msg)

    # ── Búsqueda en Gmail ─────────────────────────────────────────────────────
    print("\n── GMAIL – Búsqueda de correos del seminario ───────────────────")
    found_emails = search_gmail(gmail_service)
    results["gmail_encontrados"] = found_emails

    if found_emails:
        for i, em in enumerate(found_emails, 1):
            print(f"\n  [{i}] Asunto : {em['subject']}")
            print(f"       De     : {em['from']}")
            print(f"       Fecha  : {em['date']}")
            print(f"       Avance : {em['snippet'][:120]}...")
            if em["links"]:
                print("       Links  :")
                for lnk in em["links"][:5]:
                    print(f"                {lnk}")
    else:
        print("  No se encontraron correos relacionados con el seminario.")
        print("  (Puede que aún no hayan llegado o que la búsqueda deba ajustarse.)")

    # ── Resumen final ─────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  RESUMEN FINAL")
    print("=" * 65)
    print(f"\n  Correos encontrados en Gmail : {len(results['gmail_encontrados'])}")
    print(f"  Eventos CREADOS              : {len(results['creados'])}")
    print(f"  Eventos ACTUALIZADOS         : {len(results['actualizados'])}")
    print(f"  Errores                      : {len(results['errores'])}")

    all_events = results["creados"] + results["actualizados"]
    if all_events:
        print("\n  DETALLE DE EVENTOS:")
        for ev in sorted(all_events, key=lambda x: x["date"]):
            print(f"    • {ev['date']} {ev['time']}  →  {ev['summary']}")

    if results["errores"]:
        print("\n  ERRORES:")
        for err in results["errores"]:
            print(f"    ✗ {err}")

    if results["gmail_encontrados"]:
        print("\n  CORREOS ENCONTRADOS:")
        for em in results["gmail_encontrados"]:
            print(f"    • [{em['date']}] {em['subject']} — {em['from']}")

    print("\n" + "=" * 65)
    print("  Proceso completado.")
    print("=" * 65)


if __name__ == "__main__":
    main()
