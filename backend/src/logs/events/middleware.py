import re
from uuid import uuid4

from django.utils.deprecation import MiddlewareMixin

from src.logs.events.context import (
    context_from_request,
    reset_context,
    set_context,
)

REQUEST_ID_META = 'HTTP_X_REQUEST_ID'
REQUEST_ID_HEADER = 'X-Request-ID'
# A client supplied id goes into every event and into the response
# header, so only a short safe value is accepted.
REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._~+/=-]{1,64}\Z')


class EventContextMiddleware(MiddlewareMixin):

    """ Give every request a correlation id and publish its ip,
        user agent and actor to the contextvar read by emit(). """

    def __call__(self, request):
        try:
            return super().__call__(request)
        finally:
            # The one place the context is reset: process_response is
            # skipped when an inner middleware raises, and this runs
            # either way, so the context cannot leak to the next
            # request of the same thread.
            self._reset(request)

    def process_request(self, request) -> None:
        request.request_id = self._request_id(request)
        request._event_context_token = set_context(
            context_from_request(request),
        )

    def process_response(self, request, response):
        request_id = getattr(request, 'request_id', None)
        if request_id:
            response[REQUEST_ID_HEADER] = request_id
        return response

    @staticmethod
    def _request_id(request) -> str:
        request_id = request.META.get(REQUEST_ID_META)
        if request_id and REQUEST_ID_PATTERN.match(request_id):
            return request_id
        return uuid4().hex

    @staticmethod
    def _reset(request) -> None:
        token = getattr(request, '_event_context_token', None)
        if token is None:
            return
        request._event_context_token = None
        reset_context(token)
