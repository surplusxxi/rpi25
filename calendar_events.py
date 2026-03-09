"""
Módulo de gestión de eventos en Google Calendar.
Zona horaria: America/Argentina/Buenos_Aires
"""

from __future__ import annotations
import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

TIMEZONE = "America/Argentina/Buenos_Aires"
TZ = ZoneInfo(TIMEZONE)


# ─────────────────────────────────────────────
# Definición de todos los eventos
# ─────────────────────────────────────────────

SEMINARIO_BASE_DESC = """
📌 Diplomatura objetivo: Salud Internacional

🔗 Links:
• YouTube principal: https://www.youtube.com/c/EscueladegobiernoensaludFlorealFerrara
• Canal alternativo: https://www.youtube.com/@escueladegobiernoensaludff/featured
• Formulario diplomatura: https://forms.gle/QmN9so4e5uPDxM2Q9
""".strip()

EVENTS_DEFINITION = [
    # ──── PARTE 1: Seminario Políticas Públicas en Salud ────

    {
        "title": "Seminario Políticas Públicas en Salud – Clase 1",
        "date": "2026-03-04",
        "start_time": "14:00",
        "end_time": "16:00",
        "location": "YouTube – Escuela de Gobierno en Salud Floreal Ferrara",
        "description": """Seminario transversal introductorio de Políticas Públicas de Salud de la Provincia de Buenos Aires.

📚 Actividad:
Clase introductoria del seminario requerido para diplomaturas y cursos superiores.

⚠️ Importante:
• La clase se transmite por YouTube.
• Si no puedo verla en vivo queda grabada.
• Aprobar el seminario y completar la preinscripción es REQUISITO para continuar el proceso.
• Aprobar no garantiza vacante definitiva.

📋 Contenido orientativo:
• Integralidad de políticas de salud
• Gobierno en salud
• Salud mental en transformación
• Recursos estratégicos
• Red de servicios de salud
• Igualdad y diversidad
• Plan Quinquenal 2022–2027
• Gestión de fuerza laboral

""" + SEMINARIO_BASE_DESC,
        "reminders_minutes": [1440, 120, 30],  # 1 día, 2 horas, 30 min
    },
    {
        "title": "Seminario Políticas Públicas en Salud – Clase 2",
        "date": "2026-03-11",
        "start_time": "14:00",
        "end_time": "16:00",
        "location": "YouTube – Escuela de Gobierno en Salud Floreal Ferrara",
        "description": """Segunda clase del Seminario de Políticas Públicas en Salud.

📋 Indicaciones:
• Ver transmisión en YouTube en vivo.
• Si no puedo verla en vivo, revisar grabación posterior.
• Tomar apuntes para la evaluación final.

""" + SEMINARIO_BASE_DESC,
        "reminders_minutes": [1440, 120, 30],
    },
    {
        "title": "Seminario Políticas Públicas en Salud – Clase 3",
        "date": "2026-03-18",
        "start_time": "14:00",
        "end_time": "16:00",
        "location": "YouTube – Escuela de Gobierno en Salud Floreal Ferrara",
        "description": """Última clase del Seminario de Políticas Públicas en Salud.

📋 Después del seminario:
• Revisar correo → llegará evaluación multiple choice.
• Fecha límite de entrega: 29/03/2026.

✅ Requisito:
Aprobar la evaluación es condición para la matriculación definitiva.

""" + SEMINARIO_BASE_DESC,
        "reminders_minutes": [1440, 120, 30],
    },
    {
        "title": "Recordatorio – Completar evaluación Seminario Políticas Públicas en Salud",
        "date": "2026-03-25",
        "start_time": "10:00",
        "end_time": "10:30",
        "location": "Revisar mail / Google Forms",
        "description": """⏰ Recordatorio para completar la evaluación final del seminario.

📋 Tareas:
• Revisar correo electrónico.
• Localizar el formulario de evaluación.
• Completar la evaluación antes del 29/03/2026.

⚠️ Importante:
• Evaluación OBLIGATORIA.
• Fecha límite: 29/03/2026.

🔗 Links:
• Formulario: https://forms.gle/QmN9so4e5uPDxM2Q9
• YouTube: https://www.youtube.com/c/EscueladegobiernoensaludFlorealFerrara

📌 Diplomatura objetivo: Salud Internacional""",
        "reminders_minutes": [4320, 1440, 480],  # 3 días, 1 día, 8hs (= 08:00 mismo día)
    },

    # ──── PARTE 2: Eventos de evaluación (estimados si no hay correo) ────

    {
        "title": "Abrir evaluación – Seminario Políticas Públicas en Salud",
        "date": "2026-03-19",
        "start_time": "09:00",
        "end_time": "09:30",
        "location": "Revisar mail / Google Forms",
        "description": """Apertura estimada de la evaluación final del Seminario Transversal.

📋 Acción:
• Abrir el correo con el link de evaluación.
• Verificar instrucciones y fecha límite.
• Revisar formulario: https://forms.gle/QmN9so4e5uPDxM2Q9

⚠️ Nota: Evento creado como referencia. Confirmar fecha exacta al recibir el correo de la Escuela de Gobierno en Salud Floreal Ferrara.

📌 Diplomatura objetivo: Salud Internacional""",
        "reminders_minutes": [10080, 4320, 1440, 120],  # 1 semana, 3 días, 1 día, 2 horas
    },
    {
        "title": "Completar evaluación – Seminario Políticas Públicas en Salud",
        "date": "2026-03-24",
        "start_time": "18:00",
        "end_time": "19:00",
        "location": "Google Forms – Online",
        "description": """Completar la evaluación multiple choice del seminario antes del 29/03/2026.

📋 Pasos:
• Buscar correo de la Escuela de Gobierno en Salud Floreal Ferrara.
• Acceder al formulario de evaluación.
• Completar y enviar el cuestionario.

🔗 Formulario: https://forms.gle/QmN9so4e5uPDxM2Q9

⚠️ Fecha límite: 29/03/2026

📌 Diplomatura objetivo: Salud Internacional""",
        "reminders_minutes": [10080, 4320, 1440, 120],
    },
    {
        "title": "⚠️ ÚLTIMO DÍA – Evaluación Seminario Políticas Públicas en Salud",
        "date": "2026-03-29",
        "start_time": "12:00",
        "end_time": "13:00",
        "location": "Google Forms – Online",
        "description": """🚨 HOY ES EL ÚLTIMO DÍA para completar la evaluación del seminario.

📋 Acción inmediata:
• Si aún no completaste la evaluación, hacerlo AHORA.
• Formulario: https://forms.gle/QmN9so4e5uPDxM2Q9

⚠️ Sin aprobar la evaluación NO hay matriculación definitiva en la Diplomatura de Salud Internacional.

📌 Diplomatura objetivo: Salud Internacional""",
        "reminders_minutes": [10080, 4320, 1440, 120],
    },

    # ──── PARTE 3: Materia UPSO ────

    {
        "title": "Definir cronograma tentativo SIRAD – Teoría Antropológica de la Salud",
        "date": "2026-03-13",
        "start_time": "10:00",
        "end_time": "10:30",
        "location": "SIRAD / Online",
        "description": """Tarea: Definir el cronograma tentativo de la materia en el sistema SIRAD.

📚 Materia: Teoría Antropológica de la Salud
🏛️ Carrera: Enfermería
📍 Sede: UPSO Monte Hermoso

👥 Equipo docente:
• Prof. Juan Pablo Pardias
• Prof. Lauriano Alimenti
• Aux. Fernando Sandoval

📋 Acción:
Ingresar a SIRAD y verificar/definir el cronograma de clases del primer cuatrimestre.""",
        "reminders_minutes": [1440],
    },
    {
        "title": "Inicio de Teoría Antropológica de la Salud – UPSO Monte Hermoso",
        "date": "2026-03-16",
        "start_time": "08:00",
        "end_time": "10:00",
        "location": "UPSO Monte Hermoso",
        "description": """Inicio de cursada del primer cuatrimestre 2026.

📚 Materia: Teoría Antropológica de la Salud
🏛️ Carrera: Enfermería
📍 Sede: UPSO Monte Hermoso

👥 Equipo docente:
• Prof. Juan Pablo Pardias
• Prof. Lauriano Alimenti
• Aux. Fernando Sandoval

📋 Acciones del día:
• Confirmar cronograma y modalidad de cursada.
• Consultar con docentes sobre programa y bibliografía.
• Verificar horario definitivo en SIRAD.""",
        "reminders_minutes": [1440],
    },
    {
        "title": "Confirmar cronograma y modalidad – Teoría Antropológica de la Salud",
        "date": "2026-03-16",
        "start_time": "10:00",
        "end_time": "10:30",
        "location": "UPSO Monte Hermoso / SIRAD",
        "description": """Confirmar con los docentes el cronograma definitivo y la modalidad de cursada.

📚 Materia: Teoría Antropológica de la Salud
🏛️ Carrera: Enfermería
📍 Sede: UPSO Monte Hermoso

👥 Docentes:
• Prof. Juan Pablo Pardias
• Prof. Lauriano Alimenti
• Aux. Fernando Sandoval

📋 Verificar:
• Modalidad (presencial / virtual / mixta)
• Días y horarios de clase
• Fechas de parciales
• Bibliografía requerida""",
        "reminders_minutes": [1440],
    },
]


