from celery import shared_task
from django.contrib.auth import get_user_model
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.models import Account
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)
from pneumatic_backend.payment.messages import (
    MSG_BL_0023,
    MSG_BL_0024,
)
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.payment.stripe.webhooks import WebhookService
from pneumatic_backend.payment.stripe.exceptions import StripeServiceException


UserModel = get_user_model()


def _increase_plan_users(
    account_id: int,
    is_superuser: bool,
    auth_type: AuthTokenType.LITERALS,
    increment=True,
):

    """ Increases the Premium plan quantity
        If increment=True then increase by one
        Otherwise, increase to paid users count """

    account = Account.objects.by_id(account_id).first()
    if account is None:
        raise Exception(MSG_BL_0023)
    if account.billing_plan != BillingPlanType.PREMIUM:
        return
    if account.is_tenant:
        account = account.master_account
        if account is None:
            raise Exception(MSG_BL_0024)
    if not account.is_paid:
        return
    paid_users_count = account.get_paid_users_count()
    if paid_users_count > account.max_users:
        if increment:
            quantity = account.max_users + 1
        else:
            quantity = paid_users_count
        if quantity > 0:
            user = account.get_owner()
            try:
                service = StripeService(
                    user=user,
                    is_superuser=is_superuser,
                    auth_type=auth_type
                )
                service.increase_subscription(quantity=quantity)
            except StripeServiceException as ex:
                capture_sentry_message(
                    message=(
                        f'Premium plan incrementing failed ({account.id})'
                    ),
                    data={
                        'account_id': account.id,
                        'ex': str(ex)
                    },
                    level=SentryLogLevel.ERROR,
                )


@shared_task
def increase_plan_users(
    account_id: int,
    is_superuser: bool,
    auth_type: AuthTokenType.LITERALS,
    increment=True
):
    _increase_plan_users(
        account_id=account_id,
        increment=increment,
        is_superuser=is_superuser,
        auth_type=auth_type,
    )


@shared_task
def handle_webhook(data: dict):
    service = WebhookService()
    service.handle(data)
