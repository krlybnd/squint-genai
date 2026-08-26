import unittest

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.modules.chat.enums import ReasoningStatus, ReasoningStep
from agentic_chat.modules.chat.streaming.sse_reasoning_handlers import NODE_DONE_HANDLERS


class TestSseReasoningHandlers(unittest.TestCase):
    def test_guard_blocked(self) -> None:
        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.GUARD](
            {"guard_blocked": True, "guard_reason": "injection detected"},
            "en",
        )

        # Assert
        self.assertIs(data.step, ReasoningStep.GUARD)
        self.assertIs(data.status, ReasoningStatus.DONE)
        self.assertIn("injection detected", data.message)

    def test_guard_pii_redactions(self) -> None:
        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.GUARD](
            {
                "guard_blocked": False,
                "pii_redactions": 2,
                "pii_details": [{"kind": "email", "placeholder": "[EMAIL]"}],
                "safe_query": "contact [EMAIL]",
            },
            "en",
        )

        # Assert
        self.assertIn("(2)", data.message)
        self.assertEqual(data.pii_redactions, 2)
        self.assertEqual(data.safe_query, "contact [EMAIL]")

    def test_guard_ok_without_redactions(self) -> None:
        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.GUARD](
            {"guard_blocked": False, "pii_redactions": 0, "guard_reason": "ok"},
            "en",
        )

        # Assert
        self.assertEqual(data.message, "ok")

    def test_rewrite_with_search_query(self) -> None:
        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.REWRITE](
            {
                "needs_retrieval": True,
                "search_query": "contract terms",
                "rewrite_reason": "doc search",
                "indexed_document_count": 5,
            },
            "en",
        )

        # Assert
        self.assertIs(data.step, ReasoningStep.REWRITE)
        self.assertIn("contract terms", data.message)
        self.assertTrue(data.needs_retrieval)
        self.assertEqual(data.indexed_document_count, 5)

    def test_rewrite_needs_retrieval_without_search_query(self) -> None:
        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.REWRITE](
            {"needs_retrieval": True, "search_query": "", "rewrite_reason": "fallback reason"},
            "en",
        )

        # Assert
        self.assertIn("fallback reason", data.message)

    def test_rewrite_no_retrieval(self) -> None:
        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.REWRITE](
            {"needs_retrieval": False, "rewrite_reason": "small talk"},
            "en",
        )

        # Assert
        self.assertFalse(data.needs_retrieval)
        self.assertIn("small talk", data.message)

    def test_retrieve_done(self) -> None:
        # Arrange
        output = {
            "retrieved_chunks": [{"chunk_id": "a"}, {"chunk_id": "b"}],
            "search_meta": {"skipped": False},
        }

        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.RETRIEVE](output, "en")

        # Assert
        self.assertIs(data.step, ReasoningStep.RETRIEVE)
        self.assertEqual(data.chunks, 2)

    def test_generate_done(self) -> None:
        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.GENERATE]({}, "en")

        # Assert
        self.assertIs(data.step, ReasoningStep.GENERATE)
        self.assertIs(data.status, ReasoningStatus.DONE)

    def test_block_uses_generate_done_handler(self) -> None:
        # Act
        generate = NODE_DONE_HANDLERS[AgentGraphNode.GENERATE]({}, "en")
        block = NODE_DONE_HANDLERS[AgentGraphNode.BLOCK]({}, "en")

        # Assert
        self.assertEqual(generate.step, block.step)
        self.assertEqual(generate.message, block.message)


if __name__ == "__main__":
    unittest.main()
