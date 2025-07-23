from pneumatic_backend.payment.stripe.permissions import (
    StripeWebhookPermission
)
from django.conf import settings


def test_stripe_permission__signature__ok(mocker):

    # arrange

    permission = StripeWebhookPermission()
    mocker.patch(
        'pneumatic_backend.payment.stripe.permissions.StripeWebhookPermission.'
        'configuration',
        settings.CONFIGURATION_PROD
    )
    ip = '127.0.0.1'
    mocker.patch(
        'pneumatic_backend.payment.stripe.permissions.StripeWebhookPermission.'
        'whitelist',
        [ip]
    )
    stripe_secret_key = (
        'sk_test_51N6TJkBM2UVM1VfGfeB4YtiqwRHTI55Y4VquoUQtiloS2iqn7aNE6ZNmF4'
        'DWco1Kr2OWcd0dCbF0rV2TWG7qKDnt004p84Jyax'
    )
    mocker.patch(
        'pneumatic_backend.payment.stripe.permissions.StripeWebhookPermission.'
        'stripe_secret_key',
        stripe_secret_key
    )
    stripe_webhook_secret = 'we_1N6XhwBM2UVM1VfGdCsiGf83'
    mocker.patch(
        'pneumatic_backend.payment.stripe.permissions.StripeWebhookPermission.'
        'stripe_webhook_secret',
        stripe_webhook_secret
    )
    sig_header = (
        't=1685096681,'
        'v1=e7af09bdf8ed7ad1e8f9df93e9d0b6070cc690c4432a8392f2e36769f1d64395,'
        'v0=96c2c5d050f5b8bb0031386e70960ad5ca7f30f17aacb1cc101631fbb70e6aa8'
    )
    body = b'some body'
    request_mock = mocker.Mock(
        META={'HTTP_REMOTE_ADDR': ip},
        headers={'Stripe-Signature': sig_header},
        body=body
    )

    view_mock = mocker.Mock()
    # verify_header_mock = mocker.patch(
    #     'pneumatic_backend.payment.stripe.permissions.stripe.'
    #     'WebhookSignature.verify_header',
    #     return_value=True
    # )

    # act & assert
    assert permission.has_permission(request_mock, view_mock) is True
    # verify_header_mock.assert_called_once_with(
    #     payload=body,
    #     header=sig_header,
    #     secret=stripe_webhook_secret,
    #     tolerance=None
    # )
