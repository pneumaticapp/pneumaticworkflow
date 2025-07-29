import hashlib
import secrets
from datetime import timedelta
from typing import Any, Optional
from abc import abstractmethod
from django.utils.encoding import force_bytes
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.exceptions import TokenError
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.utils.salt import get_salt


UserModel = get_user_model()


class PneumaticToken:

    # TODO Need replace cls to self methods

    """ Not JWT. Store in cache 2 type of values:
        - user_id: List[encrypted tokens]
        - encrypted token: {
            'user_id': 3685,
            'account_id': 1688,
            'user_agent': 'PostmanRuntime/7.40.0',
            'user_ip': None,
            'for_api_key': False,
            'is_superuser': False
          }
        This values need for save cached user data and active tokens.
        If token inactive - it unavailable from cache
        (except for the api token, it is always available).
    """

    cache = caches['auth']

    def __init__(self, key: str, user: UserModel):
        self.key = key
        self.user = user

    @classmethod
    def _get_cached_data(cls, token) -> Optional[dict]:
        encrypted_token = cls.encrypt(token)
        return cls.cache.get(encrypted_token)

    @classmethod
    def data(cls, token):
        return cls._get_cached_data(token)

    @classmethod
    def encrypt(cls, token):
        encrypted_token = hashlib.pbkdf2_hmac(
            'sha256',
            token.encode(),
            force_bytes(settings.SECRET_KEY),
            settings.AUTH_TOKEN_ITERATIONS,
        )
        return encrypted_token.hex()

    @classmethod
    def create(
        cls,
        user: UserModel,
        token: Optional[str] = None,
        user_agent: str = None,
        user_ip: str = None,
        for_api_key: bool = False,
        for_superuser: bool = False,
    ) -> str:

        # In token_urlsafe param is 24 because of 24 is length of bytes token,
        # and after decoding its length grows up. And with param of
        # 24 it returns token of length 32. This may be resolved with some
        # function, but token length has exponential grow, and didn't worth it
        if not token:
            token = secrets.token_urlsafe(24)
        encrypted_token = cls.encrypt(token)

        tokens = cls._get_tokens(encrypted_token, user)

        cache_values = {
            'user_id': user.pk,
            'account_id': user.account_id,
            'user_agent': user_agent,
            'user_ip': user_ip,
            'for_api_key': for_api_key,
            'is_superuser': for_superuser,
        }

        cls.set_key_value(encrypted_token, cache_values)
        cls.set_key_value(user.pk, tokens)
        return token

    @classmethod
    def set_user_token(cls, token: str, user: UserModel):
        encrypted_token = cls.encrypt(token)
        cls.set_key_value(user.pk, cls._get_tokens(encrypted_token, user))

    @classmethod
    def _get_tokens(cls, encrypted_token: str, user: UserModel):
        tokens = cls.cache.get(user.pk)
        if not tokens:
            tokens = [encrypted_token]
        elif encrypted_token not in tokens:
            tokens.append(encrypted_token)
        return tokens

    @classmethod
    def get_user_tokens(cls, user: UserModel):
        tokens = cls.cache.get(user.pk)
        return tokens

    @classmethod
    def get_user_from_token(
        cls,
        token: str,
    ) -> UserModel:
        cached_data = cls._get_cached_data(token)
        if cached_data:
            return UserModel.objects.get(pk=cached_data['user_id'])
        else:
            raise UserModel.DoesNotExist

    @classmethod
    def expire_token(cls, token: str):
        encrypted_token = cls.encrypt(token)
        user_info = cls.cache.get(encrypted_token)
        if not user_info:
            return None

        user_pk = user_info.get('user_id')
        tokens = cls.cache.get(user_pk)

        if tokens and encrypted_token in tokens:
            tokens.remove(encrypted_token)
            cls.set_key_value(user_pk, tokens)

        cls.cache.delete(encrypted_token)

    @classmethod
    def expire_all_tokens(cls, user: UserModel):
        tokens = cls.cache.get(user.pk) or []
        for token in tokens:
            cls.cache.delete(token)

        cls.cache.delete(user.pk)

    @classmethod
    def set_key_value(cls, key: str, value: Any):
        cls.cache.set(key, value, timeout=None)


class GuestToken(Token):
    token_type = AuthTokenType.GUEST
    lifetime = timedelta(days=365)


class PublicBaseToken:

    @property
    @abstractmethod
    def token_length(self) -> int:
        pass

    @property
    @abstractmethod
    def token_type(self) -> AuthTokenType:
        pass

    def __init__(self, token: Optional[str] = None):
        if token:
            self._validate_length(token)
            self.token = token
        else:
            self.token = get_salt(length=self.token_length)

    def __str__(self) -> str:
        return self.token

    def _validate_length(self, token: str):
        if len(token) != self.token_length:
            raise TokenError('Incorrect token length')

    @property
    def is_embedded(self):
        return self.token_type == AuthTokenType.EMBEDDED

    @property
    def is_public(self):
        return self.token_type == AuthTokenType.PUBLIC


class PublicToken(PublicBaseToken):

    token_type = AuthTokenType.PUBLIC
    token_length = 8


class EmbedToken(PublicBaseToken):

    token_type = AuthTokenType.EMBEDDED
    token_length = 32
