# pylint: disable=attribute-defined-outside-init
# All about this file only exists because original AsgiHandler from
# channels doesn't works propertly, and does things, that developers could have
# avoided (sync_to_async decorator, for example). If we use a parent handler,
# it will spam the console with errors, if you send a couple of requests in one
# moment. At browser that will looks like CORS-policy error, but the real
# culprit is not CORS, but async mind games.


import logging
import sys

from channels.exceptions import RequestAborted, RequestTimeout
from channels.http import AsgiHandler as ChannelsAsgiHandler
from django import http
from django.conf import settings
from django.core import signals
from django.core.exceptions import RequestDataTooBig
from django.http import FileResponse, HttpResponse
from django.urls import set_script_prefix

logger = logging.getLogger("django.request")


class AsgiHandler(ChannelsAsgiHandler):
    # All methods have been copied and slightly modified from the parent-class
    # If you wanna know what happens here - look in the parent class
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            raise ValueError(
                "The AsgiHandler can only handle HTTP connections, not %s"
                % scope["type"]
            )
        self.scope = scope
        self.send = send

        try:
            body_stream = await self.read_body(receive)
        except RequestAborted:
            return
        await self.handle(body_stream)

    async def handle(self, body):
        script_prefix = self.scope.get("root_path", "") or ""
        if settings.FORCE_SCRIPT_NAME:
            script_prefix = settings.FORCE_SCRIPT_NAME
        set_script_prefix(script_prefix)
        signals.request_started.send(sender=self.__class__, scope=self.scope)
        try:
            request = self.request_class(self.scope, body)
        except UnicodeDecodeError:
            logger.warning(
                "Bad Request (UnicodeDecodeError)",
                exc_info=sys.exc_info(),
                extra={"status_code": 400},
            )
            response = http.HttpResponseBadRequest()
        except RequestTimeout:
            response = HttpResponse(
                "408 Request Timeout (upload too slow)",
                status=408
            )
        except RequestAborted:
            return
        except RequestDataTooBig:
            response = HttpResponse("413 Payload too large", status=413)
        else:
            response = self.get_response(request)
            if isinstance(response, FileResponse):
                response.block_size = 1024 * 512
        for response_message in self.encode_response(response):
            await self.send(response_message)
        response.close()
