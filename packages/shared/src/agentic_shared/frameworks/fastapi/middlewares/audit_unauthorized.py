import logging
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from agentic_shared.core.compliance.enums import AuditEventCategory
from agentic_shared.core.compliance.models import AuditEvent
from agentic_shared.core.compliance.protocols import AuditLogger
from agentic_shared.domains.persistence.audit_logger import emit_audit

logger = logging.getLogger(__name__)


class AuditUnauthorizedMiddleware(BaseHTTPMiddleware):
    """Record 401 responses when an APP-scoped AuditLogger is in the Dishka container."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        if response.status_code != 401:
            return response
        try:
            container = request.app.state.dishka_container
        except AttributeError:
            return response
        try:
            audit = await container.get(AuditLogger)
        except Exception:
            logger.debug("no AuditLogger in container", exc_info=True)
            return response
        await emit_audit(
            audit,
            AuditEvent(
                category=AuditEventCategory.AUTH,
                action="http.unauthorized",
                outcome="failure",
                metadata={"path": str(request.url.path), "method": request.method},
            ),
        )
        return response
