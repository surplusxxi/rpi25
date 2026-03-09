#!/usr/bin/env python3
"""
=============================================================
Asistente Académico – Gestor de Agenda
=============================================================
Zona horaria: America/Argentina/Buenos_Aires

Funcionalidades:
  PARTE 1 – Crea/actualiza eventos del Seminario Políticas
            Públicas en Salud (Escuela de Gobierno Floreal Ferrara)
  PARTE 2 – Busca en Gmail correos sobre evaluación del seminario
            y crea eventos adicionales si se encuentra información
  PARTE 3 – Crea eventos para la materia UPSO Monte Hermoso
             (Teoría Antropológica de la Salud)
=============================================================
"""

import sys
import json
from datetime import datetime
from auth import get_credentials
from calendar_events import run_calendar_sync, EVENTS_DEFINITION
from gmail_search import search_gmail


# ─────────────────────────────────────────────
# Helpers para el resumen final
# ─────────────────────────────────────────────

def format_minutes(minutes: int) -> str:
    if minutes >= 10080:
        return f"{minutes // 10080} semana(s)"
    if minutes >= 1440:
        return f"{minutes // 1440} día(s)"
    if minutes >= 60:
        return f"{minutes // 60} hora(s)"
    return f"{minutes} min"


def print_separator(char="─", width=60):
    print(char * width)


def print_header(text: str):
    print_separator("═")
    print(f"  {text}")
    print_separator("═")


def print_section(text: str):
    print()
    print_separator()
    print(f"  {text}")
    print_separator()


def print_calendar_summary(results: list[dict]):
    print_section("RESUMEN – GOOGLE CALENDAR")

    created = [r for r in results if r["action"] == "creado"]
    updated = [r for r in results if r["action"] == "actualizado"]
    errors = [r for r in results if r["action"] == "error"]

    print(f"\n  ✅ Eventos CREADOS: {len(created)}")
    for r in created:
        print(f"     • {r['title']}")
        print(f"       Fecha: {r['date']}")
        if r.get("link"):
            print(f"       Link:  {r['link']}")

    if updated:
        print(f"\n  🔄 Eventos ACTUALIZADOS: {len(updated)}")
        for r in updated:
            print(f"     • {r['title']}")
            print(f"       Fecha: {r['date']}")

    if errors:
        print(f"\n  ❌ Eventos con ERROR: {len(errors)}")
        for r in errors:
            print(f"     • {r['title']} ({r['date']})")
            print(f"       Error: {r['error']}")


def print_gmail_summary(messages: list[dict]):
    print_section("RESUMEN – GMAIL")

    if not messages:
        print("\n  ⬜ No se encontraron correos relacionados.")
        print("     Esto puede deberse a que:")
        print("     • Los correos aún no fueron enviados por la institución.")
        print("     • El correo se encuentra en otra cuenta o carpeta.")
        print("     • Se debe buscar manualmente en:")
        print("       - Carpeta 'Spam' o 'Promociones'")
        print("       - Otros correos asociados")
        return

    relevant = [m for m in messages if m["es_relevante"]]
    other = [m for m in messages if not m["es_relevante"]]

    print(f"\n  📬 Total de correos encontrados: {len(messages)}")
    print(f"  🎯 Correos relevantes (evaluación): {len(relevant)}")
    print(f"  📄 Otros correos relacionados: {len(other)}")

    if relevant:
        print("\n  ─── CORREOS RELEVANTES ───")
        for i, m in enumerate(relevant, 1):
            print(f"\n  [{i}] {m['asunto']}")
            print(f"       Remitente: {m['remitente']}")
            print(f"       Fecha: {m['fecha']}")
            if m["snippet"]:
                print(f"       Vista previa: {m['snippet'][:120]}...")
            if m["fechas_en_cuerpo"]:
                print(f"       Fechas detectadas: {', '.join(m['fechas_en_cuerpo'][:5])}")
            if m["links_en_cuerpo"]:
                print(f"       Links encontrados:")
                for link in m["links_en_cuerpo"][:5]:
                    print(f"         - {link}")
            if m["keywords_detectadas"]:
                print(f"       Keywords: {', '.join(m['keywords_detectadas'])}")

    if other:
        print(f"\n  ─── OTROS CORREOS (no específicamente sobre evaluación) ───")
        for m in other[:5]:
            print(f"     • {m['asunto']} | {m['remitente']} | {m['fecha'][:16]}")


