from typing import Optional, Tuple
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from pneumatic_backend.authentication.tokens import (
    PublicBaseToken,
    PublicToken,
    EmbedToken,
)
from pneumatic_backend.processes.models import Template


class PublicAuthService(BaseAuthentication):

    """ Request user is anonymous and not authenticated.
        The service is Used to get a template from JWT.
        Use with the PublicTemplatePermission """

    header_prefix = 'Token'

    @classmethod
    def _get_header(cls, request) -> Optional[str]:
        """
        Extracts the header containing template public_id from the given
        request.
        """
        return request.headers.get(
            'X-Public-Authorization',
            request.META.get('X-Public-Authorization')
        )

    @classmethod
    def get_token(cls, request) -> Optional[PublicToken]:

        """ Extracts token from header
            Return None if the header empty or has incorrect format """

        header = cls._get_header(request)
        token = None
        if header and isinstance(header, str):
            parts = header.split()
            if len(parts) == 2 and parts[0] == cls.header_prefix:
                raw_token = parts[1]
                if len(raw_token) == PublicToken.token_length:
                    token = PublicToken(raw_token)
                elif len(raw_token) == EmbedToken.token_length:
                    token = EmbedToken(raw_token)
        return token

    @classmethod
    def get_template(cls, token: PublicBaseToken) -> Optional[Template]:

        # TODO add caching in https://my.pneumatic.app/workflows/16934

        filter_kwargs = {}
        if token.is_public:
            filter_kwargs['public_id'] = str(token)
            filter_kwargs['is_public'] = True
        elif token.is_embedded:
            filter_kwargs['embed_id'] = str(token)
            filter_kwargs['is_embedded'] = True
        template = (
            Template.objects.exclude_onboarding()
            .active()
            .filter(**filter_kwargs)
            .first()
        )
        return template

    def authenticate_header(self, request):
        return f'{self.header_prefix} realm="api"'

    def authenticate(self, request) -> Tuple[AnonymousUser, PublicToken]:

        """ Modifies the request for calls with public or embedded token """

        token = PublicAuthService.get_token(request)
        if not token:
            return None
        template = PublicAuthService.get_template(token)
        if not template:
            return None
        request.token_type = token.token_type
        request.public_template = template
        request.is_superuser = False
        return AnonymousUser(), token
