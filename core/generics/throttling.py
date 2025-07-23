# pylint: disable=super-init-not-called,attribute-defined-outside-init
from typing import Optional
from rest_framework.throttling import SimpleRateThrottle
from django.core.exceptions import ImproperlyConfigured
from pneumatic_backend.authentication.enums import AuthTokenType


class CustomSimpleRateThrottle(SimpleRateThrottle):

    """ Limits the rate of anonymous API calls.

    * Unlike ScopedRateThrottle and throttling decorator,
    in allows throttling to be applied to the basic viewset actions
    as 'create' and 'retrieve'

    * Unlike the drf throttling implementation, it counts the speed,
        not the number of request at a time """

    def __init__(self):
        self.need_wait = False

    def get_rate(self):
        """
        Determine the string representation of the allowed request rate.
        """
        if not getattr(self, 'scope', None):
            msg = (
                "You must set either `.scope` or "
                "`.rate` for '%s' throttle" %
                self.__class__.__name__
            )
            raise ImproperlyConfigured(msg)

        return self.THROTTLE_RATES.get(self.scope)

    def get_cache_key(self, request, *args, **kwargs) -> str:
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }

    def throttle_success(self):
        self.cache.set(self.key, self.current_request_time, self.period)
        return True

    def skip_condition(self, *args, **kwargs) -> bool:

        """ Should return 'True' if throttling is not required """

        if self.get_rate() is None:
            return True

    def _get_period(self):
        num_requests, duration = self.parse_rate(self.rate)
        return duration / num_requests

    def _allow_request(self, request) -> bool:

        """ Returns 'False' if request should be throttled """

        self.rate = self.get_rate()
        self.period = self._get_period()
        self.key = self.get_cache_key(request)
        self.prev_request_time = self.cache.get(self.key, None)
        self.current_request_time = self.timer()
        if self.prev_request_time is None:
            return self.throttle_success()

        self.wait_time = (
            self.prev_request_time + self.period - self.current_request_time
        )
        self.need_wait = self.wait_time >= 0
        if self.need_wait:
            return self.throttle_failure()
        return self.throttle_success()

    def allow_request(self, request, view) -> bool:

        """ Returns 'False' if request should be throttled """

        if self.skip_condition(request):
            return True
        return self._allow_request(request)

    def wait(self) -> Optional[int]:
        """
        Returns the recommended next request time in seconds.
        """
        if self.need_wait:
            return self.wait_time
        return None


class AnonThrottle(CustomSimpleRateThrottle):

    """ The IP address of the request will be used as the unique cache key
        Runs only for anonymous requests """

    def skip_condition(self, request) -> bool:

        if super().skip_condition(request):
            return True
        return request.user.is_authenticated


class BaseAuthThrottle(CustomSimpleRateThrottle):

    skip_for_paid_accounts = True

    def skip_condition(self, request) -> bool:

        if super().skip_condition(request):
            return True
        user = request.user
        if not user.is_authenticated:
            return True
        elif self.skip_for_paid_accounts and user.account.is_paid:
            return True
        else:
            return False


class TokenThrottle(BaseAuthThrottle):

    """ The user id will be used as the unique cache key
        Runs only for authenticated users via user token"""

    def get_ident(self, request) -> str:
        return str(request.user.pk)

    def skip_condition(self, request) -> bool:

        if super().skip_condition(request):
            return True
        elif request.token_type != AuthTokenType.USER:
            return True
        else:
            return False


class ApiKeyThrottle(BaseAuthThrottle):

    """ The account API key id will be used as the unique cache key
        Runs only for authenticated users via API token """

    def get_ident(self, request) -> str:
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        token = auth_header.split()[1]
        return token

    def skip_condition(self, request) -> bool:

        if super().skip_condition(request):
            return True
        elif request.token_type != AuthTokenType.API:
            return True
        else:
            return False
