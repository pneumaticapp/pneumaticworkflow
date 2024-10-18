from datetime import timedelta
import pytest
from django.conf import settings
from django.utils import timezone
from pneumatic_backend.services.email import EmailService
from pneumatic_backend.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
)
from pneumatic_backend.notifications.enums import EmailTemplate

pytestmark = pytest.mark.django_db


class TestEmailService:

    def test_call_mailing_dev(self, mocker):

        settings_mock = mocker.patch(
            'pneumatic_backend.services.email.settings'
        )
        send_to_console_mock = mocker.patch(
            'pneumatic_backend.services.email.'
            'EmailService._send_email_to_console'
        )
        user_id = 1
        email = 'john@cena.com'
        settings_mock.CONFIGURATION_CURRENT = settings.CONFIGURATION_DEV
        settings_mock.CONFIGURATION_DEV = settings.CONFIGURATION_DEV
        EmailService._send_mail(
            user_id=user_id,
            recipient_email=email,
            template_code=EmailTemplate.RESET_PASSWORD,
        )

        send_to_console_mock.assert_called_with(
            recipient_email=email,
            template_code=EmailTemplate.RESET_PASSWORD,
            data=None,
        )

    def test_call_mailing_staging(self, mocker, customerio_client):

        settings_mock = mocker.patch(
            'pneumatic_backend.services.email.settings')
        send_via_customerio_mock = mocker.patch(
            'pneumatic_backend.services.tasks.send_email_via_customerio.delay'
        )
        user_id = 1
        email = 'john@cena.com'
        settings_mock.CONFIGURATION_CURRENT = settings.CONFIGURATION_STAGING
        settings_mock.CONFIGURATION_DEV = settings.CONFIGURATION_DEV
        EmailService._send_mail(
            user_id=user_id,
            recipient_email=email,
            template_code=EmailTemplate.RESET_PASSWORD,
        )

        send_via_customerio_mock.assert_called_with(
            user_id=user_id,
            email=email,
            template_code=EmailTemplate.RESET_PASSWORD,
            dynamic_data=None,
        )

    def test_user_deactivated_email(self, mocker):

        account = create_test_account(logo_lg='https://another/image.jpg')
        user = create_test_user(account=account)
        call_mailing_mock = mocker.patch(
            'pneumatic_backend.services.email.EmailService._send_mail'
        )

        EmailService.send_user_deactivated_email(user)

        call_mailing_mock.assert_called_with(
            user_id=user.id,
            recipient_email=user.email,
            template_code=EmailTemplate.USER_DEACTIVATED,
            data={
                'logo_lg': user.account.logo_lg,
            }
        )

    def test_send_verification_email(self, mocker):

        account = create_test_account(logo_lg='https://another/image.jpg')
        user = create_test_user(account=account)
        user.first_name = 'Shrek'
        user.save()
        call_mailing_mock = mocker.patch(
            'pneumatic_backend.services.email.EmailService._send_mail'
        )

        data = {
            'token': '123456',
            'first_name': user.first_name,
            'logo_lg': user.account.logo_lg
        }

        EmailService.send_verification_email(
            user=user,
            token='123456',
            logo_lg=account.logo_lg
        )

        call_mailing_mock.assert_called_with(
            user_id=user.id,
            recipient_email=user.email,
            template_code=EmailTemplate.ACCOUNT_VERIFICATION,
            data=data,
        )

    def test_send_digest_email(self, mocker):

        # arrange
        account = create_test_account(logo_lg='https://another/image.jpg')
        user = create_test_user(account=account)
        call_mailing_mock = mocker.patch(
            'pneumatic_backend.services.email.EmailService._send_mail'
        )
        create_token_mock = mocker.patch(
            'pneumatic_backend.accounts.tokens.UnsubscribeEmailToken.'
            'create_token',
            return_value='MdmslSLjg',
        )
        now = timezone.now()
        mailing_data = {
            'user': user,
            'templates': [
                {
                    'started': 5,
                    'in_progress': 5,
                    'overdue': 0,
                    'completed': 3,
                    'template_name': 'First template',
                    'template_id': 1,
                },
                {
                    'started': 2,
                    'in_progress': 2,
                    'overdue': 0,
                    'completed': 2,
                    'template_name': 'Second template',
                    'template_id': 2,
                },
            ],
            'started': 7,
            'in_progress': 7,
            'overdue': 5,
            'completed': 2,
            'token': 'MdmslSLjg',
        }
        date_from = (now - timedelta(days=7))
        date_to = now
        data = {
            'user': user,
            'date_from': date_from,
            'date_to': date_to,
            'digest': mailing_data,
            'logo_lg': account.logo_lg,
        }

        # act
        EmailService.send_workflows_digest_email(**data)

        # assert
        call_mailing_mock.assert_called_with(
            user_id=user.id,
            recipient_email=user.email,
            template_code=EmailTemplate.WORKFLOWS_DIGEST,
            data={
                'user': user,
                'date_from': date_from.strftime('%d %b'),
                'date_to': date_to.strftime('%d %b, %Y'),
                'unsubscribe_token': create_token_mock.return_value,
                'logo_lg': account.logo_lg,
                **mailing_data,
            }
        )
