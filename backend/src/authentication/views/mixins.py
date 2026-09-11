from django.db.models import ObjectDoesNotExist
from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpRequest
from rest_framework.exceptions import (
    AuthenticationFailed,
    ValidationError,
)

from src.accounts.enums import Language
from src.accounts.models import Account
from src.accounts.services.account import (
    AccountService,
)
from src.accounts.services.exceptions import (
    AccountServiceException,
    UserServiceException,
)
from src.accounts.services.user import UserService
from src.authentication.entities import UserData
from src.authentication.enums import (
    AuthTokenType,
    LoginFailedReason,
)
from src.authentication.messages import (
    MSG_AU_0003,
    MSG_AU_0016,
)
from src.authentication.services.user_auth import AuthService
from src.authentication.tokens import PneumaticToken
from src.logs.events import AuditEventService
from src.logs.service import AccountLogService
from src.payment.stripe.exceptions import StripeServiceException
from src.payment.stripe.service import StripeService
from src.processes.services.system_workflows import (
    SystemWorkflowService,
)
from src.utils.http import (
    get_client_ip,
    get_user_agent_header,
)
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class SignUpMixin:

    # Which provider signed the person up; every subclass names
    # its own. LoginEventMixin reads an attribute of the same name.
    source = None

    def _get_request(self) -> Optional[HttpRequest]:

        """ The request being handled, when there is one.

            A view has it as an attribute; a service that mixes this
            in has none, and then the events fall back to the context
            the middleware published. """

        return getattr(self, 'request', None)

    def after_signup(self, user: UserModel):

        """ Create signup log and send notification if enabled, and
            journal the sign up. SignUpView overrides this without
            the log and the notification: an e-mail sign up never
            had them, and the journal must not bring them along. """

        if user.account.log_api_requests and self.source:
            service = AccountLogService(user)
            service.signup(user=user, source=self.source)
        if settings.SLACK and settings.SLACK_CONFIG['NOTIFY_ON_SIGNUP']:
            from src.authentication.tasks import (  # noqa: PLC0415
                send_new_signup_notification,
            )
            send_new_signup_notification.delay(user.account_id)
        self.emit_signup(user)

    def emit_signup(self, user: UserModel) -> None:

        """ The one place every sign up source goes through, so the
            user.signup event is published here and nowhere else.
            A service has no request: the address and the browser
            then come from the context of the middleware. """

        AuditEventService.user_signed_up(
            user=user,
            source=self.source,
            request=self._get_request(),
        )

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
        timezone: Optional[str] = None,
        password: Optional[str] = None,
    ) -> UserModel:

        request = self._get_request()
        is_superuser = getattr(request, 'is_superuser', False)
        user_service = UserService(
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
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
                self.after_signup(user)
                return user

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
        timezone: Optional[str] = None,
        password: Optional[str] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_term: Optional[str] = None,
        utm_content: Optional[str] = None,
        gclid: Optional[str] = None,
        billing_sync: bool = settings.PROJECT_CONF['BILLING'],
        request: Optional[HttpRequest] = None,
        ms_graph_user_id: Optional[str] = None,
    ) -> Tuple[UserModel, PneumaticToken]:

        request = request or self._get_request()
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
                if billing_sync:
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
                self.after_signup(account_owner)
                token = AuthService.get_auth_token(
                    user=account_owner,
                    user_agent=get_user_agent_header(request),
                    user_ip=get_client_ip(request),
                )
        return account_owner, token


class LoginEventMixin:

    """ The sign in events of a login view: which provider signed
        somebody in, and which refusal to journal when it did not.

        Every view that mixes this in declares its own source
        (SignUpMixin defaults it to None for the views that also
        sign people up).

        The SSO providers built on BaseSSOService journal the login in
        the service instead, where the new and the returning person
        are told apart without the view having to ask. """

    def _login_or_signup(
        self,
        request,
        user_data: UserData,
        validated_data: dict,
        signup_enabled: bool,
    ) -> Tuple[UserModel, PneumaticToken]:

        """ The token of a Google or Microsoft callback.

            An active user signs in; an address nobody knows signs up
            when the deployment takes sign ups and is refused as
            SIGNUP_DISABLED otherwise. signup_enabled comes from the
            view: the flag belongs to the deployment the view serves.
            A user the SSO policy keeps out is refused as SSO_REQUIRED,
            the same reason the password sign in journals. """

        try:
            user = UserModel.objects.active().get(email=user_data['email'])
        except ObjectDoesNotExist as ex:
            if not signup_enabled:
                self.emit_login_failed(
                    request=request,
                    reason=LoginFailedReason.SIGNUP_DISABLED,
                    email=user_data['email'],
                )
                raise AuthenticationFailed(MSG_AU_0003) from ex
            return self.signup(
                **user_data,
                utm_source=validated_data.get('utm_source'),
                utm_medium=validated_data.get('utm_medium'),
                utm_campaign=validated_data.get('utm_campaign'),
                utm_term=validated_data.get('utm_term'),
                utm_content=validated_data.get('utm_content'),
                gclid=validated_data.get('gclid'),
            )
        try:
            self.check_sso_restrictions(user)
        except ValidationError:
            self.emit_login_failed(
                request=request,
                reason=LoginFailedReason.SSO_REQUIRED,
                email=user.email,
            )
            raise
        token = AuthService.get_auth_token(
            user=user,
            user_agent=get_user_agent_header(request),
            user_ip=get_client_ip(request),
        )
        self.emit_login(user=user, request=request)
        return user, token

    def emit_login(self, user: UserModel, request) -> None:
        AuditEventService.user_logged_in(
            user=user,
            source=self.source,
            request=request,
        )

    def emit_login_failed(
        self,
        request,
        reason: LoginFailedReason.LITERALS,
        email: Optional[str] = None,
    ):
        AuditEventService.login_failed(
            request=request,
            reason=reason,
            email=email,
        )


class SSORestrictionMixin:

    @staticmethod
    def check_sso_restrictions(user: UserModel):
        if settings.PROJECT_CONF['SSO_AUTH'] and not user.is_account_owner:
            raise ValidationError(MSG_AU_0016)