# ─────────────────────────────────────────────
# Funciones principales
# ─────────────────────────────────────────────

def build_event_body(ev: dict) -> dict:
    """Construye el body del evento para la API de Google Calendar."""
    date = ev["date"]
    start_dt = datetime.datetime.fromisoformat(f"{date}T{ev['start_time']}:00")
    end_dt = datetime.datetime.fromisoformat(f"{date}T{ev['end_time']}:00")

    reminders = {
        "useDefault": False,
        "overrides": [
            {"method": "popup", "minutes": m}
            for m in ev["reminders_minutes"]
        ],
    }

    body = {
        "summary": ev["title"],
        "location": ev.get("location", ""),
        "description": ev["description"],
        "start": {
            "dateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": TIMEZONE,
        },
        "reminders": reminders,
    }
    return body


def find_existing_event(
    service,
    calendar_id: str,
    title: str,
    date: str,
) -> Optional[dict]:
    """
    Busca un evento existente por título exacto y fecha.
    Retorna el evento si existe, None si no.
    """
    start_of_day = f"{date}T00:00:00-03:00"
    end_of_day = f"{date}T23:59:59-03:00"

    try:
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        for event in result.get("items", []):
            if event.get("summary", "").strip() == title.strip():
                return event
    except HttpError as e:
        print(f"[CALENDAR] Error buscando evento: {e}")

    return None


