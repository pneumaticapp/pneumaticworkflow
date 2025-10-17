from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import Token, TokenError

from src.accounts.models import Account
from src.payment.messages import MSG_BL_0001
from src.payment.stripe.entities import TokenSubscriptionData
from src.payment.stripe.enums import TokenType

UserModel = get_user_model()


class ConfirmToken(Token):

    """ Contains:
        account id
        request user id """

    token_type = TokenType.CONFIRM
    lifetime = timedelta(days=365)

    def __init__(
        self,
        token: Optional[str] = None,
        verify: bool = True,
    ):
        super().__init__(token, verify)
        if token:
            self.user = self._get_user()

    def _get_user(self):
        try:
            return UserModel.objects.get(
                account_id=self.payload['account_id'],
                id=self.payload['user_id'],
            )
        except ObjectDoesNotExist:
            try:
                return Account.objects.get(
                    id=self.payload['account_id'],
                ).get_owner()
            except ObjectDoesNotExist as ex:
                raise TokenError(MSG_BL_0001) from ex

    def get_subscription_data(self) -> Optional[TokenSubscriptionData]:
        data = self.payload.get('subscription')
        if data:
            return TokenSubscriptionData(**data)
        return None
