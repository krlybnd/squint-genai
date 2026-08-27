import asyncio

from agentic_eval.modules.generation.app import answer_questions


class _FakeGraph:
    async def ainvoke(self, state: object, config: object) -> dict[str, object]:
        return {"answer": "ok", "retrieved_chunks": [{"text": "ctx"}]}


def test_answer_questions_preserves_order() -> None:
    # Arrange
    graph = _FakeGraph()

    # Act
    results = asyncio.run(
        answer_questions(
            ["first", "second"],
            tenant_id="tenant-a",
            graph=graph,
            max_concurrent=2,
        )
    )

    # Assert
    assert [item.answer for item in results] == ["ok", "ok"]
    assert [item.contexts for item in results] == [["ctx"], ["ctx"]]
