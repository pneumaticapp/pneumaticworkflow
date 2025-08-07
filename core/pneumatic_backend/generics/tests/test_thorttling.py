import pytest
from pneumatic_backend.generics.throttling import (
    CustomSimpleRateThrottle,
    TokenThrottle,
    ApiKeyThrottle,
    AnonThrottle
)
from pneumatic_backend.authentication.enums import AuthTokenType


pytestmark = pytest.mark.django_db


class TestCustomSimpleRateThrottle:

    def test_init__ok(self):

        # act
        service = CustomSimpleRateThrottle()

        # assert
        assert service.need_wait is False

    def test_get_rate__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        rate_value = '1/s'
        service = CustomSimpleRateThrottle()
        service.scope = 'scope'
        service.THROTTLE_RATES = {'scope': rate_value}

        # act
        result = service.get_rate()

        # assert
        assert result == rate_value

    def test_get_rate__not_rate__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        service = CustomSimpleRateThrottle()
        service.scope = 'scope'
        service.THROTTLE_RATES = {}

        # act
        result = service.get_rate()

        # assert
        assert result is None

    def test_get_period__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        num_requests, duration = 3, 60
        parse_rate_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.parse_rate',
            return_value=(num_requests, duration)
        )
        service = CustomSimpleRateThrottle()
        service.rate = '3/min'

        # act
        period = service._get_period()

        # assert
        parse_rate_mock.assert_called_once_with(service.rate)
        assert period == 20

    def test_allow_request__run_throttling__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        return_mock = mocker.Mock()
        allow_request_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '._allow_request',
            return_value=return_mock
        )

        request = mocker.Mock()
        view = mocker.Mock()
        throttle = CustomSimpleRateThrottle()

        # act
        result = throttle.allow_request(request, view)

        # assert
        skip_condition_mock.assert_called_once_with(request)
        allow_request_mock.assert_called_once_with(request)
        assert result is return_mock

    def test_allow_request__skip_throttling(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=True
        )
        allow_request_mock = mocker.patch(
            'rest_framework.throttling.SimpleRateThrottle.allow_request',
        )

        request = mocker.Mock()
        view = mocker.Mock()
        throttle = CustomSimpleRateThrottle()

        # act
        result = throttle.allow_request(request, view)

        # assert
        skip_condition_mock.assert_called_once_with(request)
        allow_request_mock.assert_not_called()
        assert result is True

    def test_get_cache_key__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        scope = 'scope'
        ident = 7
        get_ident_mock = mocker.patch(
            'rest_framework.throttling.SimpleRateThrottle.get_ident',
            return_value=ident
        )

        request = mocker.Mock()
        view = mocker.Mock()
        throttle_cls = CustomSimpleRateThrottle
        throttle_cls.scope = scope
        throttle = throttle_cls()

        # act
        result = throttle.get_cache_key(request, view)

        # assert
        get_ident_mock.assert_called_once_with(request)
        assert result == 'throttle_%(scope)s_%(ident)s' % {
            'scope': scope,
            'ident': str(ident)
        }

    def test_throttle_success__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        period = 3
        current_request_time = 65
        key = 'key'
        cache_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.cache',
        )
        cache_mock.set = mocker.Mock()
        service = CustomSimpleRateThrottle()
        service.period = period
        service.key = key
        service.current_request_time = current_request_time

        # act
        result = service.throttle_success()

        # assert
        cache_mock.set.assert_called_once_with(
            key, current_request_time, period
        )
        assert result is True

    def test_skip_condition__not_rate__skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        get_rate_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.get_rate',
            return_value=None
        )
        service = CustomSimpleRateThrottle()

        # act
        result = service.skip_condition()

        # assert
        assert result is True
        get_rate_mock.assert_called_once()

    def test_private_allow_request__not_prev_request_time__allow(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        rate = '3/s'
        get_rate_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.get_rate',
            return_value=rate
        )
        period = 0.3
        get_period_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '._get_period',
            return_value=period
        )
        key = 'key'
        get_cache_key_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.get_cache_key',
            return_value=key
        )
        cache_get_mock = mocker.Mock(return_value=None)
        mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.cache',
            get=cache_get_mock
        )
        throttle_success_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.throttle_success',
            return_value=True
        )
        request = mocker.Mock()
        service = CustomSimpleRateThrottle()

        # act
        result = service._allow_request(request)

        # assert
        get_rate_mock.get_period_mock()
        get_period_mock.assert_called_once()
        get_cache_key_mock.assert_called_once_with(request)
        cache_get_mock.assert_called_once_with(key, None)
        throttle_success_mock.assert_called_once()
        assert service.prev_request_time is None
        assert result is True

    def test_private_allow_request__period_expired__allow(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        key = 'key'
        mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.get_cache_key',
            return_value=key
        )
        rate = '3/s'
        get_rate_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.get_rate',
            return_value=rate
        )
        period = 0.3
        get_period_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '._get_period',
            return_value=period
        )
        prev_request_time = 1639048599.1951413
        prev_request_time_mock = mocker.Mock(return_value=prev_request_time)
        mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.cache',
            get=prev_request_time_mock
        )
        current_request_time = prev_request_time + 0.4
        current_request_time_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.timer',
            return_value=current_request_time
        )
        result_mock = mocker.Mock()
        throttle_success_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.throttle_success',
            return_value=result_mock
        )
        request = mocker.Mock()
        service = CustomSimpleRateThrottle()

        # act
        result = service._allow_request(request)

        # assert
        prev_request_time_mock.assert_called_once_with(key, None)
        current_request_time_mock.assert_called_once()
        throttle_success_mock.assert_called_once()
        get_rate_mock.assert_called_once()
        get_period_mock.assert_called_once()
        assert result is result_mock
        assert service.need_wait is False
        assert service.wait_time < 0

    def test_private_allow_request__period_not_expired__disallow(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        key = 'key'
        mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.get_cache_key',
            return_value=key
        )
        rate = '3/s'
        get_rate_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.get_rate',
            return_value=rate
        )
        period = 0.3
        get_period_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '._get_period',
            return_value=period
        )
        prev_request_time = 1639048599.1951413
        prev_request_time_mock = mocker.Mock(return_value=prev_request_time)
        cache_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.cache'
        )
        cache_mock.get = prev_request_time_mock
        current_request_time = prev_request_time + 0.2
        current_request_time_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.timer',
            return_value=current_request_time
        )
        result_mock = mocker.Mock()
        throttle_failure_mock = mocker.patch(
            'rest_framework.throttling.SimpleRateThrottle'
            '.throttle_failure',
            return_value=result_mock
        )
        request = mocker.Mock()
        service = CustomSimpleRateThrottle()

        # act
        result = service._allow_request(request)

        # assert
        get_rate_mock.assert_called_once()
        prev_request_time_mock.assert_called_once_with(key, None)
        current_request_time_mock.assert_called_once()
        throttle_failure_mock.assert_called_once()
        get_period_mock.assert_called_once()
        assert result is result_mock
        assert service.need_wait is True
        assert service.wait_time > 0

    def test_wait__return_wait_time(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        wait_time = 3
        service = CustomSimpleRateThrottle()
        service.need_wait = True
        service.wait_time = wait_time

        # act
        result = service.wait()

        # assert
        assert result == wait_time

    def test_wait__no_wait(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        service = CustomSimpleRateThrottle()
        service.need_wait = False

        # act
        result = service.wait()

        # assert
        assert result is None


class TestAnonThrottle:

    def test_skip_condition__skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_subscribed=True)
        user_mock = mocker.Mock(
            is_authenticated=True,
            account=account_mock
        )
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.USER,
        )
        throttle = AnonThrottle()

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is True
        super_skip_condition_mock.assert_called_once()

    def test_skip_condition__not_skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        user_mock = mocker.Mock(is_authenticated=False)
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.USER
        )
        throttle = AnonThrottle()

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is False
        super_skip_condition_mock.assert_called_once()


