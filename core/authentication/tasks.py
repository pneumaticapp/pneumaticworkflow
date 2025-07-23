from celery import shared_task
from django.conf import settings
from slack import WebClient
from pneumatic_backend.accounts.models import User, Account
from pneumatic_backend.authentication.services.exceptions import (
    AuthException
)
from pneumatic_backend.authentication.services.microsoft import (
    MicrosoftAuthService
)


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
                    'text': text
                }
            }
        ],
        text='A new account just signed up'
    )


@shared_task(ignore_result=True)
def update_microsoft_contacts(user_id: int):
    user = User.objects.get(id=user_id)
    service = MicrosoftAuthService()
    try:
        service.update_user_contacts(user)
    except AuthException:
        pass
