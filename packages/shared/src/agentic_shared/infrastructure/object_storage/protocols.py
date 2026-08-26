from typing import Protocol, runtime_checkable


@runtime_checkable
class ObjectStorageReader(Protocol):
    def object_exists(self, key: str) -> bool: ...

    def download(self, key: str) -> bytes: ...


@runtime_checkable
class ObjectStorageWriter(Protocol):
    def presigned_put_url(
        self,
        key: str,
        *,
        content_type: str = "application/pdf",
        expires_seconds: int | None = None,
    ) -> tuple[str, int]: ...

    def upload(self, key: str, data: bytes, content_type: str = "application/pdf") -> str: ...

    def delete(self, key: str) -> None: ...
