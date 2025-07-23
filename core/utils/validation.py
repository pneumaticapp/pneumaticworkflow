from typing import Optional
from rest_framework.exceptions import ValidationError

from pneumatic_backend.generics.entities import (
    ValidationErrorData
)


class ErrorCode:

    VALIDATION_ERROR = 'validation_error'
    INVITE_ALREADY_ACCEPTED = 'invite_already_accepted'


def raise_validation_error(
    message: str,
    name: Optional[str] = None,
    api_name: Optional[str] = None,
    error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
    **kwargs
):
    """ Short functionality for raising validation error

        The error has a different format depending on the attributes
        1. Common error - the error does not apply to a specific field
        2. Nested field error - the field api_name is unique
        3. Simple field error - the field name is unique
           and located at the top level of the form.
    """
    if message is None:
        raise AttributeError(
            '"Message" and can\'t be is None at the same time'
        )
    data = ValidationErrorData(
        code=error_code,
        message=message,
        details={**kwargs}
    )
    if api_name:
        data['details']['reason'] = message
        data['details']['api_name'] = api_name
    elif name:
        data['details']['reason'] = message
        data['details']['name'] = name

    raise ValidationError(data)