def print_event_definitions_summary():
    """Muestra un resumen de los eventos que se intentarán crear."""
    print_section("EVENTOS A SINCRONIZAR")

    parts = {
        "PARTE 1 – Seminario Políticas Públicas en Salud": [
            e for e in EVENTS_DEFINITION if "Seminario" in e["title"] or "evaluación Seminario" in e["title"].lower()
        ],
        "PARTE 2 – Evaluación del Seminario": [
            e for e in EVENTS_DEFINITION if "evaluación" in e["title"].lower() and "Seminario" in e["title"] and "Recordatorio" not in e["title"]
        ],
        "PARTE 3 – UPSO Monte Hermoso": [
            e for e in EVENTS_DEFINITION if "UPSO" in e["title"] or "Antropológica" in e["title"] or "cronograma" in e["title"].lower()
        ],
    }

    for part_name, events in parts.items():
        if events:
            print(f"\n  📂 {part_name}")
            for e in events:
                reminders_str = " | ".join(format_minutes(m) for m in e["reminders_minutes"])
                print(f"     • {e['date']} {e['start_time']}–{e['end_time']}  →  {e['title']}")
                print(f"       Recordatorios: {reminders_str}")


def print_final_report(calendar_results: list[dict], gmail_messages: list[dict]):
    print()
    print_header("REPORTE FINAL – ASISTENTE ACADÉMICO")
    print(f"  Fecha de ejecución: {datetime.now().strftime('%d/%m/%Y %H:%M')} (ART)")
    print(f"  Zona horaria: America/Argentina/Buenos_Aires")

    print_calendar_summary(calendar_results)
    print_gmail_summary(gmail_messages)

    print()
    print_separator("═")
    print("  NOTAS IMPORTANTES")
    print_separator("═")
    print("""
  1. Si no se encontraron correos de la evaluación, revisar manualmente:
     - Bandeja de entrada y Spam en Gmail
     - Correo llegará entre el 18/03 y 19/03/2026 (estimado)

  2. Los eventos de "Abrir evaluación" y "Completar evaluación" fueron creados
     con fechas estimadas. Actualizar cuando llegue el correo oficial.

  3. La fecha límite de evaluación es el 29/03/2026. El evento de
     "ÚLTIMO DÍA" tiene recordatorios agresivos configurados.

  4. Para la materia UPSO: verificar el cronograma en SIRAD el 13/03/2026.

  5. Aprobar el seminario NO garantiza vacante definitiva en la diplomatura.
""")
    print_separator("═")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    print_header("ASISTENTE ACADÉMICO – INICIO")
    print("""
  Este script gestiona tu agenda académica:
  • Seminario Políticas Públicas en Salud (Escuela Floreal Ferrara)
  • Materia Teoría Antropológica de la Salud (UPSO Monte Hermoso)
  • Búsqueda de correos sobre evaluación del seminario
""")

    # 1. Autenticación
    print_section("AUTENTICACIÓN – Google APIs")
    try:
        creds = get_credentials()
        print("  ✅ Autenticación exitosa.")
    except FileNotFoundError as e:
        print(f"\n  ❌ ERROR DE AUTENTICACIÓN\n")
        print(str(e))
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌ Error inesperado en autenticación: {e}")
        sys.exit(1)

    # 2. Mostrar eventos a sincronizar
    print_event_definitions_summary()

    # 3. Sincronizar Calendar (Partes 1, 2 y 3)
    print_section("SINCRONIZANDO – Google Calendar")
    calendar_results = run_calendar_sync(creds)

    # 4. Buscar en Gmail (Parte 2)
    print_section("BUSCANDO EN – Gmail")
    gmail_messages = search_gmail(creds)

    # 5. Si hay correos relevantes con links/fechas, reportarlos
    relevant_msgs = [m for m in gmail_messages if m["es_relevante"]]
    if relevant_msgs:
        print(f"\n  ⚠️  Se encontraron {len(relevant_msgs)} correo(s) relevante(s).")
        print("  Revisar el reporte final para ver los datos extraídos.")
        print("  Se recomienda actualizar manualmente los eventos de evaluación")
        print("  con las fechas y links exactos del correo oficial.")

    # 6. Reporte final
    print_final_report(calendar_results, gmail_messages)


if __name__ == "__main__":
    main()
