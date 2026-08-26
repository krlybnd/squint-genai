import unittest

from agentic_shared.core.resources.client import BaseResourceClient, open_resource
from agentic_shared.core.resources.settings import ResourceSettings


class _Settings(ResourceSettings):
    title: str = "test-resource"


class _Client(BaseResourceClient[_Settings]):
    async def health_check(self) -> bool:
        return True


class TestBaseResourceClientLifecycle(unittest.IsolatedAsyncioTestCase):
    def test_init_logs_opening(self) -> None:
        # Act / Assert
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            client = _Client(_Settings())
        self.assertTrue(any("opening test-resource" in line for line in captured.output))
        client.close()

    def test_close_logs_once(self) -> None:
        # Arrange
        client = _Client(_Settings())
        # Act / Assert
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            client.close()
            client.close()
        closing = [line for line in captured.output if "closing test-resource" in line]
        self.assertEqual(len(closing), 1)

    async def test_aclose_logs_closing(self) -> None:
        # Arrange
        client = _Client(_Settings())
        # Act / Assert
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            await client.aclose()
        self.assertTrue(any("closing test-resource" in line for line in captured.output))

    async def test_open_resource_closes_on_exit(self) -> None:
        # Arrange
        client = _Client(_Settings())
        # Act / Assert
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            async with open_resource(client):
                pass
        self.assertTrue(any("closing test-resource" in line for line in captured.output))

    async def test_aexit_logs_error_then_closes(self) -> None:
        # Arrange
        client = _Client(_Settings())
        # Act / Assert
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            with self.assertRaises(RuntimeError):
                async with client:
                    raise RuntimeError("boom")
        output = "\n".join(captured.output)
        self.assertIn("exit test-resource with error", output)
        self.assertIn("closing test-resource", output)


if __name__ == "__main__":
    unittest.main()
