from collections.abc import Awaitable, Callable, Mapping

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, headers: Mapping[str, str]) -> None:
        super().__init__(app)
        self._headers = dict(headers)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for header, value in self._headers.items():
            if header not in response.headers:
                response.headers[header] = value
        return response
