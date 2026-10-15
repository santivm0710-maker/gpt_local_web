import json
import threading
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request, urlopen

from backend.conversation_repository import ConversationRepository
from backend.conversation_service import ConversationService
from backend.database import SQLiteDatabase
from backend.http_server import ChatHTTPServer


class StubChatService:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def ask(self, message, history=None):
        self.calls.append((message, history or []))
        if self.error is not None:
            raise self.error
        return f"Respuesta: {message}"


class ConversationRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.database = SQLiteDatabase(Path(self.temp_dir.name) / "nested" / "chat.db")
        self.database.initialize()

    def test_schema_initialization_is_repeatable_and_exchange_is_persisted(self):
        self.database.initialize()
        repository = ConversationRepository(self.database)
        conversation = repository.create()

        repository.add_exchange(conversation["id"], "Hola, ¿qué tal?", "Muy bien.")

        stored = repository.get(conversation["id"])
        self.assertEqual(stored["title"], "Hola, ¿qué tal?")
        self.assertEqual(
            [(message["role"], message["content"]) for message in stored["messages"]],
            [("user", "Hola, ¿qué tal?"), ("assistant", "Muy bien.")],
        )
        self.assertEqual(repository.list()[0]["message_count"], 2)

    def test_service_passes_saved_context_and_limits_history(self):
        repository = ConversationRepository(self.database)
        conversation = repository.create()
        chat = StubChatService()
        service = ConversationService(repository, chat, history_limit=2)

        service.send_message(conversation["id"], "Primer mensaje")
        service.send_message(conversation["id"], "Segundo mensaje")

        self.assertEqual(chat.calls[0], ("Primer mensaje", []))
        self.assertEqual(
            chat.calls[1],
            (
                "Segundo mensaje",
                [
                    {"role": "user", "content": "Primer mensaje"},
                    {"role": "assistant", "content": "Respuesta: Primer mensaje"},
                ],
            ),
        )

    def test_failed_model_request_does_not_persist_an_exchange(self):
        repository = ConversationRepository(self.database)
        conversation = repository.create()

        service = ConversationService(
            repository,
            StubChatService(RuntimeError("Ollama no está disponible")),
            history_limit=20,
        )
        with self.assertRaisesRegex(RuntimeError, "Ollama no está disponible"):
            service.send_message(conversation["id"], "Hola")

        self.assertEqual(repository.get(conversation["id"])["messages"], [])


class ConversationApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        database = SQLiteDatabase(Path(self.temp_dir.name) / "chat.db")
        database.initialize()
        service = ConversationService(
            ConversationRepository(database), StubChatService(), history_limit=20
        )
        app = SimpleNamespace(
            conversations=service,
            config=SimpleNamespace(max_body=64 * 1024),
            image_service=SimpleNamespace(MODELS={}),
        )
        self.server = ChatHTTPServer(("127.0.0.1", 0), app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/json"} if data else {},
            method=method,
        )
        with urlopen(request) as response:
            return response.status, json.loads(response.read())

    def test_create_send_and_reload_conversation(self):
        status, listed = self.request("GET", "/api/conversaciones")
        self.assertEqual(status, 200)
        self.assertEqual(listed["conversations"], [])

        status, created = self.request("POST", "/api/conversaciones")
        conversation_id = created["conversation"]["id"]
        self.assertEqual(status, 201)

        status, answer = self.request(
            "POST",
            "/api/chat",
            {"conversationId": conversation_id, "message": "Hola"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(answer["reply"], "Respuesta: Hola")

        status, loaded = self.request(
            "GET", f"/api/conversaciones/{conversation_id}"
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            [message["role"] for message in loaded["conversation"]["messages"]],
            ["user", "assistant"],
        )


if __name__ == "__main__":
    unittest.main()
