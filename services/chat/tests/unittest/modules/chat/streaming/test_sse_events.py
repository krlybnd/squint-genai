import unittest

from fastapi import FastAPI

from agentic_chat.modules.chat.router import router
from agentic_chat.modules.chat.streaming.sse_events import SSE_MEDIA_TYPE, parse_sse_chunk


class TestSseEvents(unittest.TestCase):
    def test_parse_sse_chunk(self) -> None:
        # Arrange
        chunk = 'event: token\ndata: {"content": "hi"}\n\n'

        # Act
        parsed = parse_sse_chunk(chunk)

        # Assert
        self.assertEqual(parsed, {"event": "token", "data": '{"content": "hi"}'})

    def test_stream_and_replay_openapi_is_sse_not_json(self) -> None:
        # Arrange
        app = FastAPI()
        app.include_router(router)

        # Act
        spec = app.openapi()

        # Assert
        for path in (
            "/v1/chat/sessions/{session_id}/stream",
            "/v1/chat/sessions/{session_id}/replay",
        ):
            content = spec["paths"][path]["post"]["responses"]["200"]["content"]
            self.assertIn(SSE_MEDIA_TYPE, content)
            self.assertNotIn("application/json", content)
            self.assertEqual(content[SSE_MEDIA_TYPE]["schema"]["type"], "string")


if __name__ == "__main__":
    unittest.main()
