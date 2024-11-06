from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError

from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.models import UserInvite
from pneumatic_backend.accounts.tokens import TransferToken
from pneumatic_backend.accounts.services.exceptions import (
    InvalidTransferTokenException,
    AlreadyAcceptedInviteException,
    ExpiredTransferTokenException,
    ReassignUserDoesNotExist,
)
from pneumatic_backend.payment.stripe.service import StripeService
from pneumatic_backend.accounts.enums import (
    UserStatus,
    UserInviteStatus,
    BillingPlanType,
)
from pneumatic_backend.accounts.services.reassign import (
    ReassignService
)
from pneumatic_backend.processes.services.remove_user_from_draft import (
    remove_user_from_draft,
)
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.accounts.services.user import UserService
from pneumatic_backend.payment.tasks import increase_plan_users
from pneumatic_backend.accounts.services import AccountService


UserModel = get_user_model()


class UserTransferService(
    BaseIdentifyMixin
):

    def __init__(self):
        self.user = None
        self.token = None
        self.prev_user = None

    def _get_valid_user(self, user_id: int) -> UserModel:
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            raise InvalidTransferTokenException()
        else:
            if self.token['new_user_id'] != user.id:
                raise InvalidTransferTokenException()
            if user.status == UserStatus.ACTIVE:
                raise AlreadyAcceptedInviteException()
            return user

    def _get_valid_prev_user(self) -> UserModel:
        try:
            return UserModel.objects.exclude(
                id=self.user.id
            ).get(
                email=self.user.email,
                id=self.token['prev_user_id'],
                status=UserStatus.ACTIVE
            )
        except UserModel.DoesNotExist:
            raise ExpiredTransferTokenException()

    def _get_valid_token(self, token_str: str) -> TransferToken:
        try:
            token = TransferToken(token=token_str)
        except TokenError:
            raise InvalidTransferTokenException()
        else:
            if not token.get('new_user_id') or not token.get('prev_user_id'):
                raise InvalidTransferTokenException()
            return token

    def _after_transfer_actions(self):

        if (
            settings.PROJECT_CONF['BILLING']
            and self.user.account.billing_sync
            and self.user.account.billing_plan == BillingPlanType.PREMIUM
        ):
            increase_plan_users.delay(
                account_id=self.user.account_id,
                is_superuser=False,
                auth_type=AuthTokenType.USER
            )
        self.identify(self.user)
        self.group(self.prev_user)
        self.group(self.user)
        AnalyticService.users_transferred(user=self.prev_user)

    def _delete_prev_user_pending_invites(self):
        UserInvite.objects.on_account(
            self.prev_user.account.id
        ).filter(
            status=UserInviteStatus.PENDING,
            invited_user=self.prev_user
        ).delete()

    def _accept_user_pending_invite(self):
        UserInvite.objects.on_account(
            self.user.account.id
        ).filter(
            status=UserInviteStatus.PENDING,
            invited_user=self.prev_user
        ).delete()

    def _deactivate_prev_user(self):

        try:
            service = ReassignService(old_user=self.prev_user)
        except ReassignUserDoesNotExist:
            pass
        else:
            service.reassign_everywhere()
        remove_user_from_draft(
            account_id=self.prev_user.account.id,
            user_id=self.prev_user.id
        )
        self._delete_prev_user_pending_invites()
        if (
            settings.PROJECT_CONF['BILLING']
            and self.prev_user.account.billing_sync
            and self.prev_user.is_account_owner
            and self.prev_user.account.billing_plan in
                BillingPlanType.PAYMENT_PLANS
        ):
            service = StripeService(
                user=self.prev_user,
                is_superuser=False,
                auth_type=AuthTokenType.USER
            )
            service.cancel_subscription()

        UserService.deactivate(self.prev_user, skip_validation=True)

    def _activate_user(self):

        self.user.is_active = True  # need for django admin
        self.user.first_name = self.prev_user.first_name
        self.user.last_name = self.prev_user.last_name
        self.user.status = UserStatus.ACTIVE
        self.user.save(update_fields=[
            'status', 'is_active', 'first_name', 'last_name'
        ])
        service = AccountService(
            instance=self.user.account,
            user=self.user
        )
        service.update_users_counts()

    def accept_transfer(
        self,
        user_id: int,
        token_str: str,
    ):
        """ Accept transferring user from prev to new account

            user_id - new account user id
            token['new_user_id'] - new account user id
            token['prev_user_id'] - prev account user id
        """

        self.token = self._get_valid_token(token_str)
        self.user = self._get_valid_user(user_id)
        self.prev_user = self._get_valid_prev_user()
        with transaction.atomic():
            self._deactivate_prev_user()
            self._activate_user()
            self._after_transfer_actions()

    def get_account(self):
        return self.user.account

    def get_user(self):
        return self.user
