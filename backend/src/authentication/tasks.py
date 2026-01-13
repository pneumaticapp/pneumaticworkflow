import contextlib

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from slack import WebClient

from src.accounts.models import Account, User
from src.authentication.services.exceptions import (
    AuthException,
)
from src.authentication.services.google import (
    GoogleAuthService,
)
from src.authentication.services.microsoft import (
    MicrosoftAuthService,
)
from src.authentication.services.okta_logout import (
    OktaLogoutService,
)
from src.utils.logging import log_okta_message, SentryLogLevel

UserModel = get_user_model()


@shared_task(ignore_result=True)
def send_new_signup_notification(account_id: int):

    channel = settings.SLACK_CONFIG['SIGNUP_CHANNEL']
    token = settings.SLACK_CONFIG['MARVIN_TOKEN']
    account = Account.objects.by_id(account_id).first()
    if not account:
        return

    user = User.objects.on_account(account_id).account_owner().first()
    if not user:
        return

    name, email = f'{user.first_name} {user.last_name}', user.email

    if account.name:
        text = f'*{account.name}* just signed up by *{name}* / {email}'
    else:
        text = f'A new account just signed up by *{name}* / {email}'

    client = WebClient(token=token)
    client.chat_postMessage(
        channel=channel,
        blocks=[
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': text,
                },
            },
        ],
        text='A new account just signed up',
    )


@shared_task(
    autoretry_for=(User.DoesNotExist,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
)
def update_microsoft_contacts(user_id: int):
    user = User.objects.get(id=user_id)
    service = MicrosoftAuthService()
    with contextlib.suppress(AuthException):
        service.update_user_contacts(user)


@shared_task(
    autoretry_for=(User.DoesNotExist,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
)
def update_google_contacts(user_id: int):
    user = User.objects.get(id=user_id)
    service = GoogleAuthService()
    with contextlib.suppress(AuthException):
        service.update_user_contacts(user)


@shared_task(ignore_result=True)
def process_okta_logout(logout_token: str, request_data: dict):
    """
    Process Okta Back-Channel Logout request.

    This task:
    1. Validates the logout_token (bearer token)
    2. Processes logout based on token type (iss_sub or email)
    """

    log_okta_message(
        message="Okta logout task started",
        data={
            'task_name': 'process_okta_logout',
            'request_data': request_data,
            'token_present': bool(logout_token),
        },
        level=SentryLogLevel.INFO,
    )

    service = OktaLogoutService(logout_token=logout_token)
    service.process_logout(**request_data)
