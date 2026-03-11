# Prompt Maestro — Organizador de Google Drive

Reorganización segura, incremental y retomable de Google Drive.
Owner objetivo: `laureanoalimenti@gmail.com`

---

## Instalación

```bash
pip install -r requirements.txt
```

---

## Configuración de credenciales Google

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto nuevo (o usar uno existente)
3. Habilitar **Google Drive API**
4. Crear credenciales → **OAuth 2.0** → tipo **Desktop app**
5. Descargar el archivo como `credentials.json` y colocarlo en este directorio
6. La primera ejecución abrirá el navegador para autorizar el acceso

---

## Uso

```bash
python drive_organizer.py
```

El script detecta automáticamente si hay un checkpoint previo guardado en tu Drive
y retoma desde donde quedó.

---

## Fases de trabajo

| Fase | Descripción | Acción |
|------|-------------|--------|
| 1 | **Mapeo** | Lista todos tus archivos. No toca nada. |
| 2 | **Propuesta** | Sugiere destino para cada archivo. Requiere "APROBADO". |
| 3 | **Ejecución incremental** | Mueve de a una carpeta fuente. Confirmación por paso. |
| 4 | **Revisión \_REVISAR/** | Revisa archivos ambiguos de a 10. |
| 5 | **Limpieza de permisos** | Lista y permite revocar accesos externos. |

---

## Reglas de oro

- **Nunca** elimina archivos. Solo mueve o sugiere.
- **Nunca** toca archivos cuyo owner no sea `laureanoalimenti@gmail.com`.
- **Nunca** ejecuta movimientos sin aprobación explícita.
- Guarda el checkpoint en Drive tras cada acción importante.
- Archivos ambiguos van a `_REVISAR/`, nunca a la basura.

---

## Estructura destino

```
📁 _REVISAR/
📁 _ARCHIVO_HISTORICO/
📁 [AÑO]_Salud_Publica/
📁 [AÑO]_Docencia_UNS/
📁 [AÑO]_Municipio_BBca/
📁 [AÑO]_Politica/
📁 [AÑO]_Personal/
📁 [AÑO]_Musica/
📁 [AÑO]_Proyectos_Tech/
```

Carpetas ya organizadas que se respetan:
- `1. Documentación Personal`
- `2. Títulos y Certificados`
- `3. Antecedentes profesionales y docentes`

---

## Checkpoint

El archivo `drive_organizer_checkpoint.json` se guarda en la raíz de tu Drive.
Contiene el estado completo: fase actual, carpetas procesadas, archivos movidos,
archivos en `_REVISAR`, y permisos revocados.

Para retomar en cualquier momento:
```bash
python drive_organizer.py
# El script detecta el checkpoint y pregunta si continuar
```
