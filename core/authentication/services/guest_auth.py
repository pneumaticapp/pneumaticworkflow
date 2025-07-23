import json
from typing import Optional, Tuple
from django.core.cache import cache as default_cache
from django.contrib.auth import get_user_model
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework_simplejwt.authentication import (
    JWTAuthentication
)
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError
)
from pneumatic_backend.authentication.enums import (
    GuestCachedStatus,
    AuthTokenType,
)
from pneumatic_backend.authentication.tokens import GuestToken
from pneumatic_backend.authentication.queries import GetGuestQuery
from pneumatic_backend.authentication.messages import (
    MSG_AU_0007,
    MSG_AU_0009,
    MSG_AU_0010,
    MSG_AU_0011,
)


UserModel = get_user_model()


class GuestJWTAuthService(JWTAuthentication):

    CACHE_TIMEOUT = 86400  # day
    cache = default_cache

    @classmethod
    def get_token(
        cls,
        user_id: int,
        task_id: int,
        account_id: int,
    ) -> GuestToken:

        token = GuestToken()
        token['account_id'] = account_id
        token['user_id'] = user_id
        token['task_id'] = task_id
        return token

    @classmethod
    def get_str_token(
        cls,
        user_id: int,
        task_id: int,
        account_id: int,
    ) -> str:

        return str(
            cls.get_token(
                user_id=user_id,
                task_id=task_id,
                account_id=account_id
            )
        )

    def get_header(self, request):
        """
        Extracts the header containing the JSON web token from the given
        request.
        """
        header = request.headers.get(
            'X-Guest-Authorization',
            request.META.get('X-Guest-Authorization')
        )
        if isinstance(header, str):
            header = header.encode(HTTP_HEADER_ENCODING)
        return header

    def get_raw_token(self, header):
        """
        Extracts an unvalidated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if len(parts) > 1:
            raise AuthenticationFailed(MSG_AU_0007)
        return parts[0]

    def get_validated_token(self, raw_token) -> GuestToken:
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        try:
            return GuestToken(raw_token)
        except TokenError:
            raise InvalidToken(MSG_AU_0010)

    def get_user(self, validated_token: GuestToken) -> UserModel:
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token['user_id']
            account_id = validated_token['account_id']
            task_id = validated_token['task_id']
        except KeyError:
            raise InvalidToken(MSG_AU_0011)
        try:
            user = UserModel.objects.execute_raw(
                GetGuestQuery(
                    user_id=user_id,
                    account_id=account_id,
                    task_id=task_id
                )
            )[0]
        except IndexError:
            raise AuthenticationFailed(MSG_AU_0009)
        else:
            return user

    @classmethod
    def _get_cache_key(cls, task_id: int) -> str:
        return f'task-{task_id}-guests'

    @classmethod
    def _get_task_cached_value(cls, task_id: int) -> dict:

        """ Returns dict with task guests statues.
            If cache empty or invalid returns empty dict

            For example:
            task cache value = {
               user_id_1: GuestCachedStatus.ACTIVE
               user_id_N: GuestCachedStatus.INACTIVE
            }
        """

        key = cls._get_cache_key(task_id)
        json_value = cls.cache.get(key, {})
        if not isinstance(json_value, str):
            value = {}
        else:
            value = json.loads(json_value)
            if not isinstance(value, dict):
                value = {}
        return value

    @classmethod
    def _set_guest_cache(
        cls,
        task_id: int,
        status: GuestCachedStatus,
        user_id: Optional[int] = None
    ):

        """ Store in cache guests status for task.
            If 'user_id' not specified - sets status for all task guests.

            For example:
            task cache value = {
               user_id: GuestCachedStatus.ACTIVE
            }
        """

        key = cls._get_cache_key(task_id)
        value = cls._get_task_cached_value(task_id)
        if user_id:
            value[str(user_id)] = status
        else:
            for elem in value.keys():
                value[elem] = status
        cls.cache.set(key, json.dumps(value), cls.CACHE_TIMEOUT)

    @classmethod
    def deactivate_task_guest_cache(
        cls,
        task_id: int,
        user_id: Optional[int] = None
    ):
        """ Set the guest status active in cache
            It means that guest user will receive and permission denied error
            for next request """

        cls._set_guest_cache(
            task_id=task_id,
            user_id=user_id,
            status=GuestCachedStatus.INACTIVE
        )

    @classmethod
    def activate_task_guest_cache(
        cls,
        task_id: int,
        user_id: Optional[int] = None
    ):
        """ Set the guest status active in cache
            It means that the guest will be authenticated quickly
            (using cache value) during the day (CACHE_TIMEOUT) """

        cls._set_guest_cache(
            task_id=task_id,
            user_id=user_id,
            status=GuestCachedStatus.ACTIVE
        )

    @classmethod
    def delete_task_guest_cache(
        cls,
        task_id: int
    ):
        key = cls._get_cache_key(task_id)
        cls.cache.delete(key)

    def get_cached_user(self, validated_token: GuestToken) -> UserModel:

        """ Uses for quick access to the user instance.
            First gets user form db and then sets the value in the cache
            for quick access during the day (CACHE_TIMEOUT).

            The structure of the data in the cache for each task with guests:
            task_cache_key : {
               user_1_id: GuestCachedStatus.ACTIVE,
               user_2_id: GuestCachedStatus.INACTIVE,
               ...
            }
        """

        user_id = str(validated_token['user_id'])
        task_id = validated_token['task_id']
        key = self._get_cache_key(task_id)
        value = self._get_task_cached_value(task_id)
        guest_status = value.get(user_id)
        if guest_status == GuestCachedStatus.ACTIVE:
            try:
                user = UserModel.guests_objects.get(id=user_id)
            except UserModel.DoesNotExist:
                value[user_id] = GuestCachedStatus.INACTIVE
                self.cache.set(key, json.dumps(value), self.CACHE_TIMEOUT)
                raise AuthenticationFailed(MSG_AU_0009)
        elif guest_status == GuestCachedStatus.INACTIVE:
            raise AuthenticationFailed(MSG_AU_0009)
        else:
            try:
                user = self.get_user(validated_token)
            except AuthenticationFailed:
                value[user_id] = GuestCachedStatus.INACTIVE
                raise
            else:
                value[user_id] = GuestCachedStatus.ACTIVE
            finally:
                self.cache.set(key, json.dumps(value), self.CACHE_TIMEOUT)
        return user

    def authenticate(self, request) -> Tuple[UserModel, GuestToken]:
        header = self.get_header(request)
        if header is None:
            request.session['is_authenticated'] = False
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            request.session['is_authenticated'] = False
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_cached_user(validated_token)
        request.task_id = validated_token['task_id']
        request.token_type = AuthTokenType.GUEST
        request.is_superuser = False
        request.session['is_authenticated'] = True
        return user, validated_token
