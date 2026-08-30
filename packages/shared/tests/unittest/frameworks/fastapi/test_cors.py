import unittest

from starlette.middleware.cors import CORSMiddleware

from agentic_shared.core.package import PackageInfo
from agentic_shared.frameworks.fastapi.framework import FastAPIAppBuilder
from agentic_shared.frameworks.fastapi.middlewares.security_headers_middleware.middleware import (
    SecurityHeadersMiddleware,
)
from agentic_shared.frameworks.fastapi.middlewares.security_headers_middleware.settings import (
    SecurityHeadersSettings,
)
from agentic_shared.frameworks.fastapi.settings import FastAPISettings


def _cors_kwargs(app) -> dict:
    for item in app.user_middleware:
        if item.cls is CORSMiddleware:
            return item.kwargs
    raise AssertionError("CORSMiddleware not registered")


def _build(*, settings: FastAPISettings) -> object:
    return (
        FastAPIAppBuilder(
            PackageInfo(name="test-app", version="0.0.0", description="test"),
            settings=settings,
        )
        .with_standard_middleware()
        .build()
    )


class TestFastAPIAppBuilder(unittest.TestCase):
    def test_cors_uses_explicit_origins_with_credentials(self) -> None:
        app = _build(
            settings=FastAPISettings(cors_origins="http://localhost:5173,http://localhost"),
        )

        kwargs = _cors_kwargs(app)

        self.assertEqual(kwargs["allow_origins"], ["http://localhost:5173", "http://localhost"])
        self.assertTrue(kwargs["allow_credentials"])
        self.assertEqual(kwargs["allow_methods"], ["*"])
        self.assertEqual(kwargs["allow_headers"], ["*"])
        self.assertNotIn("*", kwargs["allow_origins"])
        self.assertEqual(app.title, "test-app")
        self.assertEqual(app.version, "0.0.0")

    def test_cors_rejects_wildcard_origin(self) -> None:
        with self.assertRaises(ValueError):
            _build(settings=FastAPISettings(cors_origins="http://localhost,*"))

    def test_cors_rejects_empty_origin_list(self) -> None:
        with self.assertRaises(ValueError):
            _build(settings=FastAPISettings(cors_origins="  ,  "))

    def test_security_headers_can_be_disabled(self) -> None:
        app = _build(
            settings=FastAPISettings(
                cors_origins="http://localhost",
                security_headers=SecurityHeadersSettings(enabled=False),
            ),
        )

        self.assertFalse(any(item.cls is SecurityHeadersMiddleware for item in app.user_middleware))

    def test_security_headers_passed_from_settings(self) -> None:
        security = SecurityHeadersSettings(x_frame_options="SAMEORIGIN")
        app = _build(
            settings=FastAPISettings(
                cors_origins="http://localhost",
                security_headers=security,
            ),
        )

        item = next(m for m in app.user_middleware if m.cls is SecurityHeadersMiddleware)
        self.assertEqual(item.kwargs["headers"], security.as_headers())


if __name__ == "__main__":
    unittest.main()
