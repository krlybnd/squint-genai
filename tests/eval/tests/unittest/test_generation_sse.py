from agentic_eval.core.clients.sse import parse_sse, strip_vault_marks


def test_strip_vault_marks_keeps_plaintext() -> None:
    # Arrange
    marked = "Tax ID [[vault:<HU_TAX_AABBCCDD>]]99999999-9-99[[/vault]] on file."

    # Act
    plain = strip_vault_marks(marked)

    # Assert
    assert plain == "Tax ID 99999999-9-99 on file."
    assert "<HU_TAX_AABBCCDD>" not in plain


def test_parse_sse_reads_done_answer_and_error() -> None:
    # Arrange
    raw = (
        'event: token\ndata: {"content": "Hel"}\n\n'
        'event: done\ndata: {"answer": "Hello", "citations": [{"excerpt": "src"}]}\n\n'
    )

    # Act
    events = parse_sse(raw)

    # Assert
    assert events[0] == ("token", {"content": "Hel"})
    assert events[1][0] == "done"
    assert events[1][1]["answer"] == "Hello"
    assert parse_sse('event: error\ndata: {"message": "boom"}\n\n')[0][0] == "error"
