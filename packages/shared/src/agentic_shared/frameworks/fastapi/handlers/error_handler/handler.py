import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agentic_shared.domains.domain_errors import (
    BadRequestError,
    ConflictError,
    DomainError,
    NotFoundError,
)

logger = logging.getLogger(__name__)


def register_domain_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(_request: Request, exc: NotFoundError) -> JSONResponse:
        logger.debug("not found: %s", exc.message)
        return JSONResponse(status_code=404, content={"detail": exc.message})

    @app.exception_handler(ConflictError)
    async def _conflict(_request: Request, exc: ConflictError) -> JSONResponse:
        logger.info("conflict: %s", exc.message)
        return JSONResponse(status_code=409, content={"detail": exc.message})

    @app.exception_handler(BadRequestError)
    async def _bad_request(_request: Request, exc: BadRequestError) -> JSONResponse:
        logger.info("bad request: %s", exc.message)
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(DomainError)
    async def _domain(_request: Request, exc: DomainError) -> JSONResponse:
        logger.info("domain error: %s", exc.message)
        return JSONResponse(status_code=400, content={"detail": exc.message})
