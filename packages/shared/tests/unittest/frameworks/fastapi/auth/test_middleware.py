import unittest

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from agentic_shared.frameworks.fastapi.auth.middleware import (
    SECURITY_HEADERS,
    SecurityHeadersMiddleware,
)


async def _ok(_request):
    return PlainTextResponse("ok")


class TestSecurityHeadersMiddleware(unittest.TestCase):
    def test_injects_security_headers_when_missing(self) -> None:
        # Arrange
        app = Starlette(routes=[Route("/", _ok)])
        app.add_middleware(SecurityHeadersMiddleware)

        # Act
        response = TestClient(app).get("/")

        # Assert
        self.assertEqual(response.status_code, 200)
        for header, value in SECURITY_HEADERS.items():
            self.assertEqual(response.headers[header], value)

    def test_does_not_override_existing_headers(self) -> None:
        # Arrange
        async def _custom(_request):
            return PlainTextResponse(
                "ok",
                headers={"X-Frame-Options": "SAMEORIGIN", "X-Content-Type-Options": "nosniff"},
            )

        app = Starlette(routes=[Route("/", _custom)])
        app.add_middleware(SecurityHeadersMiddleware)

        # Act
        response = TestClient(app).get("/")

        # Assert
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(response.headers["Referrer-Policy"], SECURITY_HEADERS["Referrer-Policy"])


if __name__ == "__main__":
    unittest.main()
