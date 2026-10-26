import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch

from backend.app_config import AppConfig
from backend.image_service import CloudflareImageService


class CloudflareImageServiceTests(unittest.TestCase):
    def setUp(self):
        self.config = AppConfig(
            base_dir=Path(tempfile.gettempdir()),
            cloudflare_account_id="account-id",
            cloudflare_api_token="secret-token",
        )

    def test_phoenix_is_the_default_and_is_available(self):
        service = CloudflareImageService(self.config)

        self.assertEqual(service.DEFAULT_MODEL, "@cf/leonardo/phoenix-1.0")
        self.assertIn(
            service.DEFAULT_MODEL,
            {model["id"] for model in service.available_models()},
        )

    def test_generate_sends_bearer_token_and_phoenix_parameters(self):
        image_bytes = b"generated image"
        headers = Message()
        headers["Content-Type"] = "image/jpeg"

        class Response:
            def __init__(self, response_headers, response_body):
                self.headers = response_headers
                self.response_body = response_body

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self, _limit):
                return self.response_body

        with patch(
            "backend.image_service.urlopen",
            return_value=Response(headers, image_bytes),
        ) as urlopen:
            image, content_type = CloudflareImageService(self.config).generate(
                "Un paisaje al atardecer",
                CloudflareImageService.DEFAULT_MODEL,
            )

        request = urlopen.call_args.args[0]
        authorization = request.get_header("Authorization")
        self.assertTrue(authorization.startswith("Bearer "))
        self.assertTrue(authorization.endswith(self.config.cloudflare_api_token))
        self.assertEqual(
            json.loads(request.data),
            {
                "prompt": "Un paisaje al atardecer",
                "width": 1024,
                "height": 1024,
                "num_steps": 25,
            },
        )
        self.assertEqual(image, image_bytes)
        self.assertEqual(content_type, "image/jpeg")


if __name__ == "__main__":
    unittest.main()
