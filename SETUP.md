# Asistente Académico – Configuración

## Requisitos previos

### 1. Credenciales OAuth2 de Google

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto nuevo (o usar uno existente)
3. Habilitar las APIs:
   - **Google Calendar API**
   - **Gmail API**
4. En **Credenciales** → **Crear credenciales** → **ID de cliente OAuth**
5. Tipo de aplicación: **Aplicación de escritorio**
6. Descargar el archivo JSON → guardarlo como `credentials.json` en esta carpeta

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el script

```bash
python3 calendar_assistant.py
```

La primera vez abrirá una ventana del navegador para autorizar el acceso.
El token se guarda en `token.json` para usos posteriores.

---

## Qué hace el script

### PARTE 1 – Seminario Políticas Públicas en Salud

Crea o actualiza los siguientes eventos en Google Calendar:

| Fecha | Evento |
|-------|--------|
| 04/03/2026 14:00–16:00 | Clase 1 del Seminario |
| 11/03/2026 14:00–16:00 | Clase 2 del Seminario |
| 18/03/2026 14:00–16:00 | Clase 3 del Seminario |
| 25/03/2026 10:00–10:30 | Recordatorio evaluación |

### PARTE 2 – Evaluación del Seminario

| Fecha | Evento |
|-------|--------|
| 19/03/2026 09:00–09:30 | Abrir evaluación |
| 24/03/2026 18:00–19:00 | Completar evaluación |
| 29/03/2026 12:00–12:30 | Último día evaluación |

También busca en Gmail correos relacionados con:
- Seminario Transversal
- Evaluación / cuestionario multiple choice
- Diplomatura / vacante
- Fechas 19/03 y 29/03

### PARTE 3 – UPSO Teoría Antropológica de la Salud

| Fecha | Evento |
|-------|--------|
| 13/03/2026 10:00–10:30 | Definir cronograma en SIRAD |
| 16/03/2026 08:00–10:00 | Inicio de cursada |
| 16/03/2026 10:00–10:30 | Confirmar cronograma y modalidad |

---

## Seguridad

- `credentials.json` y `token.json` están en `.gitignore`
- Nunca compartir estos archivos
