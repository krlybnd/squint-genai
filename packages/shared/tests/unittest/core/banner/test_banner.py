import unittest
from io import StringIO
from unittest.mock import patch

from agentic_shared.core.banner import print_startup_banner
from agentic_shared.core.package import PackageInfo

_LOGO_MARK = "┓╹"


class TestBanner(unittest.TestCase):
    def test_print_uses_package_info(self) -> None:
        stream = StringIO()
        print_startup_banner(
            PackageInfo(name="agentic-api", version="0.2.0", description="api"),
            stream=stream,
            shared=None,
        )

        text = stream.getvalue()
        self.assertIn(_LOGO_MARK, text)
        self.assertIn("agentic-api  v0.2.0", text)
        self.assertNotIn("agentic-shared", text)

    def test_print_startup_banner_loads_distribution(self) -> None:
        stream = StringIO()
        info = PackageInfo(name="agentic-chat", version="9.9.9", description="chat svc")
        shared = PackageInfo(name="agentic-shared", version="1.2.3", description="lib")

        with patch(
            "agentic_shared.core.banner.PackageInfo.from_distribution",
            side_effect=lambda name, **_: info if name == "agentic-chat" else shared,
        ):
            print_startup_banner("agentic-chat", stream=stream)

        text = stream.getvalue()
        self.assertIn("agentic-chat  v9.9.9", text)
        self.assertIn("agentic-shared  v1.2.3", text)
        self.assertIn(_LOGO_MARK, text)

    def test_skips_shared_line_when_same_package(self) -> None:
        stream = StringIO()
        shared = PackageInfo(name="agentic-shared", version="1.0.0", description="lib")
        print_startup_banner(shared, stream=stream, shared=shared)

        text = stream.getvalue()
        self.assertEqual(text.count("agentic-shared"), 1)


class TestPackageInfo(unittest.TestCase):
    def test_from_distribution_reads_installed_shared(self) -> None:
        info = PackageInfo.from_distribution("agentic-shared")

        self.assertEqual(info.name, "agentic-shared")
        self.assertTrue(info.version)
        self.assertIn("Shared", info.description)

    def test_from_distribution_fallback_when_missing(self) -> None:
        info = PackageInfo.from_distribution(
            "definitely-not-installed-xyz",
            fallback_name="fallback",
        )

        self.assertEqual(info.name, "fallback")
        self.assertEqual(info.version, "0.0.0")
        self.assertEqual(info.description, "")


if __name__ == "__main__":
    unittest.main()
