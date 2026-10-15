import base64
import binascii
import json
from urllib.request import Request, urlopen

from .app_config import AppConfig


class CloudflareImageService:
    DEFAULT_MODEL = "@cf/black-forest-labs/flux-1-schnell"
    MODELS = {
        "@cf/black-forest-labs/flux-1-schnell": {
            "name": "FLUX.1 Schnell",
            "description": "Rápido y equilibrado",
            "parameters": {"steps": 8},
        },
        "@cf/lykon/dreamshaper-8-lcm": {
            "name": "DreamShaper 8 LCM",
            "description": "Estilo artístico y fotorealista",
            "parameters": {"num_steps": 20, "guidance": 7.5},
        },
    }

    def __init__(self, config: AppConfig):
        self.account_id = config.cloudflare_account_id
        self.api_token = config.cloudflare_api_token
        self.max_image_bytes = config.max_image_bytes
        self.max_response_bytes = config.max_image_bytes * 4 // 3 + 64 * 1024
        self.timeout_seconds = config.image_timeout_seconds

    @classmethod
    def available_models(cls) -> list[dict[str, str]]:
        return [
            {"id": model_id, "name": config["name"], "description": config["description"]}
            for model_id, config in cls.MODELS.items()
        ]

    def generate(self, prompt: str, model: str) -> tuple[bytes, str]:
        if not self.account_id or not self.api_token:
            raise ValueError(
                "Configura CLOUDFLARE_ACCOUNT_ID y CLOUDFLARE_API_TOKEN en el archivo .env"
            )
        if model not in self.MODELS:
            raise ValueError("El modelo de imagen seleccionado no está disponible")

        url = (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/ai/run/{model}"
        )
        model_config = self.MODELS[model]
        body = json.dumps({"prompt": prompt, **model_config["parameters"]}).encode("utf-8")
        request = Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ChatOllama/1.0",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            content_type = response.headers.get_content_type()
            response_body = response.read(self.max_response_bytes + 1)
        if len(response_body) > self.max_response_bytes:
            raise ValueError("La respuesta del proveedor supera el tamaño máximo permitido")

        if content_type == "application/json":
            try:
                result = json.loads(response_body)
                encoded_image = result["result"]["image"]
                image = base64.b64decode(encoded_image, validate=True)
                content_type = "image/jpeg" if model == self.DEFAULT_MODEL else "image/png"
            except (binascii.Error, KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
                raise ValueError("Cloudflare no devolvió una imagen válida") from e
        elif content_type.startswith("image/"):
            image = response_body
        else:
            raise ValueError("Cloudflare devolvió un formato de imagen no compatible")

        if len(image) > self.max_image_bytes:
            raise ValueError("La imagen generada supera el tamaño máximo permitido")
        return image, content_type
