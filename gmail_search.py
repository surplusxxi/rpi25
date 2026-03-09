"""
Módulo de búsqueda en Gmail.
Busca correos relacionados con el Seminario Transversal de Políticas Públicas en Salud
y la evaluación de la Escuela de Gobierno en Salud Floreal Ferrara.
"""

from __future__ import annotations
import base64
import re
from email import message_from_bytes
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials


# ─────────────────────────────────────────────
# Queries de búsqueda
# ─────────────────────────────────────────────

GMAIL_QUERIES = [
    # Búsquedas específicas del seminario
    "Seminario Transversal Políticas Públicas Salud",
    "Escuela Gobierno Salud Floreal Ferrara evaluación",
    "diplomatura salud internacional inscripción",
    "cuestionario multiple choice seminario salud",
    "vacante diplomatura salud Ferrara",
    "preinscripción diplomatura salud provincial",
    # Fechas clave
    "evaluación seminario 29/03",
    "evaluación seminario 19/03",
    # UPSO
    "UPSO Monte Hermoso Teoría Antropológica",
    "UPSO enfermería cuatrimestre 2026",
]

# Keywords para detección de fechas y links en el cuerpo
DATE_PATTERNS = [
    r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b",  # dd/mm/yyyy
    r"\b\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}\b",      # yyyy-mm-dd
    r"\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b",        # "19 de marzo de 2026"
    r"\b\d{1,2}\s+de\s+\w+\b",                      # "19 de marzo"
]

URL_PATTERN = r"https?://[^\s<>\"']+"

EVALUATION_KEYWORDS = [
    "formulario", "form", "evaluación", "evaluacion", "cuestionario",
    "multiple choice", "link de evaluación", "fecha límite", "fecha limite",
    "completar antes", "aprobar", "matriculación", "vacante",
    "19/03", "29/03", "marzo",
]


# ─────────────────────────────────────────────
# Funciones de extracción
# ─────────────────────────────────────────────

def decode_body(payload: dict) -> str:
    """Decodifica el cuerpo del mensaje de Gmail (base64 → texto plano)."""
    body = ""

    def extract_parts(part):
        nonlocal body
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                body += base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        elif mime == "text/html":
            data = part.get("body", {}).get("data", "")
            if data and not body:  # solo si no hay texto plano
                raw = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                # Limpiar HTML básico
                body += re.sub(r"<[^>]+>", " ", raw)
        elif "parts" in part:
            for subpart in part.get("parts", []):
                extract_parts(subpart)

    if "parts" in payload:
        for part in payload.get("parts", []):
            extract_parts(part)
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return body.strip()


def extract_info_from_body(body: str) -> dict:
    """Extrae fechas, links y keywords relevantes del cuerpo del mensaje."""
    info = {
        "fechas_encontradas": [],
        "links_encontrados": [],
        "keywords_detectadas": [],
        "es_relevante": False,
    }

    # Extraer fechas
    for pattern in DATE_PATTERNS:
        matches = re.findall(pattern, body, re.IGNORECASE)
        info["fechas_encontradas"].extend(matches)

    # Extraer URLs
    urls = re.findall(URL_PATTERN, body)
    info["links_encontrados"] = list(set(urls))[:10]  # máximo 10 links únicos

    # Detectar keywords de evaluación
    body_lower = body.lower()
    for kw in EVALUATION_KEYWORDS:
        if kw.lower() in body_lower:
            info["keywords_detectadas"].append(kw)

    # Determinar si es relevante
    info["es_relevante"] = len(info["keywords_detectadas"]) >= 2

    # Deduplicate fechas
    info["fechas_encontradas"] = list(set(info["fechas_encontradas"]))

    return info


def get_header(headers: list, name: str) -> str:
    """Extrae un header específico de la lista de headers."""
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def search_gmail(creds: Credentials) -> list[dict]:
    """
    Realiza búsquedas en Gmail con múltiples queries.
    Retorna lista de mensajes encontrados con sus metadatos.
    """
    service = build("gmail", "v1", credentials=creds)
    found_messages = {}  # id → mensaje (para evitar duplicados)

    print(f"\n[GMAIL] Ejecutando {len(GMAIL_QUERIES)} búsquedas...\n")

    for query in GMAIL_QUERIES:
        try:
            result = service.users().messages().list(
                userId="me",
                q=query,
                maxResults=10,
            ).execute()

            messages = result.get("messages", [])
            if messages:
                print(f"  🔍 Query: '{query}' → {len(messages)} resultado(s)")
            else:
                print(f"  ⬜ Query: '{query}' → sin resultados")

            for msg_ref in messages:
                msg_id = msg_ref["id"]
                if msg_id in found_messages:
                    continue  # ya procesado

                # Obtener mensaje completo
                msg = service.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format="full",
                ).execute()

                payload = msg.get("payload", {})
                headers = payload.get("headers", [])

                subject = get_header(headers, "Subject")
                sender = get_header(headers, "From")
                date = get_header(headers, "Date")
                body = decode_body(payload)
                info = extract_info_from_body(body)

                found_messages[msg_id] = {
                    "id": msg_id,
                    "asunto": subject,
                    "remitente": sender,
                    "fecha": date,
                    "snippet": msg.get("snippet", ""),
                    "body_preview": body[:500] if body else "",
                    "fechas_en_cuerpo": info["fechas_encontradas"],
                    "links_en_cuerpo": info["links_encontrados"],
                    "keywords_detectadas": info["keywords_detectadas"],
                    "es_relevante": info["es_relevante"],
                    "query_origen": query,
                }

        except HttpError as e:
            print(f"  ❌ Error en query '{query}': {e}")

    messages_list = list(found_messages.values())

    # Ordenar: primero los relevantes
    messages_list.sort(key=lambda m: (not m["es_relevante"], m["fecha"]))

    print(f"\n[GMAIL] Total mensajes únicos encontrados: {len(messages_list)}")
    relevant = [m for m in messages_list if m["es_relevante"]]
    print(f"[GMAIL] Mensajes relevantes (evaluación): {len(relevant)}")

    return messages_list
