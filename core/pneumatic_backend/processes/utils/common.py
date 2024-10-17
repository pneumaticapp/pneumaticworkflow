# pylint: disable=protected-access
import re
from typing import Optional
from datetime import timedelta
from typing import (
    Type, List, Set, Dict, Union
)

from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, ListSerializer
from pneumatic_backend.utils.salt import get_salt

VAR_PATTERN = re.compile(r'{{\s*([^\{\}\s]+)\s*}}')
VAR_PATTERN_TEMPLATE = r'\{\{(\s*?)%s(\s*?)\}\}'
VAR_PATTERN_FIELD = re.compile(
    r'\{\{(\s*?)((?!date|template-name).)+(\s*?)\}\}'
)


def is_tasks_ordering_correct(tasks: List[int]) -> bool:
    tasks_set = set(tasks)
    if len(tasks) > len(tasks_set):
        return False
    if tasks_set and tasks_set != set(range(1, max(tasks_set) + 1)):
        return False
    return True


def are_users_in_process_account(
    user_ids: Union[Set[int], List[int]],
    account_id: Type[int]
) -> bool:

    UserModel = get_user_model()
    if not user_ids:
        return True
    return UserModel.objects.are_users_in_account(
        account_id,
        user_ids
    )


def get_prefetch_fields(serializer) -> List[str]:
    related_fields = []

    for field, handler in serializer._declared_fields.items():
        field_name = handler.source or field
        if isinstance(handler, ModelSerializer):
            related_fields.extend(
                f'{field_name}__{related}' for related in
                get_prefetch_fields(handler)
            )

            related_fields.append(field_name)

        elif isinstance(handler, ListSerializer):
            related_fields.extend(
                f'{field_name}__{related}' for related in
                get_prefetch_fields(handler.child)
            )

            related_fields.append(field_name)

    return related_fields


def string_abbreviation(
    name: str,
    length: int,
    postfix: str = '',
    with_ellipsis: bool = True
) -> str:
    if name is None:
        return postfix[:length]
    if (len(name) + len(postfix)) > length:
        cut_length = len(name) + len(postfix) - length

        if with_ellipsis:
            name = f'{name[:-(cut_length+1)]}…'
        else:
            name = f'{name[:-cut_length]}'

    return f'{name}{postfix}'


def contains_fields_vars(value: Optional[str] = None) -> bool:

    """ Exclude system vars like date and template-name """

    if not value:
        return False
    return bool(VAR_PATTERN_FIELD.search(value))


def contains_vars(value: Optional[str] = None) -> bool:

    if not value:
        return False
    return bool(VAR_PATTERN.search(value))


def insert_fields_values_to_text(
    text: Optional[str],
    fields_values: Dict[str, str]
) -> str:

    if contains_vars(text):
        for api_name, value in fields_values.items():
            field_variable_pattern = VAR_PATTERN_TEMPLATE % api_name
            text = re.sub(field_variable_pattern, value, text)
    return text


def insert_kickoff_fields_vars(workflow) -> str:

    """ Insert kickoff fields values to the workflow name """

    fields_values = workflow.get_kickoff_fields_values()
    return insert_fields_values_to_text(
        text=workflow.name_template,
        fields_values=fields_values
    )


def get_duration_format(duration: timedelta) -> str:
    """ Format example: 15 days 6 hours 23 minutes"""
    def plural(n, word):
        return (
            f'1 {word}' if n == 1 else
            f'{n} {word + "s"}'
        )
    duration = abs(int(duration.total_seconds()))
    days, seconds = divmod(duration, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if not days and not hours and not minutes:
        return 'Less than 1 minute'
    result_str = f'{plural(minutes, "minute")}'
    if days or hours:
        result_str = f'{plural(hours, "hour")} {result_str}'
    if days:
        result_str = f'{plural(days, "day")} {result_str}'
    return result_str


def get_user_agent(request) -> Optional[str]:
    return request.headers.get(
        'User-Agent',
        request.META.get('HTTP_USER_AGENT')
    )


def create_api_name(prefix: str) -> str:
    salt = get_salt(6, exclude=('upper',))
    return f'{prefix}-{salt}'
