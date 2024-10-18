# pylint: disable=no-name-in-module
from ast import literal_eval
from collections import OrderedDict, Iterable
from collections.abc import Mapping
from django.core.exceptions import ValidationError as DjangoValidationError
from typing import Dict, Any, List, Optional, Union
from rest_framework.exceptions import ValidationError
from rest_framework.settings import api_settings
from rest_framework.serializers import as_serializer_error
from rest_framework.fields import (
    Field,
    SkipField,
    get_error_detail,
    set_value,
    empty
)
from pneumatic_backend.utils.validation import (
    raise_validation_error,
    ErrorCode
)
from pneumatic_backend.generics.entities import (
    ValidationErrorData
)
from pneumatic_backend.generics.messages import (
    MSG_GE_0003,
    MSG_GE_0004,
    MSG_GE_0005,
)


class ValidationUtilsMixin:

    """ Methods for common validation functionality"""

    @staticmethod
    def get_valid_list_integers(raw_value: str) -> List[int]:

        """ Validates and returns list of integers
           '1,23,4' -> [1, 23, 4]"""

        validation_error = ValidationError(MSG_GE_0003)
        result = []
        try:
            value = literal_eval(raw_value)
        except (TypeError, ValueError, SyntaxError):
            raise validation_error
        else:
            if isinstance(value, int):
                result = [value]
            elif isinstance(value, Iterable):
                if not value:
                    raise validation_error
                for number in value:
                    try:
                        result.append(int(number))
                    except (TypeError, ValueError):
                        raise validation_error
            else:
                raise validation_error
            return result


class AdditionalValidationMixin:

    """ Functionality for additional validation in serializers """

    def additional_validate(self, data: Dict[str, Any]):

        """ Runs additional validation after DRF validation
            for each field in Meta.fields. The difference is that
            the validated_data already exists and useful

            The signature of the custom validation method for "id" field:

                def additional_validate_id(value: Any, data:Dict[str, Any]):
                    pass
        """

        if not hasattr(self.Meta, 'fields'):
            raise Exception(MSG_GE_0005)

        for field_name in self.Meta.fields:
            method_name = f'additional_validate_{field_name}'
            method = getattr(self, method_name, None)
            if method:
                method(value=data.get(field_name), data=data)