class TestTokenThrottle:

    def test_skip_condition__user_not_authenticated__skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_subscribed=True)
        user_mock = mocker.Mock(
            is_authenticated=False,
            account=account_mock
        )
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.USER
        )
        throttle = TokenThrottle()

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is True
        super_skip_condition_mock.assert_called_once()

    def test_skip_condition__skip_for_paid_account__skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_paid=True)
        user_mock = mocker.Mock(
            is_authenticated=True,
            account=account_mock
        )
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.USER
        )
        throttle = TokenThrottle()

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is True
        super_skip_condition_mock.assert_called_once()

    def test_skip_condition__not_skip_for_paid_account__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_paid=True)
        user_mock = mocker.Mock(
            is_authenticated=True,
            account=account_mock
        )
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.USER
        )
        throttle = TokenThrottle()
        throttle.skip_for_paid_accounts = False

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is False
        super_skip_condition_mock.assert_called_once()

    def test_skip_condition__api_request__skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_paid=True)
        user_mock = mocker.Mock(
            is_authenticated=True,
            account=account_mock
        )
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.API
        )
        throttle = TokenThrottle()

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is True
        super_skip_condition_mock.assert_called_once()

    def test_get_ident__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        pk = 7
        user_mock = mocker.Mock(pk=pk)
        request = mocker.Mock(user=user_mock)
        throttle = TokenThrottle()

        # act
        result = throttle.get_ident(request)

        # assert
        assert result == '7'


