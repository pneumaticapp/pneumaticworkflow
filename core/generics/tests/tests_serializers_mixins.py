import pytest
from rest_framework.serializers import ValidationError
from pneumatic_backend.generics.mixins.serializers import (
    ValidationUtilsMixin,
    CustomValidationErrorMixin
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.generics.messages import (
    MSG_GE_0003,
    MSG_GE_0004,
)


class TestValidationUtilsMixin:

    def test_get_valid_list_integers__simple_value__ok(self):

        # arrange
        raw_value = '23'
        true_value = [23]
        mixin = ValidationUtilsMixin()

        # act
        validated_value = mixin.get_valid_list_integers(raw_value)

        # assert
        assert validated_value == true_value

    @pytest.mark.parametrize('raw_value', ('1, 23', '1,23'))
    def test_get_valid_list_integers__complex_value__ok(self, raw_value):

        # arrange
        true_value = [1, 23]
        mixin = ValidationUtilsMixin()

        # act
        validated_value = mixin.get_valid_list_integers(raw_value)

        # assert
        assert validated_value == true_value

    @pytest.mark.parametrize(
        'raw_value',
        ('undefined', None, [], '1,a', '1 23', ',1,23,')
    )
    def test_get_valid_list_integers__invalid_value__validation_error(
        self,
        raw_value
    ):
        # arrange
        mixin = ValidationUtilsMixin()

        # act
        with pytest.raises(ValidationError) as e:
            mixin.get_valid_list_integers(raw_value)

        # assert
        assert e.value.detail[0] == MSG_GE_0003


class TestCustomValidationErrorMixin:

    def test_raise_validation_error__error_by_api_name__format_ok(self):

        # arrange
        api_name = 'api-name'
        mixin = CustomValidationErrorMixin()
        mixin._validated_data = 'not-empty'
        message = 'Test message'

        # act
        with pytest.raises(ValidationError) as e:
            mixin.raise_validation_error(
                message=message,
                api_name=api_name
            )

        # assert
        error = e.value.detail
        assert error['code'] == ErrorCode.VALIDATION_ERROR
        assert error['message'] == message
        assert error['details']['api_name'] == api_name
        assert error['details']['reason'] == message

    def test_raise_validation_error__error_by_name__format_ok(self):

        # arrange
        name = 'test-name'
        mixin = CustomValidationErrorMixin()
        mixin._validated_data = 'not-empty'
        message = 'Test message'

        # act
        with pytest.raises(ValidationError) as e:
            mixin.raise_validation_error(
                message=message,
                name=name
            )

        # assert
        error = e.value.detail
        assert error['code'] == ErrorCode.VALIDATION_ERROR
        assert error['message'] == message
        assert error['details']['name'] == name
        assert error['details']['reason'] == message

    def test_raise_validation_error__common_error__format_ok(self):

        # arrange
        mixin = CustomValidationErrorMixin()
        mixin._validated_data = 'not-empty'
        message = 'Test message'

        # act
        with pytest.raises(ValidationError) as e:
            mixin.raise_validation_error(message=message)

        # assert
        error = e.value.detail
        assert error['code'] == ErrorCode.VALIDATION_ERROR
        assert error['message'] == message
        assert 'details' not in error.keys()

    def test_raise_validation_error__before_is_valid__exception(self):

        # arrange
        mixin = CustomValidationErrorMixin()
        message = 'Test message'

        # act
        with pytest.raises(Exception) as e:
            mixin.raise_validation_error(message=message)

        # assert
        assert str(e.value) == MSG_GE_0004
