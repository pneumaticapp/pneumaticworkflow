import re
from typing import Optional
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from src.generics.mixins.views import AnonymousMixin
from src.logs.events.context import (
    RequestContext,
    reset_context,
    set_context,
)

REQUEST_ID_META = 'HTTP_X_REQUEST_ID'
REQUEST_ID_HEADER = 'X-Request-ID'
REAL_IP_META = 'HTTP_X_REAL_IP'
# A client supplied id goes into every event and into the response
# header, so only a short safe value is accepted.
REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._~+/=-]{1,64}\Z')
# A header is whatever length a client sent, and every event of the
# request carries it.
USER_AGENT_MAX = 500


class EventContextMiddleware(
    AnonymousMixin,
    MiddlewareMixin,
):

    """ Give every request a correlation id and publish its ip and
        user agent to the contextvar read by emit().

        Who acts is not here: DRF authenticates after the middleware
        chain, and the caller names the actor in its call of
        AuditEventService. """

    def _user_ip(self, request: HttpRequest) -> Optional[str]:

        """ X-Real-IP first, the address our nginx writes and the one
            the tokens of a session carry; a request that came around
            nginx falls back to AnonymousMixin. X-Forwarded-For, which
            AnonymousMixin reads first, keeps whatever the client sent
            in front of the address nginx appends. """

        return request.META.get(REAL_IP_META) or self.get_user_ip(request)

    def _user_agent(self, request: HttpRequest) -> Optional[str]:
        user_agent = self.get_user_agent(request)
        if not user_agent:
            return None
        return user_agent[:USER_AGENT_MAX]

    @staticmethod
    def _request_id(request: HttpRequest) -> str:
        request_id = request.META.get(REQUEST_ID_META)
        if request_id and REQUEST_ID_PATTERN.match(request_id):
            return request_id
        return uuid4().hex

    @staticmethod
    def _reset(request: HttpRequest):
        token = getattr(request, '_event_context_token', None)
        if token is None:
            return
        request._event_context_token = None
        reset_context(token)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            return super().__call__(request)
        finally:
            # The one place the context is reset: process_response is
            # skipped when an inner middleware raises, and this runs
            # either way, so the context cannot leak to the next
            # request of the same thread.
            self._reset(request)

    def process_request(self, request: HttpRequest):
        request.request_id = self._request_id(request)
        request._event_context_token = set_context(
            RequestContext(
                request_id=request.request_id,
                ip=self._user_ip(request),
                user_agent=self._user_agent(request),
            ),
        )

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse,
    ) -> HttpResponse:
        request_id = getattr(request, 'request_id', None)
        if request_id:
            response[REQUEST_ID_HEADER] = request_id
        return response