class TestApiKeyThrottle:

    def test_skip_condition__user_not_authenticated__skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_subscribed=True)
        user_mock = mocker.Mock(
            is_authenticated=False,
            account=account_mock
        )
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.USER
        )
        throttle = ApiKeyThrottle()

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is True
        super_skip_condition_mock.assert_called_once()

    def test_skip_condition__skip_for_paid_account__skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_paid=True)
        user_mock = mocker.Mock(
            is_authenticated=True,
            account=account_mock
        )
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.USER
        )
        throttle = ApiKeyThrottle()

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is True
        super_skip_condition_mock.assert_called_once()

    def test_skip_condition__not_skip_for_paid_account__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_paid=True)
        user_mock = mocker.Mock(
            is_authenticated=True,
            account=account_mock
        )
        request = mocker.Mock(
            user=user_mock,
            token_type=AuthTokenType.API
        )
        throttle = ApiKeyThrottle()
        throttle.skip_for_paid_accounts = False

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is False
        super_skip_condition_mock.assert_called_once()

    def test_skip_condition__not_api_request__skip(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        super_skip_condition_mock = mocker.patch(
            'pneumatic_backend.generics.throttling.CustomSimpleRateThrottle'
            '.skip_condition',
            return_value=False
        )
        account_mock = mocker.Mock(is_paid=False)
        user_mock = mocker.Mock(
            is_authenticated=True,
            account=account_mock
        )
        request = mocker.Mock(
            token_type=AuthTokenType.USER,
            user=user_mock
        )
        throttle = ApiKeyThrottle()

        # act
        result = throttle.skip_condition(request)

        # assert
        assert result is True
        super_skip_condition_mock.assert_called_once()

    def test_get_ident__ok(self, mocker):

        # arrange
        mocker.patch.object(
            CustomSimpleRateThrottle,
            attribute='__init__',
            return_value=None
        )
        token = '123'
        headers_mock = {
            'HTTP_AUTHORIZATION': f'Bearer {token}'
        }
        request = mocker.Mock(META=headers_mock)
        throttle = ApiKeyThrottle()

        # act
        result = throttle.get_ident(request)

        # assert
        assert result == token
