import json
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

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

        if path not in ("/api/chat", "/api/imagen"):
            return self._json(404, {"error": "No encontrado"})
        data = self._read_request_data()
        if data is None:
            return
        message, image_model = data
        if not message:
            return self._json(400, {"error": "Mensaje vacio"})

        if path == "/api/imagen":
            return self._generate_image(message, image_model)
        try:
            self._json(200, {"reply": self.app.chat_service.ask(message)})
        except Exception as e:  # igual que el messagebox.showerror del original
            self._json(502, {"error": str(e)})

    def _read_request_data(self) -> tuple[str, str] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > self.app.config.max_body:
            self._json(400, {"error": "Mensaje vacio o demasiado largo"})
            return None
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            message = str(data.get("message", "")).strip()
            image_model = data.get("model", CloudflareImageService.DEFAULT_MODEL)
        except (ValueError, AttributeError):
            self._json(400, {"error": "JSON invalido"})
            return None
        return message, image_model

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
