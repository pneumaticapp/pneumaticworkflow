from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from src.authentication.messages import MSG_AU_0016

UserModel = get_user_model()


class SSORestrictionMixin:
    """
    Mixin for checking SSO authorization restrictions.

    Prohibits users from logging in using other methods,
    if their account has an active SSO configuration.
    """

    @staticmethod
    def check_sso_restrictions(user_email: str) -> None:
        if not settings.PROJECT_CONF.get('SSO_AUTH', False):
            return
        try:
            user = UserModel.objects.active().get(email=user_email)
            if not user.is_account_owner:
                raise ValidationError(MSG_AU_0016)
        except UserModel.DoesNotExist:
            pass
