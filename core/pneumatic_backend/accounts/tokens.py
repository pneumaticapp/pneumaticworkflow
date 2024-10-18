from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError
from pneumatic_backend.analytics.enums import MailoutType
from pneumatic_backend.accounts.enums import (
    UserStatus
)
from pneumatic_backend.accounts.services.exceptions import (
    InvalidOrExpiredToken,
    AlreadyAcceptedInviteException,
    AlreadyRegisteredException,
)
from pneumatic_backend.accounts.messages import (
    MSG_A_0008
)

UserModel = get_user_model()


class BaseToken(Token):

    @classmethod
    def for_user_id(cls, user_id: int):
        token = cls()
        token[api_settings.USER_ID_CLAIM] = user_id
        return token


class InviteToken(BaseToken):

    token_type = 'invite'
    lifetime = timedelta(days=7)

    def __init__(self, token=None, verify=True):
        self.user = None
        self.invite = None
        try:
            super().__init__(token, verify)
        except TokenError:
            raise InvalidOrExpiredToken()

    def verify(self):
        try:
            super().verify()
        except TokenError:
            raise InvalidOrExpiredToken()

        try:
            self.user = UserModel.objects.get(
                id=self.payload[api_settings.USER_ID_CLAIM]
            )
        except ObjectDoesNotExist:
            raise InvalidOrExpiredToken()

        if self.user.status == UserStatus.ACTIVE:
            raise AlreadyAcceptedInviteException()
        if UserModel.objects.filter(email=self.user.email).active().exists():
            raise AlreadyRegisteredException()
        self.invite = self.user.invite
        if not self.invite:
            raise InvalidOrExpiredToken()


class ResetPasswordToken(BaseToken):
    token_type = 'password'
    lifetime = timedelta(minutes=30)

    def verify(self):
        super().verify()
        user_id = self.payload[api_settings.USER_ID_CLAIM]
        try:
            UserModel.objects.active().get(id=user_id)
        except ObjectDoesNotExist:
            raise TokenError(MSG_A_0008)


class AuthToken(BaseToken):
    token_type = 'auth_info'
    lifetime = timedelta(minutes=10)

    @classmethod
    def for_auth_data(cls, **kwargs):
        token = cls()
        token.payload.update(kwargs)
        return token


class TransferToken(BaseToken):
    token_type = 'user_transfer'
    lifetime = timedelta(days=settings.USER_TRANSFER_TOKEN_LIFETIME_IN_DAYS)


class VerificationToken(BaseToken):
    token_type = 'account_verification'
    lifetime = timedelta(days=settings.VERIFICATION_DEADLINE_IN_DAYS)


class DigestUnsubscribeToken(BaseToken):
    token_type = 'digest_unsub'
    lifetime = timedelta(days=settings.DIGEST_UNSUB_TOKEN_IN_DAYS)


class UnsubscribeEmailToken(BaseToken):

    token_type = 'unsubscribe'
    lifetime = timedelta(days=settings.UNSUBSCRIBE_TOKEN_IN_DAYS)

    @classmethod
    def create_token(cls, user_id: int, email_type: MailoutType):
        token = cls.for_user_id(user_id)
        token.payload.update({'email_type': MailoutType.MAP[email_type]})
        return token
