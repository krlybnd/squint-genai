import unittest

from agentic_shared.core.resources.client import BaseResourceClient
from agentic_shared.core.resources.settings import ResourceSettings


class _Settings(ResourceSettings):
    title: str = "test-resource"


class _Client(BaseResourceClient[_Settings]):
    async def health_check(self) -> bool:
        return True


class TestBaseResourceClientLifecycle(unittest.IsolatedAsyncioTestCase):
    async def test_aenter_logs_opened(self) -> None:
        client = _Client(_Settings())
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            async with client:
                pass
        self.assertTrue(any("opened test-resource" in line for line in captured.output))
        self.assertTrue(any("closed test-resource" in line for line in captured.output))

    def test_close_logs_once(self) -> None:
        client = _Client(_Settings())
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            client.close()
            client.close()
        closing = [line for line in captured.output if "closed test-resource" in line]
        self.assertEqual(len(closing), 1)

    async def test_aclose_logs_closed(self) -> None:
        client = _Client(_Settings())
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            await client.aclose()
        self.assertTrue(any("closed test-resource" in line for line in captured.output))

    async def test_aexit_logs_error_then_closes(self) -> None:
        client = _Client(_Settings())
        with self.assertLogs(_Client.__module__, level="INFO") as captured:
            with self.assertRaises(RuntimeError):
                async with client:
                    raise RuntimeError("boom")
        output = "\n".join(captured.output)
        self.assertIn("opened test-resource", output)
        self.assertIn("exit test-resource with error", output)
        self.assertIn("closed test-resource", output)


if __name__ == "__main__":
    unittest.main()
