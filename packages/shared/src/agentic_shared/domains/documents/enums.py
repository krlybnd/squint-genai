from enum import StrEnum


class IndexStatus(StrEnum):
    INDEXED = "indexed"
    INDEXING = "indexing"
    FAILED = "failed"
    PENDING = "pending"
