"""Load a JSON golden file by dispatching each row to the first matching parser."""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from typing import ClassVar

from agentic_eval.core.golden.abstention import AbstentionGolden
from agentic_eval.core.golden.base import Golden
from agentic_eval.core.golden.labeled import LabeledGolden
from agentic_eval.core.golden.settings import GoldenSettings


class GoldenDataset:
    """Ordered goldens. Add a kind by subclassing ``Golden`` and appending ``parsers``."""

    parsers: ClassVar[tuple[type[Golden], ...]] = (AbstentionGolden, LabeledGolden)

    def __init__(self, items: Sequence[Golden]) -> None:
        self._items = tuple(items)

    def __iter__(self) -> Iterator[Golden]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> Golden:
        return self._items[index]

    @classmethod
    def load(cls, settings: GoldenSettings | None = None) -> GoldenDataset:
        cfg = settings if settings is not None else GoldenSettings()
        raw = json.loads(cfg.dataset_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise TypeError(f"golden dataset must be a JSON list: {cfg.dataset_path}")
        return cls([cls.parse(item, known_source_files=cfg.known_source_files) for item in raw])

    @classmethod
    def parse(cls, raw: object, *, known_source_files: Sequence[str]) -> Golden:
        for parser in cls.parsers:
            if parser.matches(raw):
                return parser.parse(raw, known_source_files=known_source_files)
        raise ValueError(f"no golden parser matched: {raw!r}")

    @property
    def labeled(self) -> tuple[LabeledGolden, ...]:
        return tuple(item for item in self._items if isinstance(item, LabeledGolden))

    @property
    def abstention(self) -> tuple[AbstentionGolden, ...]:
        return tuple(item for item in self._items if isinstance(item, AbstentionGolden))
