from rest_framework.permissions import BasePermission
from pneumatic_backend.analytics.customerio.utils import check_webhook_hash
from pneumatic_backend.utils import logging


class WebhookAPIPermission(BasePermission):

    def has_permission(self, request, view) -> bool:
        result = check_webhook_hash(request)
        if result is False:
            logging.capture_sentry_message(
                message='customer.io webhook permission error',
                data={
                    'request_data': request.data,
                    'request_headers': request.headers,
                },
                level=logging.SentryLogLevel.ERROR
            )
        return result
