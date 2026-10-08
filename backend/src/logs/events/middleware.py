import re
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from src.generics.mixins.views import AnonymousMixin
from src.logs.events.entities import RequestContext, request_context

REQUEST_ID_META = 'HTTP_X_REQUEST_ID'
REQUEST_ID_HEADER = 'X-Request-ID'
REAL_IP_META = 'HTTP_X_REAL_IP'
REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9._~+/=-]{1,64}\Z')
USER_AGENT_MAX = 500


class EventContextMiddleware(AnonymousMixin, MiddlewareMixin):
    """Publish request metadata and restore the prior context on exit."""

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            return super().__call__(request)
        finally:
            context = getattr(request, '_event_context', None)
            if context is not None:
                request._event_context = None
                request_context.reset(context)

    def process_request(self, request: HttpRequest):
        request_id = request.META.get(REQUEST_ID_META)
        if not request_id or not REQUEST_ID_PATTERN.match(request_id):
            request_id = uuid4().hex
        request.request_id = request_id
        user_agent = self.get_user_agent(request)
        user_agent = user_agent[:USER_AGENT_MAX] if user_agent else None
        # nginx supplies X-Real-IP; requests outside nginx use the fallback.
        ip = request.META.get(REAL_IP_META) or self.get_user_ip(request)
        request._event_context = request_context.set(
            RequestContext(
                request_id=request_id,
                ip=ip,
                user_agent=user_agent,
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
