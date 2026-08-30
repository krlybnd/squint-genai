from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentic_shared.integrations.idp.keycloak.client import KeycloakAdminClientFactory  # noqa: E402
from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings  # noqa: E402


class TestKeycloakAdminClientFactory(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_token_posts_client_credentials(self) -> None:
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"access_token": "tok-1"}
        http = MagicMock()
        http.post = AsyncMock(return_value=response)
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "agentic_shared.integrations.idp.keycloak.client.httpx.AsyncClient",
            return_value=http,
        ):
            factory = KeycloakAdminClientFactory(KeycloakAdminSettings())
            token = await factory.fetch_token()

        self.assertEqual(token, "tok-1")
        http.post.assert_awaited_once()
        kwargs = http.post.await_args.kwargs
        self.assertEqual(kwargs["data"]["grant_type"], "client_credentials")

    async def test_fetch_token_rejects_missing_access_token(self) -> None:
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {}
        http = MagicMock()
        http.post = AsyncMock(return_value=response)
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "agentic_shared.integrations.idp.keycloak.client.httpx.AsyncClient",
            return_value=http,
        ):
            factory = KeycloakAdminClientFactory(KeycloakAdminSettings())
            with self.assertRaises(RuntimeError):
                await factory.fetch_token()
