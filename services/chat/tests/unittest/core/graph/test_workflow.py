import unittest

from agentic_chat.core.graph.enums import AgentGraphNode
from agentic_chat.core.graph.workflow import route_after_guard


class TestAgentWorkflow(unittest.TestCase):
    def test_route_after_guard_blocked(self) -> None:
        # Act / Assert
        self.assertEqual(route_after_guard({"guard_blocked": True}), AgentGraphNode.BLOCK)

    def test_route_after_guard_ok(self) -> None:
        # Act / Assert
        self.assertEqual(route_after_guard({"guard_blocked": False}), AgentGraphNode.REWRITE)


if __name__ == "__main__":
    unittest.main()
