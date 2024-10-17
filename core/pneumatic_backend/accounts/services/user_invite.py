from typing import Optional, List
from django.db import transaction, IntegrityError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.authentication.tokens import PneumaticToken
from pneumatic_backend.accounts.enums import (
    UserStatus,
    BillingPlanType,
    SourceType,
    UserInviteStatus,
    Timezone,
    Language,
)
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.analytics.mixins import (
    BaseIdentifyMixin,
)
from pneumatic_backend.accounts.services.exceptions import (
    UsersLimitInvitesException,
    AlreadyAcceptedInviteException,
    AlreadyRegisteredException,
    UserNotFoundException,
)
from pneumatic_backend.accounts.entities import InviteData
from pneumatic_backend.accounts.tokens import (
    InviteToken,
)
from pneumatic_backend.accounts.models import (
    APIKey,
    Contact,
    UserInvite,
)
from pneumatic_backend.services.email import EmailService
from pneumatic_backend.accounts.tokens import TransferToken
from pneumatic_backend.processes.api_v2.services.system_workflows import (
    SystemWorkflowService
)
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.payment.tasks import increase_plan_users


UserModel = get_user_model()


class UserInviteService(
    BaseIdentifyMixin
):

    def __init__(
        self,
        current_url: str,
        is_superuser: bool = False,
        request_user: Optional[UserModel] = None,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER,
        send_email: bool = True
    ):
        if request_user:
            self.account = request_user.account
            self.request_user = request_user
        else:
            self.account = None
            self.request_user = None
        self.current_url = current_url
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        # TODO Replace send_email to is_superuser in
        #   https://my.pneumatic.app/workflows/33941/
        self.send_email = send_email

    def _get_invite_token(self, user: UserModel) -> str:
        return str(InviteToken.for_user(user))

    def _get_transfer_token(
        self,
        current_account_user: UserModel,
        another_account_user: UserModel
    ) -> str:

        token = TransferToken()
        token['new_user_id'] = current_account_user.id
        token['prev_user_id'] = another_account_user.id
        return str(token)

    def _create_invited_user(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo: Optional[str] = None,
        password: Optional[str] = None,
    ) -> UserModel:

        owner = self.account.get_owner()
        user = UserModel(
            email=email,
            account_id=self.account.id,
            status=UserStatus.INVITED,
            is_active=False,
            is_admin=True,
            photo=photo,
            first_name=(first_name or '').title(),
            last_name=(last_name or '').title(),
            timezone=owner.timezone,
            language=owner.language,
            date_fmt=owner.date_fmt,
            date_fdw=owner.date_fdw,
        )
        if password:
            user.password = password
        user.save()
        return user

    def _get_another_account_user(self, email: str) -> Optional[UserModel]:

        return UserModel.objects.filter(
            status=UserStatus.ACTIVE,
            email=email
        ).exclude(
            account_id=self.account.id
        ).first()

    def _get_account_user(self, email) -> Optional[UserModel]:
        return self.account.users.filter(email=email).first()

    def _create_user_invite(
        self,
        user: UserModel,
        invited_from: SourceType.LITERALS
    ):

        UserInvite.objects.create(
            invited_user=user,
            account_id=self.account.id,  # TODO or another user acc ?
            email=user.email,
            invited_by=self.request_user,
            invited_from=invited_from,
        )

    def _user_create_actions(self, user: UserModel):

        APIKey.objects.get_or_create(
            user=user,
            name=user.get_full_name(),
            account_id=user.account_id,
            key=PneumaticToken.create(user, for_api_key=True)
        )

        if self.account.billing_plan == BillingPlanType.FREEMIUM:
            # TODO Need use two efficient SQL-queries
            #  https://my.pneumatic.app/workflows/16723
            for template in self.account.template_set.on_account(
                self.account.id
            ):
                template.template_owners.add(user)
                for workflow in template.workflows.all():
                    workflow.members.add(user)

    def _user_invite_actions(self, user: UserModel):

        self.identify(user)
        AnalyticService.users_invited(
            invite_to=user,
            is_superuser=self.is_superuser,
            invite_token=self._get_invite_token(user)
        )
        AnalyticService.users_invite_sent(
            invite_from=self.request_user,
            invite_to=user,
            current_url=self.current_url,
            is_superuser=self.is_superuser
        )

    def _send_transfer_email(
        self,
        current_account_user: UserModel,
        another_account_user: UserModel
    ):

        transfer_token_str = self._get_transfer_token(
            current_account_user=current_account_user,
            another_account_user=another_account_user
        )
        EmailService.send_user_transfer_email(
            email=another_account_user.email,
            invited_by=self.request_user,
            token=transfer_token_str,
            user_id=current_account_user.id,
            logo_lg=current_account_user.account.logo_lg
        )

    def _validate_already_accepted(self, user: UserModel):
        if user.status == UserStatus.ACTIVE:
            raise AlreadyAcceptedInviteException(
                invites_data=[{'email': user.email}]
            )

    def _validate_limit_invites(self):

        """ Account active users should be less than limit """

        account_invites_limit = (
            self.account.max_invites
            if self.account.max_invites > self.account.max_users else
            self.account.max_users
        )
        if self.account.active_users >= account_invites_limit:
            raise UsersLimitInvitesException()

    def _user_transfer_actions(
        self,
        current_account_user: UserModel,
        another_account_user: UserModel
    ):
        self.identify(current_account_user)
        # TODO Do not send invite_token.
        #   Fix in https://my.pneumatic.app/workflows/15691
        AnalyticService.users_invited(
            invite_to=another_account_user,
            is_superuser=self.is_superuser,
            invite_token=self._get_invite_token(another_account_user)
        )
        AnalyticService.users_invite_sent(
            invite_from=self.request_user,
            invite_to=another_account_user,
            current_url=self.current_url,
            is_superuser=self.is_superuser
        )

    def _transfer_existent_user(
        self,
        another_account_user: UserModel,
        invited_from: SourceType,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo: Optional[str] = None,
        groups: Optional[List[int]] = None
    ):

        """ Creates in current account user
            with same email and status 'invited'
            Creates invite for another account user """

        current_account_user = self._get_account_user(email)
        if current_account_user:
            self._validate_already_accepted(current_account_user)
        else:
            self._validate_limit_invites()
            current_account_user = self._create_invited_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                photo=photo,
                password=another_account_user.password
            )
            self._create_user_invite(
                user=current_account_user,
                invited_from=invited_from
            )
            if groups:
                current_account_user.user_groups.set(groups)
            self._user_create_actions(current_account_user)
            self._user_transfer_actions(
                current_account_user=current_account_user,
                another_account_user=another_account_user
            )
            if self.send_email:
                self._send_transfer_email(
                    current_account_user=current_account_user,
                    another_account_user=another_account_user
                )

    def _invite_new_user(
        self,
        invited_from: SourceType,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo: Optional[str] = None,
        groups: Optional[List[int]] = None
    ):

        """ if user with email already invited just skip and return ok """

        user = self._get_account_user(email)
        if user:
            self._validate_already_accepted(user)
        else:
            self._validate_limit_invites()
            user = self._create_invited_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                photo=photo,
            )
            self._create_user_invite(
                user=user,
                invited_from=invited_from
            )
            if groups:
                user.user_groups.set(groups)
            self._user_create_actions(user)
            if self.send_email:
                self._user_invite_actions(user)

    def invite_user(
        self,
        invited_from: SourceType,
        email: str,
        groups: Optional[List[int]] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo: Optional[str] = None,
    ):

        with transaction.atomic():
            another_account_user = self._get_another_account_user(email)
            if another_account_user:
                self._transfer_existent_user(
                    invited_from=invited_from,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    photo=photo,
                    another_account_user=another_account_user,
                    groups=groups,
                )
            else:
                self._invite_new_user(
                    invited_from=invited_from,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    photo=photo,
                    groups=groups,
                )
            Contact.objects.filter(
                account=self.account,
                email=email,
                status=UserStatus.ACTIVE
            ).update(
                status=UserStatus.INVITED
            )

    def invite_users(self, data: List[InviteData]):

        with transaction.atomic():
            for invite_data in data:
                self.invite_user(**invite_data)

    def resend_invite(self, user_id: str):

        """ Perform resending invite email for account user """

        user = self.account.users.filter(id=user_id).first()
        if not user:
            raise UserNotFoundException()
        elif user.status == UserStatus.ACTIVE:
            raise AlreadyAcceptedInviteException(
                invites_data=[{'email': user.email}]
            )
        elif user.status == UserStatus.INVITED:
            another_account_user = self._get_another_account_user(user.email)
            if another_account_user:
                self._send_transfer_email(
                    current_account_user=user,
                    another_account_user=another_account_user,
                )
                self._user_transfer_actions(
                    current_account_user=user,
                    another_account_user=another_account_user
                )
            else:
                self._user_invite_actions(user)

    def accept(
        self,
        invite: UserInvite,
        first_name: str,
        last_name: str,
        language: Optional[Language] = None,
        timezone: Optional[Timezone] = None,
        password: Optional[str] = None
    ) -> UserModel:

        with transaction.atomic():
            user = invite.invited_user
            if password:
                user.password = make_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True  # need for django admin
            user.status = UserStatus.ACTIVE
            if timezone:
                user.timezone = timezone
            if language:
                user.language = language
            try:
                user.save()
            except IntegrityError:
                raise AlreadyRegisteredException()

            invite.status = UserInviteStatus.ACCEPTED
            invite.save(update_fields=['status', 'date_updated'])
            service = SystemWorkflowService(user=invite.invited_user)
            service.create_onboarding_workflows()
            service.create_activated_workflows()
            account_service = AccountService(
                instance=user.account,
                user=user
            )
            account_service.update_users_counts()
        if (
            settings.PROJECT_CONF['BILLING']
            and user.account.billing_sync
            and user.account.billing_plan == BillingPlanType.PREMIUM
        ):
            increase_plan_users.delay(
                account_id=user.account_id,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type
            )

        AnalyticService.users_joined(user)
        self.identify(user)
        self.group(user)
        return user
