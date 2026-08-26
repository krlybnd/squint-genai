import unittest

from agentic_chat.modules.chat.streaming.sse_events import parse_sse_chunk


class TestSseEvents(unittest.TestCase):
    def test_parse_sse_chunk(self) -> None:
        # Arrange
        chunk = 'event: token\ndata: {"content": "hi"}\n\n'

        # Act
        parsed = parse_sse_chunk(chunk)

        # Assert
        self.assertEqual(parsed, {"event": "token", "data": '{"content": "hi"}'})


if __name__ == "__main__":
    unittest.main()
