# Chat local con generación de imágenes

Aplicación web local para conversar con un modelo de lenguaje de Ollama y generar
imágenes con modelos de Cloudflare Workers AI.

## Tecnologías

| Componente | Tecnología |
| --- | --- |
| Interfaz | HTML, CSS y JavaScript en `static/` |
| Interfaz JavaScript | `ChatApp.js` coordina la aplicación; `ChatView.js` gestiona la interfaz; `ChatApi.js` realiza las solicitudes; `app.js` inicia la aplicación. |
| Backend | Python en `backend/`, organizado en módulos para configuración, servicios, HTTP y coordinación. |
| Chat | Ollama con el modelo `llama3.2:3b` |
| Imágenes | Cloudflare Workers AI: FLUX.1 Schnell y DreamShaper 8 LCM |

## Requisitos

- Python y Ollama instalados.
- Conexión a Internet para generar imágenes.
- Cuenta de Cloudflare y credenciales de Workers AI para generar imágenes.

## Configuración

### Ollama

Descarga el modelo de chat:

```powershell
ollama pull llama3.2:3b
```

Si Ollama no se está ejecutando, puedes iniciarlo desde PowerShell:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

### Cloudflare Workers AI

La aplicación lee las credenciales desde `.env`, que está excluido de Git. En el panel de
[Workers AI](https://dash.cloudflare.com/?to=/:account/ai/workers-ai), obtén el Account ID
y crea un token con permisos para usar Workers AI. Añade ambos valores al archivo `.env`:

```env
CLOUDFLARE_ACCOUNT_ID=tu_account_id
CLOUDFLARE_API_TOKEN=tu_token_secreto
```

No compartas ni publiques el token. El servidor lo envía directamente a Cloudflare; nunca
lo expone al navegador. `.env` evita subir accidentalmente las credenciales, pero no las
cifra ni protege el equipo local. Las variables del entorno del sistema tienen prioridad
sobre las definidas en `.env`.

## Instalación y ejecución

Desde la carpeta raíz del proyecto, instala las dependencias:

```powershell
pip install -r requirements.txt
```

Inicia la aplicación desde la raíz:

```powershell
python -m backend.server
```

La aplicación abre `http://127.0.0.1:8000` en el navegador. Para detener el servidor,
presiona **Salir** en la interfaz o usa `Ctrl+C` en la terminal.

## Uso

Escribe un mensaje y presiona **Enviar** para conversar con Ollama. Cada mensaje se envía
de forma independiente; no se conserva el historial para el modelo.

Para generar una imagen, selecciona **FLUX.1 Schnell** o **DreamShaper 8 LCM**, escribe una
descripción y presiona **Crear imagen**. Las imágenes generadas se pueden descargar desde
la conversación.

Cloudflare ofrece una asignación gratuita diaria de Workers AI, sujeta a límites y cambios
del proveedor. La cantidad de imágenes depende del consumo de cada modelo. Las descripciones
se envían a Cloudflare para generar las imágenes; no incluyas información sensible.

La lista de modelos se valida en el servidor. Para cambiar el modelo de chat, modifica el
valor `chat_model` en `backend/app_config.py`.

## Estructura

```text
backend/
  app_config.py       Configuración y carga de variables de entorno
  application.py     Coordinación de la aplicación
  chat_service.py    Comunicación con Ollama
  http_server.py     Servidor HTTP
  image_service.py   Generación de imágenes con Cloudflare
  request_handler.py Rutas HTTP y API
  server.py          Punto de entrada
static/
  app.js
  ChatApi.js
  ChatApp.js
  ChatView.js
  index.html
  style.css
```
