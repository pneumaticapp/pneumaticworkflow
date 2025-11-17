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
    def check_sso_restrictions() -> None:
        if settings.PROJECT_CONF['SSO_AUTH']:
            raise ValidationError(MSG_AU_0016)
