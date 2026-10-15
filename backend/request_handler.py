import json
import logging
import sqlite3
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

from .conversation_service import ConversationNotFoundError
from .image_service import CloudflareImageService


class ChatRequestHandler(BaseHTTPRequestHandler):
    server_version = "ChatOllama/1.0"

    @property
    def app(self):
        return self.server.application

    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _same_origin(self) -> bool:
        """Evita que otra pagina web abierta en el navegador use este servidor."""
        origin = self.headers.get("Origin")
        if not origin:
            return True
        return urlparse(origin).netloc == self.headers.get("Host")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/info":
            return self._json(200, self.app.get_info())
        if path == "/api/conversaciones":
            try:
                return self._json(200, {"conversations": self.app.conversations.list()})
            except sqlite3.Error:
                logging.exception("No se pudo listar las conversaciones")
                return self._json(500, {"error": "No se pudo acceder al historial"})
        conversation_id = self._conversation_id_from_path(path)
        if conversation_id is not None:
            try:
                conversation = self.app.conversations.get(conversation_id)
            except sqlite3.Error:
                logging.exception("No se pudo cargar la conversación %s", conversation_id)
                return self._json(500, {"error": "No se pudo acceder a la conversación"})
            return self._json(
                200 if conversation else 404,
                {"conversation": conversation} if conversation else {"error": "Conversación no encontrada"},
            )
        static_file = self.app.serve_static_file(path)
        if static_file is None:
            return self._json(404, {"error": "No encontrado"})
        body, content_type = static_file
        self._send(200, body, content_type)

    def do_POST(self):
        path = urlparse(self.path).path
        if not self._same_origin():
            return self._json(403, {"error": "Origen no permitido"})

        if path == "/api/salir":
            self._json(200, {"ok": True})
            self.app.stop()
            return

        if path == "/api/conversaciones":
            try:
                return self._json(201, {"conversation": self.app.conversations.create()})
            except sqlite3.Error:
                logging.exception("No se pudo crear una conversación")
                return self._json(500, {"error": "No se pudo crear la conversación"})

        if path not in ("/api/chat", "/api/imagen"):
            return self._json(404, {"error": "No encontrado"})
        data = self._read_json_body()
        if data is None:
            return
        message = data.get("message")
        if not isinstance(message, str) or not message.strip():
            return self._json(400, {"error": "Mensaje vacio"})
        message = message.strip()

        if path == "/api/imagen":
            return self._generate_image(
                message, data.get("model", CloudflareImageService.DEFAULT_MODEL)
            )
        conversation_id = data.get("conversationId")
        if (
            not isinstance(conversation_id, int)
            or isinstance(conversation_id, bool)
            or conversation_id <= 0
        ):
            return self._json(400, {"error": "Identificador de conversación inválido"})
        try:
            reply = self.app.conversations.send_message(conversation_id, message)
            return self._json(200, {"reply": reply})
        except ConversationNotFoundError:
            return self._json(404, {"error": "Conversación no encontrada"})
        except sqlite3.Error:
            logging.exception("No se pudo guardar el mensaje de la conversación")
            return self._json(500, {"error": "No se pudo guardar el mensaje"})
        except Exception as e:  # igual que el messagebox.showerror del original
            logging.exception("No se pudo completar la solicitud de chat")
            return self._json(502, {"error": str(e)})

    def _read_json_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > self.app.config.max_body:
            self._json(400, {"error": "Mensaje vacio o demasiado largo"})
            return None
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError:
            self._json(400, {"error": "JSON invalido"})
            return None
        if not isinstance(data, dict):
            self._json(400, {"error": "El cuerpo debe ser un objeto JSON"})
            return None
        return data

    @staticmethod
    def _conversation_id_from_path(path: str) -> int | None:
        prefix = "/api/conversaciones/"
        if not path.startswith(prefix):
            return None
        value = path[len(prefix):]
        if not value or "/" in value:
            return None
        try:
            conversation_id = int(value)
        except ValueError:
            return None
        return conversation_id if conversation_id > 0 else None

    def _generate_image(self, prompt: str, model: str):
        if len(prompt) > self.app.config.max_image_prompt:
            return self._json(400, {"error": "La descripción de la imagen es demasiado larga"})
        if not isinstance(model, str) or model not in self.app.image_service.MODELS:
            return self._json(400, {"error": "El modelo de imagen seleccionado no está disponible"})
        try:
            image, content_type = self.app.image_service.generate(prompt, model)
            self._send(200, image, content_type)
        except HTTPError as e:
            self._json(502, {"error": f"Cloudflare respondió HTTP {e.code}"})
        except (URLError, TimeoutError) as e:
            self._json(502, {"error": f"No se pudo contactar al proveedor de imágenes: {e}"})
        except (OSError, ValueError) as e:
            self._json(502, {"error": f"No se pudo generar la imagen: {e}"})

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")
