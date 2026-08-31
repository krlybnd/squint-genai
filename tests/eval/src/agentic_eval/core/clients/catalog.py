"""Index catalog checks shared by generation and retrieval live suites."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path


def catalog_blockers(
    rows: Sequence[tuple[str, str]],
    expected: Sequence[str],
) -> str | None:
    """Return a blocking reason if the indexed catalog cannot support the goldens."""
    by_name: dict[str, list[str]] = defaultdict(list)
    by_stem: dict[str, set[str]] = defaultdict(set)
    for source_file, doc_id in rows:
        by_name[source_file].append(doc_id)
        by_stem[Path(source_file).stem].add(source_file)
    dupes = [name for name, ids in by_name.items() if len(set(ids)) > 1]
    mixed = [stem for stem, names in by_stem.items() if len(names) > 1]
    missing = [name for name in expected if name not in by_name and Path(name).stem not in by_stem]
    if not dupes and not mixed and not missing:
        return None
    return f"index catalog blocking: dupes={dupes} mixed={mixed} missing={missing}"
