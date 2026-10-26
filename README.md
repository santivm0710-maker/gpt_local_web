# Chat local con generación de imágenes

Aplicación web local para conversar con un modelo de lenguaje de Ollama y generar
imágenes con modelos de Cloudflare Workers AI.

## Tecnologías

| Componente | Tecnología |
| --- | --- |
| Interfaz | HTML, CSS y JavaScript en `static/` |
| Interfaz JavaScript | `ChatApp.js` coordina la aplicación; `ChatView.js` gestiona la interfaz; `ChatApi.js` realiza las solicitudes; `app.js` inicia la aplicación. |
| Backend | Python en `backend/`, organizado en módulos para configuración, servicios, HTTP, persistencia y coordinación. |
| Base de datos | SQLite, incluida en Python; guarda conversaciones y mensajes en un archivo local. |
| Chat | Ollama con el modelo `llama3.2:3b` |
| Imágenes | Cloudflare Workers AI: Leonardo Phoenix 1.0, FLUX.1 Schnell y DreamShaper 8 LCM |

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

### Base de datos local

La aplicación crea automáticamente el esquema SQLite al iniciar. En Windows, el archivo
se guarda por defecto en `%LOCALAPPDATA%\ChatLocal\chat.sqlite3`, fuera de la carpeta del
proyecto. En otros sistemas usa `$XDG_DATA_HOME/ChatLocal/chat.sqlite3` o
`~/.local/share/ChatLocal/chat.sqlite3`.

Para usar otra ubicación, configura opcionalmente `DATABASE_PATH` en `.env`; una ruta
relativa se interpreta desde la carpeta raíz del proyecto:

```env
DATABASE_PATH=data/chat.sqlite3
```

El esquema está en `backend/schema.sql`; la conexión, el repositorio y la lógica de
conversaciones están separados en `backend/database.py`,
`backend/conversation_repository.py` y `backend/conversation_service.py`. No se requiere
instalar una dependencia de base de datos adicional. La base es local y no está cifrada;
no guardes allí información sensible. Los archivos SQLite están excluidos de Git.

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

Escribe un mensaje y presiona **Enviar** para conversar con Ollama. Las conversaciones y
sus mensajes se guardan localmente y aparecen en la lista **Conversación** para poder
retomarlos. Ollama recibe los últimos 20 mensajes de la conversación como contexto.
**Nueva conversación** inicia un chat separado. El límite del contexto se puede ajustar
en `chat_history_limit` de `backend/app_config.py`.

Para generar una imagen, selecciona **Leonardo Phoenix 1.0**, **FLUX.1 Schnell** o
**DreamShaper 8 LCM**, escribe una
descripción y presiona **Crear imagen**. Phoenix ofrece mejor fidelidad al prompt y
renderizado de texto; es el modelo predeterminado. Los otros modelos siguen disponibles si
prefieres velocidad o un estilo diferente. Las imágenes generadas se pueden descargar desde
la conversación. Por ahora, ni las imágenes ni sus solicitudes se guardan en la base de
datos.

La API de conversaciones es reutilizable desde otros clientes HTTP locales:

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/conversaciones` | Lista conversaciones y cantidad de mensajes |
| `POST` | `/api/conversaciones` | Crea una conversación |
| `GET` | `/api/conversaciones/{id}` | Obtiene una conversación con sus mensajes |
| `POST` | `/api/chat` | Envía `{ "conversationId": 1, "message": "Hola" }` y guarda el intercambio |

Cloudflare ofrece 10.000 Neurons gratuitas al día en Workers Free; la cuota se comparte
entre todos los modelos de Workers AI y puede cambiar. Una imagen Phoenix de 1024 × 1024
con 25 pasos consume aproximadamente 2.370 Neurons, así que la cuota alcanza para unas
cuatro imágenes diarias si no usas otros modelos. Al agotarse, las solicitudes fallan en
Workers Free. En un plan Workers Paid, el uso que supere la cuota gratuita puede generar
cargos. Revisa el uso y el plan en Cloudflare si quieres mantener el costo en cero. Las
descripciones se envían a Cloudflare; no incluyas información sensible. Consulta la
[ficha de Phoenix 1.0](https://developers.cloudflare.com/workers-ai/models/phoenix-1.0/)
y los [precios actuales de Workers AI](https://developers.cloudflare.com/workers-ai/platform/pricing/).

La lista de modelos se valida en el servidor. Para cambiar el modelo de imagen
predeterminado, modifica `DEFAULT_MODEL` en `backend/image_service.py`. Para cambiar el
modelo de chat, modifica el valor `chat_model` en `backend/app_config.py`.

## Estructura

```text
backend/
  app_config.py       Configuración y carga de variables de entorno
  application.py     Coordinación de la aplicación
  chat_service.py    Comunicación con Ollama
  conversation_repository.py Consultas reutilizables de conversaciones y mensajes
  conversation_service.py Reglas de aplicación para el historial y el chat
  database.py        Conexiones SQLite y creación del esquema
  http_server.py     Servidor HTTP
  image_service.py  Generación de imágenes con Cloudflare
  request_handler.py Rutas HTTP y API
  schema.sql         Esquema inicial de SQLite
  server.py          Punto de entrada
static/
  app.js
  ChatApi.js
  ChatApp.js
  ChatView.js
  index.html
  style.css
```

## Acceso directo en el escritorio (Windows)

El archivo `Iniciar Chat Local.bat`, en la carpeta raíz del proyecto, inicia el servidor
y abre la aplicación en el navegador. Para crear un icono en el escritorio:

1. En el Explorador de archivos, abre la carpeta del proyecto.
2. Haz clic derecho en `Iniciar Chat Local.bat` y selecciona **Mostrar más opciones**
   > **Enviar a** > **Escritorio (crear acceso directo)**.
3. Abre el acceso directo desde el escritorio para iniciar la aplicación. La ventana de
   consola debe permanecer abierta mientras la app esté en uso; ciérrala para detenerla.

Si Windows no reconoce el comando `python`, instala Python o ajusta el lanzador para usar
el comando con el que lo inicias desde PowerShell.

## Mejoras futuras

- Empaquetar la aplicación como una app de escritorio con instalador e icono propio.
- Renombrar, eliminar y exportar conversaciones guardadas.
- Añadir opciones para configurar modelos, dirección del servidor y preferencias desde la interfaz.
- Guardar las imágenes generadas y su historial localmente.
- Incorporar generación de imágenes local para reducir la dependencia de servicios externos.
