import ollama


class OllamaChatService:
    def __init__(self, model: str):
        self.model = model

    def ask(self, message: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": message}],
        )
        return response["message"]["content"]
