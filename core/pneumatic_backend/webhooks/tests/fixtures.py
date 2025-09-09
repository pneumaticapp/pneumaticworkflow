from django.contrib.auth import get_user_model
from pneumatic_backend.webhooks.models import WebHook
from pneumatic_backend.webhooks.enums import HookEvent


UserModel = get_user_model()


def create_test_webhooks(
    user: UserModel,
    url: str = 'http://test.test'
):
    account = user.account
    WebHook.objects.bulk_create(
        WebHook(
            user_id=user.id,
            event=event,
            account_id=account.id,
            target=url
        ) for event in HookEvent.VALUES
    )


def create_test_webhook(
    user: UserModel,
    event: str,
    url: str = 'http://test.test'
):
    return WebHook.objects.create(
        user_id=user.id,
        event=event,
        account_id=user.account.id,
        target=url
    )
