import unittest
from io import StringIO

from agentic_shared.core.banner import LOGO, print_startup_banner, render_startup_banner


class TestBanner(unittest.TestCase):
    def test_render_startup_banner_includes_logo_and_service(self) -> None:
        # Act
        text = render_startup_banner("api", "0.1.0")

        # Assert
        self.assertTrue(text.startswith(LOGO))
        self.assertIn("api", text)
        self.assertIn("v0.1.0", text)

    def test_print_startup_banner_writes_stdout(self) -> None:
        # Arrange
        stream = StringIO()

        # Act
        print_startup_banner("chat", stream=stream)

        # Assert
        self.assertIn("chat", stream.getvalue())
        self.assertIn("▙▘▛▘", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
