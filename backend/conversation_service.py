from .chat_service import OllamaChatService
from .conversation_repository import ConversationRepository


class ConversationNotFoundError(Exception):
    pass


class ConversationService:
    def __init__(
        self,
        repository: ConversationRepository,
        chat_service: OllamaChatService,
        history_limit: int,
    ):
        self.repository = repository
        self.chat_service = chat_service
        self.history_limit = history_limit

    def create(self) -> dict:
        return self.repository.create()

    def list(self) -> list[dict]:
        return self.repository.list()

    def get(self, conversation_id: int) -> dict:
        conversation = self.repository.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation

    def send_message(self, conversation_id: int, message: str) -> str:
        if not self.repository.exists(conversation_id):
            raise ConversationNotFoundError(conversation_id)
        history = self.repository.get_recent_messages(
            conversation_id, self.history_limit
        )
        reply = self.chat_service.ask(message, history)
        self.repository.add_exchange(conversation_id, message, reply)
        return reply
