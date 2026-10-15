import ollama


class OllamaChatService:
    def __init__(self, model: str):
        self.model = model

    def ask(self, message: str, history: list[dict[str, str]] | None = None) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[
                *(history or []),
                {"role": "user", "content": message},
            ],
        )
        return response["message"]["content"]
