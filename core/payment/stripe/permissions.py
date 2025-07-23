from django.conf import settings
from rest_framework.permissions import BasePermission


class StripeWebhookPermission(BasePermission):

    stripe_secret_key = settings.STRIPE_SECRET_KEY
    stripe_webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    configuration = settings.CONFIGURATION_CURRENT
    whitelist = settings.STRIPE_WEBHOOK_IP_WHITELIST
    message = None

    def has_permission(self, request, view):
        if self.configuration not in (
            settings.CONFIGURATION_STAGING,
            settings.CONFIGURATION_PROD
        ):
            return True

        if not (
            request.META.get('HTTP_REMOTE_ADDR') in self.whitelist
            or request.META.get('HTTP_X_REAL_IP') in self.whitelist
        ):
            return False
        # Debug code remove in https://my.pneumatic.app/workflows/25757/
        # from pneumatic_backend.utils.logging import (
        #     capture_sentry_message,
        #     SentryLogLevel
        # )
        # capture_sentry_message(
        #     level=SentryLogLevel.INFO,
        #     message='Stripe webhook received',
        #     data={
        #         'sig_header': request.headers.get(
        #             'Stripe-Signature',
        #             request.META.get('HTTP_STRIPE_SIGNATURE')
        #         ),
        #         'body': request.body,
        #     }
        # )
        #
        # sig_header = request.headers.get(
        #     'Stripe-Signature',
        #     request.META.get('HTTP_STRIPE_SIGNATURE')
        # )
        # stripe.api_key = self.stripe_secret_key
        # try:
        #     event_ex = None
        #     event = stripe.Webhook.construct_event(
        #         request.body,
        #         sig_header,
        #         self.stripe_webhook_secret
        #     )
        # except stripe.error.StripeError as ex:
        #     event_ex = ex
        #     event = False
        # try:
        #     verify_ex = None
        #     verify = stripe.WebhookSignature.verify_header(
        #         payload=request.body,
        #         header=sig_header,
        #         secret=self.stripe_webhook_secret,
        #         tolerance=None
        #     )
        # except stripe.error.StripeError as ex:
        #     verify_ex = ex
        #     verify = False
        # capture_sentry_message(
        #     message='Debug webhook',
        #     data={
        #         'event': event,
        #         'event_ex': event_ex,
        #         'verify': verify,
        #         'verify_ex': verify_ex
        #     }
        # )
        return True
