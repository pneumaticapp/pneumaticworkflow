import re
from typing import Optional
from datetime import timedelta
from typing import (
    Type, List, Set, Dict, Union,
)
from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, ListSerializer

from src.processes.enums import (
    PredicateOperator,
    PredicateType,
    ConditionAction,
)
from src.utils.salt import get_salt

VAR_PATTERN = re.compile(r'{{\s*([^\{\}\s]+)\s*}}')
VAR_PATTERN_TEMPLATE = r'\{\{(\s*?)%s(\s*?)\}\}'
VAR_PATTERN_FIELD = re.compile(
    r'\{\{(\s*?)((?!date|template-name).)+(\s*?)\}\}',
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
    account_id: Type[int],
) -> bool:

    UserModel = get_user_model()
    if not user_ids:
        return True
    return UserModel.objects.are_users_in_account(
        account_id,
        user_ids,
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
    with_ellipsis: bool = True,
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
    fields_values: Dict[str, str],
) -> str:

    if contains_vars(text):
        for api_name, raw_value in fields_values.items():
            value = '' if raw_value is None else raw_value
            field_variable_pattern = VAR_PATTERN_TEMPLATE % api_name
            text = re.sub(field_variable_pattern, value, text)
    return text


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
        request.META.get('HTTP_USER_AGENT'),
    )


def create_api_name(prefix: str) -> str:
    salt = get_salt(6, exclude=('upper',))
    return f'{prefix}-{salt}'


def get_tasks_parents(tasks_data: List[Dict]) -> dict:

    """ Find and return task parents api_names """

    parents_by_tasks = {}
    available_api_names = {
        e['api_name'] for e in tasks_data if e.get('api_name')
    }
    for task_data in tasks_data:
        task_api_name = task_data.get('api_name')
        if task_api_name is None:
            continue
        parents_by_tasks[task_api_name] = []
        for cond in task_data.get('conditions', ()):
            if cond.get('action') == ConditionAction.START_TASK:
                for rule in cond.get('rules', ()):
                    for p in rule.get('predicates', ()):
                        try:
                            if (
                                p['operator'] == PredicateOperator.COMPLETED
                                and p['field_type'] == PredicateType.TASK
                                and p['field'] in available_api_names
                            ):
                                parents_by_tasks[task_api_name].append(
                                    p['field'],
                                )
                        except KeyError:
                            pass
    return parents_by_tasks


def get_tasks_ancestors(data: Dict[str, set]) -> Dict[str, set]:

    """ Find and return task all ancestors api_names """

    new_ancestors_found = False
    ancestors_by_tasks = {}
    for task, ancestors in data.items():
        current_ancestors = set(ancestors)
        for ancestor in ancestors:
            grand_ancestors = set(data[ancestor])
            new_ancestors = grand_ancestors - current_ancestors
            if new_ancestors:
                current_ancestors.update(new_ancestors)
                new_ancestors_found = True
        ancestors_by_tasks[task] = current_ancestors

    if new_ancestors_found:
        return get_tasks_ancestors(ancestors_by_tasks)
    else:
        return ancestors_by_tasks
