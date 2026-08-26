import unittest

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from agentic_shared.frameworks.fastapi.bootstrap import apply_standard_http_middleware
from agentic_shared.frameworks.fastapi.cors import CorsSettings


def _cors_kwargs(app: FastAPI) -> dict:
    for item in app.user_middleware:
        if item.cls is CORSMiddleware:
            return item.kwargs
    raise AssertionError("CORSMiddleware not registered")


class TestCors(unittest.TestCase):
    def test_cors_uses_explicit_origins_with_credentials(self) -> None:
        # Arrange
        app = FastAPI()
        apply_standard_http_middleware(
            app,
            cors=CorsSettings(cors_origins="http://localhost:5173,http://localhost"),
        )

        # Act
        kwargs = _cors_kwargs(app)

        # Assert
        self.assertEqual(kwargs["allow_origins"], ["http://localhost:5173", "http://localhost"])
        self.assertTrue(kwargs["allow_credentials"])
        self.assertNotIn("*", kwargs["allow_origins"])

    def test_cors_rejects_wildcard_origin(self) -> None:
        # Act / Assert
        with self.assertRaises(ValueError):
            CorsSettings(cors_origins="http://localhost,*").origin_list()

    def test_cors_rejects_empty_origin_list(self) -> None:
        # Act / Assert
        with self.assertRaises(ValueError):
            CorsSettings(cors_origins="  ,  ").origin_list()


if __name__ == "__main__":
    unittest.main()
