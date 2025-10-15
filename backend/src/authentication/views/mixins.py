from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpRequest

from src.accounts.enums import Language
from src.accounts.services.account import (
    AccountService,
    UserService,
)
from src.accounts.services.exceptions import (
    AccountServiceException,
    UserServiceException,
)
from src.accounts.services.user import UserService
from src.authentication.enums import AuthTokenType
from src.authentication.services.user_auth import AuthService
from src.authentication.tasks import (
    send_new_signup_notification,
)
from src.authentication.tokens import PneumaticToken
from src.payment.stripe.exceptions import StripeServiceException
from src.payment.stripe.service import StripeService
from src.processes.services.system_workflows import (
    SystemWorkflowService,
)
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class SignUpMixin:

    def after_signup(self, user: UserModel):
        pass

    def join_existing_account(
        self,
        account: Account,
        email: str,
        company_name: Optional[str] = None,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo: Optional[str] = None,
        job_title: Optional[str] = None,
        language: Language.LITERALS = None,
        timezone: str = None,
        password: Optional[str] = None,
    ) -> Tuple[UserModel, PneumaticToken]:

        request = getattr(self, 'request', None)
        is_superuser = getattr(request, 'is_superuser', False)
        user_service = UserService(
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER
        )
        with transaction.atomic():
            try:
                user = user_service.create(
                    account=account,
                    phone=phone,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    raw_password=password,
                    photo=photo,
                    is_account_owner=False,
                    timezone=timezone,
                    language=language,
                )
            except UserServiceException as ex:
                raise_validation_error(message=ex.message)
            else:
                token = AuthService.get_auth_token(
                    user=user,
                    user_agent=request.headers.get(
                        'User-Agent',
                        request.META.get('HTTP_USER_AGENT')
                    ),
                    user_ip=request.META.get('HTTP_X_REAL_IP'),
                )
                self.after_signup(user)
                return user, token

    def signup(
        self,
        email: str,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company_name: Optional[str] = None,
        photo: Optional[str] = None,
        job_title: Optional[str] = None,
        language: Language.LITERALS = None,
        timezone: str = None,
        password: Optional[str] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_term: Optional[str] = None,
        utm_content: Optional[str] = None,
        gclid: Optional[str] = None,
        billing_sync: bool = True,
        request: Optional[HttpRequest] = None,
    ) -> Tuple[UserModel, PneumaticToken]:

        request = request or self.request
        is_superuser = getattr(request, 'is_superuser', False)  # for Admin
        account_service = AccountService(
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
        )
        user_service = UserService(
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
        )
        with transaction.atomic():
            try:
                account = account_service.create(
                    name=company_name,
                    utm_source=utm_source,
                    utm_medium=utm_medium,
                    utm_campaign=utm_campaign,
                    utm_term=utm_term,
                    utm_content=utm_content,
                    gclid=gclid,
                    billing_sync=billing_sync,
                )
                account_owner = user_service.create(
                    account=account,
                    phone=phone,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    raw_password=password,
                    photo=photo,
                    is_account_owner=True,
                    timezone=timezone,
                    language=language,
                )
            except (AccountServiceException, UserServiceException) as ex:
                raise_validation_error(message=ex.message)
            else:
                if settings.PROJECT_CONF['BILLING'] and billing_sync:
                    try:
                        stripe_service = StripeService(user=account_owner)
                        stripe_service.update_customer()
                    except StripeServiceException as ex:
                        capture_sentry_message(
                            message=f'Stripe account sync failed {account.id}',
                            data={
                                'account_id': account.id,
                                'stripe_id': account.stripe_id,
                                'exception': str(ex),
                            },
                            level=SentryLogLevel.ERROR,
                        )
                service = SystemWorkflowService(user=account_owner)
                service.create_onboarding_templates()
                service.create_onboarding_workflows()
                service.create_activated_templates()
                service.create_activated_workflows()
                if (
                    settings.SLACK
                    and settings.SLACK_CONFIG['NOTIFY_ON_SIGNUP']
                ):
                    from src.authentication.tasks import (
                        send_new_signup_notification
                    )
                    send_new_signup_notification.delay(account.id)
                self.after_signup(account_owner)
                token = AuthService.get_auth_token(
                    user=account_owner,
                    user_agent=request.headers.get(
                        'User-Agent',
                        request.META.get('HTTP_USER_AGENT'),
                    ),
                    user_ip=request.META.get('HTTP_X_REAL_IP'),
                )
        return account_owner, token
