# Asistente Académico – Gestor de Agenda
## Zona horaria: America/Argentina/Buenos_Aires

---

## ¿Qué hace este script?

1. **PARTE 1** – Crea o actualiza 4 eventos del **Seminario de Políticas Públicas en Salud** (Escuela de Gobierno Floreal Ferrara):
   - Clase 1 → 4/03/2026 14:00–16:00
   - Clase 2 → 11/03/2026 14:00–16:00
   - Clase 3 → 18/03/2026 14:00–16:00
   - Recordatorio evaluación → 25/03/2026 10:00–10:30

2. **PARTE 2** – Busca en Gmail correos sobre la evaluación del seminario y crea:
   - Abrir evaluación → 19/03/2026 09:00
   - Completar evaluación → 24/03/2026 18:00
   - Último día evaluación → 29/03/2026 12:00

3. **PARTE 3** – Crea eventos para **Teoría Antropológica de la Salud** (UPSO Monte Hermoso):
   - Definir cronograma SIRAD → 13/03/2026
   - Inicio de cursada → 16/03/2026
   - Confirmar cronograma → 16/03/2026

---

## Configuración inicial (una sola vez)

### Paso 1: Habilitar APIs en Google Cloud Console

1. Ve a [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Crea un nuevo proyecto (o selecciona uno existente)
3. Ve a **APIs y Servicios → Biblioteca**
4. Habilita **Google Calendar API**
5. Habilita **Gmail API**

### Paso 2: Crear credenciales OAuth 2.0

1. Ve a **APIs y Servicios → Credenciales**
2. Clic en **Crear credenciales → ID de cliente OAuth 2.0**
3. Tipo de aplicación: **Aplicación de escritorio**
4. Descarga el archivo JSON
5. Renómbralo a `credentials.json`
6. Colócalo en esta carpeta (junto a `main.py`)

### Paso 3: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4: Ejecutar el script

```bash
python main.py
```

En la primera ejecución se abrirá el navegador para autorizar el acceso.
El token se guardará en `token.pickle` para usos futuros.

---

## Variable de entorno alternativa

Si no puedes usar el flujo OAuth interactivo, puedes exportar el token como variable de entorno:

```bash
export GOOGLE_TOKEN_JSON='{"token": "...", "refresh_token": "...", ...}'
python main.py
```

---

## Reglas de gestión de eventos

- **No crea duplicados**: si existe un evento con el mismo título y fecha, lo actualiza.
- **Recordatorios**: configurados con popup (1 día antes, 2 horas antes, 30 minutos antes según el evento).
- **Zona horaria**: todos los eventos usan `America/Argentina/Buenos_Aires`.
- **Descripción completa**: cada evento incluye links, instrucciones y contexto.

---

## Archivos del proyecto

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Script principal – orquesta todo el flujo |
| `auth.py` | Manejo de autenticación OAuth2 con Google |
| `calendar_events.py` | Definición y sincronización de eventos |
| `gmail_search.py` | Búsqueda de correos en Gmail |
| `requirements.txt` | Dependencias de Python |
| `credentials.json` | ⚠️ NO SUBIR AL REPOSITORIO (crear localmente) |
| `token.pickle` | ⚠️ NO SUBIR AL REPOSITORIO (se genera automáticamente) |