class CustomValidationErrorMixin:

    """ Allow change DRF validation errors format to custom.
        For more information see is_valid method docs """

    _enriched_key = 'enriched__'
    _message_key = 'message__'
    _api_name_key = 'api_name__'
    _name_key = 'name__'
    _enrich_keys = {_message_key, _api_name_key, _name_key}
    _special_keys = {_message_key, _api_name_key, _name_key, _enriched_key}
    _null_values = ('None', None, '', {}, [])

    def _get_data_for_enrichment(
        self,
        fields_data: Mapping,
        field: Optional[Field] = None
    ) -> dict:

        """ The method determines what additional data
            will be added to the error body """

        if field is None:
            name = api_settings.NON_FIELD_ERRORS_KEY
        else:
            name = field.field_name
        try:
            api_name = fields_data.get('api_name')
        except AttributeError:
            api_name = None
        return {
            self._name_key: name,
            self._api_name_key: api_name,
            self._enriched_key: True
        }

    def _enrich_error_detail(
        self,
        fields_data: Mapping,
        detail: Union[Iterable, Mapping, str],
        field: Optional[Field] = None
    ) -> dict:

        """ Adds additional information to the error body.

            Error body:
            'rules': {
              'errors': ['This list may not be empty.']
            }

            Extended error body:
            'rules': {
              'api_name__': 'condition-66',
              'name__': condition,
              'errors': [
                {
                  'message__': 'This list may not be empty.',
                  'api_name__': None,
                  'name__': rules,
                }
              ]
            }
        """

        if detail:
            if isinstance(detail, list):
                for number, sub_detail in enumerate(detail):
                    if isinstance(sub_detail, str):
                        sub_detail = {self._message_key: sub_detail}
                        sub_detail.update(
                            self._get_data_for_enrichment(
                                fields_data=fields_data,
                                field=field
                            )
                        )
                        detail[number] = sub_detail
                    else:
                        detail[number] = self._enrich_error_detail(
                            fields_data=fields_data,
                            detail=sub_detail,
                            field=field
                        )
            elif isinstance(detail, dict):
                if self._enriched_key not in detail.keys():
                    for key, sub_detail in detail.items():
                        if isinstance(sub_detail, str):
                            sub_detail = {self._message_key: sub_detail}
                            sub_detail.update(
                                self._get_data_for_enrichment(
                                    fields_data=fields_data,
                                    field=field
                                )
                            )
                            detail[key] = sub_detail
                        else:
                            detail[key] = self._enrich_error_detail(
                                fields_data=fields_data,
                                detail=sub_detail,
                                field=field
                            )
                    detail.update(
                        self._get_data_for_enrichment(
                            fields_data=fields_data,
                            field=field
                        )
                    )
            elif isinstance(detail, str):
                detail = {self._message_key: detail}
                detail.update(
                    self._get_data_for_enrichment(
                        fields_data=fields_data,
                        field=field
                    )
                )
        return detail

    def _get_errors_from_list(self, data: list, default: dict) -> List[dict]:

        """ Gets an enriched list of data,
            and returns a list of errors found

            Example:
              data = [
                {
                  'name__': 'conditions',
                  'api_name__': 'condition-666',
                  'rules': {
                    'name__': 'rules',
                    'api_name__': None,
                    'errors': ['This list may not be empty.']
                  ...

              Errors in result:
                [
                  {
                    'name': 'rules',
                    'api_name': 'condition-666',
                    'message': 'This list may not be empty.'
                  }
                ] """

        errors = []
        for value in data:
            if value not in self._null_values:
                if isinstance(value, dict):
                    errors.extend(
                        self._get_errors_from_dict(
                            data=value,
                            default=default
                        )
                    )
                elif isinstance(value, list):
                    for sub_value in value:
                        if sub_value not in self._null_values:
                            if isinstance(sub_value, dict):
                                errors.extend(
                                    self._get_errors_from_dict(
                                        data=sub_value,
                                        default=default
                                    )
                                )
                            elif isinstance(sub_value, list):
                                errors.extend(
                                    self._get_errors_from_list(
                                        data=sub_value,
                                        default=default
                                    )
                                )
        return errors

    def _get_errors_from_dict(self, data: dict, default: dict) -> List[dict]:

        """ Gets an enriched dict of data,
            and returns a list of errors found

            Example:
              data = {
                'name__': 'conditions',
                'api_name__': 'condition-666',
                'rules': {
                  'name__': 'rules',
                  'api_name__': None,
                  'errors': ['This list may not be empty.']
              ...

              Errors in result:
                [
                  {
                    'name': 'rules',
                    'api_name': 'condition-666',
                    'message': 'This list may not be empty.'
                  }
                ] """

        error = {}
        data.pop(self._enriched_key, None)
        for key in self._enrich_keys:
            value = data.pop(key, None)
            default_value = default.get(key)
            if value not in self._null_values:
                error[key] = value
            elif default_value not in self._null_values:
                error[key] = default_value

        if data.keys():
            errors = []
            for key, value in data.items():
                if value not in self._null_values:
                    if isinstance(value, list):
                        errors.extend(self._get_errors_from_list(
                            data=value,
                            default=error
                        ))
                    if isinstance(value, dict):
                        errors.extend(self._get_errors_from_dict(
                            data=value,
                            default=error
                        ))
            return errors
        else:
            return [error]

    def _get_formatted_error(self, error: dict) -> ValidationErrorData:

        """ Defines the body of the error.
            Three cases are possible:
            1. Common error - the error does not apply to a specific field
            2. Nested field error - the field api_name is unique
            3. Simple field error - the field name is unique
               and located at the top level of the form. """

        name = error.get(self._name_key)
        api_name = error.get(self._api_name_key)
        message = error.get(self._message_key)

        if name == api_settings.NON_FIELD_ERRORS_KEY:
            return ValidationErrorData(
                message=message,
                code=ErrorCode.VALIDATION_ERROR
            )
        elif api_name:
            message = f'{name.capitalize()}: {message.lower()}'
            return ValidationErrorData(
                message=message,
                code=ErrorCode.VALIDATION_ERROR,
                details={
                    'api_name': api_name,
                    'reason': message
                }
            )
        else:
            return ValidationErrorData(
                message=message,
                code=ErrorCode.VALIDATION_ERROR,
                details={
                    'name': name,
                    'reason': message
                }
            )

    def run_validation(self, data=empty):

        """ Overridden for use
            _enrich_error_detail method to the error body"""

        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data

        value = self.to_internal_value(data)
        try:
            self.run_validators(value)
            value = self.validate(value)
            msg = '.validate() should return the validated data'
            assert value is not None, msg

        except (ValidationError, DjangoValidationError) as exc:
            detail = self._enrich_error_detail(
                detail=as_serializer_error(exc),
                fields_data=value
            )
            raise ValidationError(detail)

        return value

    def to_internal_value(self, data):

        """ Overridden for use
            _enrich_error_detail method to the error body"""

        if not isinstance(data, Mapping):
            message = self.error_messages['invalid'].format(
                datatype=type(data).__name__
            )
            error_detail = self._enrich_error_detail(
                detail={api_settings.NON_FIELD_ERRORS_KEY: [message]},
                fields_data=data
            )
            raise ValidationError(error_detail, code='invalid')

        ret = OrderedDict()
        errors = OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method_name = 'validate_' + field.field_name
            validate_method = getattr(self, validate_method_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[field.field_name] = self._enrich_error_detail(
                    detail=exc.detail,
                    fields_data=data,
                    field=field
                )
            except DjangoValidationError as exc:
                errors[field.field_name] = self._enrich_error_detail(
                    detail=get_error_detail(exc),
                    fields_data=data,
                    field=field
                )
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise ValidationError(errors)

        return ret

    def is_valid(self, raise_exception=False):

        """ Overridden to raise a first validation error in a custom format

            Enriched framework format:
              'tasks': [
                {
                  'name__': 'tasks',
                  'api_name__': 'task-66',
                  'conditions': [
                    {
                      'name__': 'conditions',
                      'api_name__': 'condition-66',
                      'rules': {
                        'errors': [
                          {
                            'message__': 'This list may not be empty.',
                            'name__': 'rules'
                            'api_name__': None
                        ...

            Custom format:
              {
                'message': 'Rules: this list may not be empty.'
                'code': 'validation_error'
                'details': {
                  'api_name': 'condition-66'
                  'reason': 'Rules: this list may not be empty.'
                }
              }
        """

        result = super().is_valid(raise_exception=False)
        if self._errors and raise_exception:
            errors = self._get_errors_from_dict(data=self._errors, default={})
            first_error = self._get_formatted_error(errors[0])
            raise ValidationError(first_error)
        return result

    def raise_validation_error(
        self,
        message: str,
        name: Optional[str] = None,
        api_name: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        **kwargs
    ):
        if not hasattr(self, '_validated_data'):
            raise Exception(MSG_GE_0004)
        raise_validation_error(
            message=message,
            name=name,
            api_name=api_name,
            error_code=error_code,
            **kwargs
        )
