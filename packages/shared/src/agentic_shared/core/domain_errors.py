"""Domain-level errors mapped to HTTP status in FastAPI apps."""


class DomainError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class BadRequestError(DomainError):
    pass
