import threading
import webbrowser

from .app_config import AppConfig
from .chat_service import OllamaChatService
from .conversation_repository import ConversationRepository
from .conversation_service import ConversationService
from .database import SQLiteDatabase
from .http_server import ChatHTTPServer
from .image_service import CloudflareImageService


class ChatApplication:
    def __init__(self, config: AppConfig):
        self.config = config
        self.chat_service = OllamaChatService(config.chat_model)
        self.database = SQLiteDatabase(config.database_path)
        self.database.initialize()
        self.conversations = ConversationService(
            ConversationRepository(self.database),
            self.chat_service,
            config.chat_history_limit,
        )
        self.image_service = CloudflareImageService(config)
        self.http_server = ChatHTTPServer((config.host, config.port), self)

    def get_info(self) -> dict:
        return {
            "model": self.config.chat_model,
            "imageProvider": "Cloudflare Workers AI",
            "imageModels": self.image_service.available_models(),
            "defaultImageModel": self.image_service.DEFAULT_MODEL,
        }

    def serve_static_file(self, path: str) -> tuple[bytes, str] | None:
        if path == "/":
            path = "/index.html"
        static_dir = (self.config.base_dir / "static").resolve()
        target = (static_dir / path.lstrip("/")).resolve()
        if static_dir not in target.parents or not target.is_file():
            return None
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
        }
        return target.read_bytes(), content_types.get(target.suffix, "application/octet-stream")

    def stop(self):
        threading.Thread(target=self.http_server.shutdown, daemon=True).start()

    def run(self):
        url = f"http://{self.config.host}:{self.config.port}"
        print(f"Chat local con el modelo {self.config.chat_model}")
        print(f"Abre {url} en el navegador (Ctrl+C para detener)")
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        try:
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.http_server.server_close()
            print("Servidor detenido.")
