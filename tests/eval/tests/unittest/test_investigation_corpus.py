import re
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[4] / "resources" / "eval"
FILES = (
    "investigation-dossier-alpha.md",
    "investigation-dossier-beta.md",
    "investigation-dossier-gamma-decoy.md",
)
FORBIDDEN = (
    re.compile(r"\bOTP\b", re.IGNORECASE),
    re.compile(r"\bHoldex\b", re.IGNORECASE),
    re.compile(r"\bNovaBridge\b", re.IGNORECASE),
    re.compile(r"\bTechLine\b", re.IGNORECASE),
    re.compile(r"\b11773377\b"),
    re.compile(r"\b84592163\b"),
    re.compile(r"\bBudapest\b", re.IGNORECASE),
    re.compile(r"Váci\s+út", re.IGNORECASE),
)


def _load() -> dict[str, str]:
    return {name: (CORPUS / name).read_text(encoding="utf-8") for name in FILES}


def test_investigation_dossiers_are_synthetic_and_linked() -> None:
    corpus = _load()
    combined = "\n".join(corpus.values())
    for marker in (
        "SYNTHETIC TEST MATERIAL",
        "Kamuhold Beruházási Zrt.",
        "Kamuhold Építő Kft.",
        "99990001-00000001",
    ):
        assert marker in combined, marker
    alpha, beta, gamma = (
        corpus["investigation-dossier-alpha.md"],
        corpus["investigation-dossier-beta.md"],
        corpus["investigation-dossier-gamma-decoy.md"],
    )
    assert "Kamuhold Beruházási Zrt." in alpha and "Kamuhold Beruházási Zrt." in beta
    assert "99990001-00000001" in alpha and "99990001-00000001" in beta
    assert "KAH-KV-2023/4419" in gamma
    assert "Esther Szabo" in alpha
    assert "99999999-9-99" in alpha
    assert "eszabo.eval-fixture@example.invalid" in alpha
    assert "99999999-9-99" not in gamma
    assert "eszabo.eval-fixture@example.invalid" not in gamma
    assert "+36 99 000 0001" not in gamma
    for pattern in FORBIDDEN:
        assert not pattern.search(combined), pattern.pattern
