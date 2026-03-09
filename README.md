# rpi25 - Gmail Automation

Automatización de tareas con Gmail API desde Raspberry Pi.

## Configuración inicial

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Colocar el archivo de credenciales

**IMPORTANTE:** El archivo `client_secret_*.json` que descargaste de Google Cloud Console
**nunca debe subirse a Git**. Está protegido por `.gitignore`.

```bash
# Copia tu archivo de credenciales con este nombre exacto:
cp client_secret_429576443186-lfqjcgj19asf5fjlavpq00vceito1a1k.apps.googleusercontent.com.json \
   credentials/client_secret.json
```

### 3. Primera autenticación

Al ejecutar el script por primera vez, abrirá el navegador para que inicies sesión con tu cuenta de Google y autorices la aplicación:

```bash
python gmail_automation.py
```

Esto creará `credentials/token.pickle` — tampoco se sube a Git.
Las siguientes ejecuciones no pedirán login.

## Estructura del proyecto

```
rpi25/
├── credentials/              # Credenciales locales (ignoradas por Git)
│   ├── client_secret.json    # Tu archivo OAuth2 (copiarlo aquí)
│   └── token.pickle          # Token generado automáticamente
├── gmail_automation.py       # Script principal
├── requirements.txt          # Dependencias Python
├── .gitignore                # Protege las credenciales
└── README.md
```

## Funciones disponibles

| Función | Descripción |
|---|---|
| `autenticar()` | Conecta con Gmail API |
| `enviar_email(servicio, destinatario, asunto, cuerpo)` | Envía un email |
| `leer_emails(servicio, max_resultados, query)` | Lee emails con filtros |
| `marcar_como_leido(servicio, mensaje_id)` | Marca email como leído |

## Ejemplo de uso

```python
from gmail_automation import autenticar, enviar_email, leer_emails

servicio = autenticar()

# Enviar email
enviar_email(servicio, 'destino@gmail.com', 'Asunto', 'Mensaje')

# Leer no leídos
emails = leer_emails(servicio, query='is:unread')
```

## Seguridad

- El archivo `credentials/client_secret.json` **nunca** debe compartirse
- El `.gitignore` ya protege toda la carpeta `credentials/` y archivos `*.json`
- Si sospechas que las credenciales fueron expuestas, revócalas en [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
