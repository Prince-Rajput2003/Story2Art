import base64
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from app.database import get_db
from app.main import app
from app.services.auth_service import get_current_user
from app.utils.image_utils import image_to_data_url


class GeneratedImageRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.image_dir = Path(self.temp_dir.name)
        self.image_path = self.image_dir / "sample.png"
        Image.new("RGB", (2, 2), color="purple").save(self.image_path)
        self.image_bytes = self.image_path.read_bytes()

        self.gallery_dir_patch = patch("app.routes.gallery.GENERATED_IMAGES_DIR", self.image_dir)
        self.image_utils_dir_patch = patch("app.utils.image_utils.GENERATED_IMAGES_DIR", self.image_dir)
        self.init_db_patch = patch("app.main.init_db")
        self.gallery_dir_patch.start()
        self.image_utils_dir_patch.start()
        self.init_db_patch.start()
        app.dependency_overrides[get_db] = lambda: _FakeSession()
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id="test-user")
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        self.init_db_patch.stop()
        self.image_utils_dir_patch.stop()
        self.gallery_dir_patch.stop()
        self.temp_dir.cleanup()

    def test_image_route_is_public_with_image_headers(self):
        response = self.client.get("/api/images/sample.png")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertEqual(response.headers["cross-origin-resource-policy"], "cross-origin")
        self.assertEqual(response.content, self.image_bytes)

    def test_image_data_url_contains_correct_mime_and_payload(self):
        data_url = image_to_data_url("sample.png")

        self.assertTrue(data_url.startswith("data:image/png;base64,"))
        encoded_image = data_url.split(",", 1)[1]
        self.assertEqual(base64.b64decode(encoded_image), self.image_bytes)

    def test_generate_response_includes_image_data_url(self):
        wallet = SimpleNamespace(balance=10)
        with (
            patch("app.routes.generate.openai_service.generate_image", return_value=("sample.png", "test")),
            patch("app.routes.generate.get_credit_cost", return_value=1),
            patch("app.routes.generate.get_or_create_wallet", return_value=wallet),
            patch("app.routes.generate.deduct_credits", return_value=wallet),
        ):
            response = self.client.post(
                "/api/generate",
                json={
                    "story": "A test story for generated image response coverage",
                    "image_style": "Cinematic",
                    "aspect_ratio": "1:1",
                    "quality": "low",
                    "enhance_story": False,
                },
            )

        self.assertEqual(response.status_code, 200)
        image = response.json()["image"]
        self.assertEqual(image["filename"], "sample.png")
        self.assertTrue(image["image_url"].endswith("/api/images/sample.png"))
        self.assertTrue(image["image_data_url"].startswith("data:image/png;base64,"))
        self.assertEqual(base64.b64decode(image["image_data_url"].split(",", 1)[1]), self.image_bytes)


class _FakeSession:
    def add(self, _record):
        pass

    def commit(self):
        pass

    def refresh(self, record):
        record.id = "test-generated-image"
        record.created_at = datetime.utcnow()


if __name__ == "__main__":
    unittest.main()
