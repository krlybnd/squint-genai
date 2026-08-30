import unittest

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from agentic_shared.frameworks.fastapi.middlewares.security_headers_middleware.middleware import (
    SecurityHeadersMiddleware,
)
from agentic_shared.frameworks.fastapi.middlewares.security_headers_middleware.settings import (
    SecurityHeadersSettings,
)


async def _ok(_request):
    return PlainTextResponse("ok")


class TestSecurityHeadersMiddleware(unittest.TestCase):
    def test_injects_security_headers_when_missing(self) -> None:
        headers = SecurityHeadersSettings().as_headers()
        app = Starlette(routes=[Route("/", _ok)])
        app.add_middleware(SecurityHeadersMiddleware, headers=headers)

        response = TestClient(app).get("/")

        self.assertEqual(response.status_code, 200)
        for header, value in headers.items():
            self.assertEqual(response.headers[header], value)

    def test_does_not_override_existing_headers(self) -> None:
        headers = SecurityHeadersSettings().as_headers()

        async def _custom(_request):
            return PlainTextResponse(
                "ok",
                headers={"X-Frame-Options": "SAMEORIGIN", "X-Content-Type-Options": "nosniff"},
            )

        app = Starlette(routes=[Route("/", _custom)])
        app.add_middleware(SecurityHeadersMiddleware, headers=headers)

        response = TestClient(app).get("/")

        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(response.headers["Referrer-Policy"], headers["Referrer-Policy"])

    def test_uses_headers_from_constructor(self) -> None:
        app = Starlette(routes=[Route("/", _ok)])
        app.add_middleware(
            SecurityHeadersMiddleware,
            headers={"X-Frame-Options": "SAMEORIGIN"},
        )

        response = TestClient(app).get("/")

        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertNotIn("content-security-policy", response.headers)


if __name__ == "__main__":
    unittest.main()
