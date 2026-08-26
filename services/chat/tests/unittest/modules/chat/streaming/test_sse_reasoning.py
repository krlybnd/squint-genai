import unittest

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.modules.chat.enums import ReasoningStatus, ReasoningStep
from agentic_chat.modules.chat.streaming.sse_reasoning_handlers import NODE_DONE_HANDLERS
from agentic_chat.modules.chat.streaming.sse_transitions import active_events_after


class TestSseReasoning(unittest.TestCase):
    _ACTIVE_CASES = [
        (AgentGraphNode.PLAN, {}, [ReasoningStep.GUARD]),
        (AgentGraphNode.GUARD, {"guard_blocked": True}, [ReasoningStep.GENERATE]),
        (AgentGraphNode.GUARD, {"guard_blocked": False}, [ReasoningStep.REWRITE]),
        (AgentGraphNode.REWRITE, {"needs_retrieval": True}, [ReasoningStep.RETRIEVE]),
        (AgentGraphNode.REWRITE, {"needs_retrieval": False}, [ReasoningStep.GENERATE]),
        (
            AgentGraphNode.RETRIEVE,
            {"retrieved_chunks": [{"chunk_id": "a"}]},
            [ReasoningStep.GENERATE],
        ),
    ]

    def test_active_events_after(self) -> None:
        # Arrange / Act / Assert
        for node, output, expected_steps in self._ACTIVE_CASES:
            with self.subTest(node=node, output=output):
                events = active_events_after(node, output, "en")
                self.assertEqual(len(events), len(expected_steps) * 2)
                for step in expected_steps:
                    self.assertTrue(
                        any(f'"step": "{step}"' in event for event in events),
                        msg=f"missing step {step} in events",
                    )

    def test_plan_done_handler(self) -> None:
        # Act
        data = NODE_DONE_HANDLERS[AgentGraphNode.PLAN]({"query": "hello"}, "en")

        # Assert
        self.assertIs(data.step, ReasoningStep.PLAN)
        self.assertIs(data.status, ReasoningStatus.DONE)
        self.assertIn("hello", data.message)


if __name__ == "__main__":
    unittest.main()
