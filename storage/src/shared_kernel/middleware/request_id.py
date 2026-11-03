"""Correlation id of a request: header in, state and header out."""

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

from src.shared_kernel.http_context import (
    REQUEST_ID_HEADER,
    resolve_request_id,
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Store the request id and echo it in the response."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Resolve the id before the request, add the header after."""
        request_id = resolve_request_id(
            request.headers.get(REQUEST_ID_HEADER),
        )
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