def create_or_update_event(
    service,
    calendar_id: str,
    ev_def: dict,
) -> dict:
    """
    Crea un nuevo evento o actualiza uno existente (misma fecha y título).
    Retorna un dict con resultado: acción, título, fecha, id, error.
    """
    title = ev_def["title"]
    date = ev_def["date"]
    result = {"title": title, "date": date, "action": None, "id": None, "error": None}

    try:
        existing = find_existing_event(service, calendar_id, title, date)
        body = build_event_body(ev_def)

        if existing:
            updated = service.events().update(
                calendarId=calendar_id,
                eventId=existing["id"],
                body=body,
            ).execute()
            result["action"] = "actualizado"
            result["id"] = updated["id"]
            result["link"] = updated.get("htmlLink", "")
        else:
            created = service.events().insert(
                calendarId=calendar_id,
                body=body,
            ).execute()
            result["action"] = "creado"
            result["id"] = created["id"]
            result["link"] = created.get("htmlLink", "")

    except HttpError as e:
        result["action"] = "error"
        result["error"] = str(e)

    return result


def run_calendar_sync(creds: Credentials, calendar_id: str = "primary") -> list[dict]:
    """
    Sincroniza todos los eventos definidos con Google Calendar.
    Retorna lista de resultados.
    """
    service = build("calendar", "v3", credentials=creds)
    results = []

    print(f"\n[CALENDAR] Procesando {len(EVENTS_DEFINITION)} eventos...\n")

    for ev_def in EVENTS_DEFINITION:
        res = create_or_update_event(service, calendar_id, ev_def)
        results.append(res)

        status_icon = {"creado": "✅", "actualizado": "🔄", "error": "❌"}.get(
            res["action"], "?"
        )
        print(f"  {status_icon} [{res['action'].upper()}] {res['title']} ({res['date']})")
        if res["error"]:
            print(f"     Error: {res['error']}")

    return results
