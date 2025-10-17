from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

MSG_PT_0001 = _('You can\'t pass "snooze" for the first task.')
MSG_PT_0002 = _(
    'You should set task performers before setting template to active.',
)
MSG_PT_0003 = _('One or more performers are repeated.')
MSG_PT_0004 = lambda name: _(
    'Some fields referenced in the conditions of task "{name}" do not exist.',
).format(name=name)

MSG_PT_0005 = _('Selections can\'t be empty on radio or checkbox fields.')
MSG_PT_0006 = _('A field with a type \'User\' should be required.')
MSG_PT_0007 = _('Workflow template name is empty.')
MSG_PT_0008 = _('Some of fields in "workflow template name" don\'t exist.')
MSG_PT_0009 = _(
    'If a "workflow template name" contains only an output fields, '
    'at least one of the fields must be required.',
)
MSG_PT_0010 = _('Kickoff form data not provided.')
MSG_PT_0011 = _('Kickoff form \'id\' has incorrect value.')
MSG_PT_0012 = _('Kickoff \'id\' not provided.')
MSG_PT_0013 = _('Tasks data not provided, one task required.')
MSG_PT_0014 = _('Incorrect tasks order.')
MSG_PT_0016 = _('You should set \'template owners\' value.')
MSG_PT_0018 = _('You cannot remove yourself from template owners.')
MSG_PT_0019 = _('One or more template owners are incorrect.')
MSG_PT_0021 = _('"Public success url" is an invalid format.')
MSG_PT_0022 = _(
    'Filters \'with_tasks_in_progress\' and \'workflows_status\' '
    'cannot be used at the same time.',
)
MSG_PT_0023 = _('Permission denied. You are not a template owner.')
MSG_PT_0024 = _(
    'Inconsistent permission! Should use only for "workflow detail" actions.',
)
MSG_PT_0025 = _('The limit for creating a public id has been exceeded.')
MSG_PT_0026 = _('The limit for creating a embed id has been exceeded.')
# Translators: Template due date editor
MSG_PT_0027 = _('Expected date field api_name.')
# Translators: Template due date editor
MSG_PT_0028 = _('Only existing date fields can be used as a due date.')
# Translators: Template due date editor
MSG_PT_0029 = _('Expected task api_name.')
MSG_PT_0030 = _('Only previous tasks are allowed in a rule.')
MSG_PT_0031 = _('Only previous and current tasks are allowed in a rule.')
# Translators: Template performer editor
MSG_PT_0032 = _(
    'You should set the user id for performer with the type "user".',
)
MSG_PT_0033 = _('Performer "id" should be a number.')
MSG_PT_0034 = _('One or more performers are incorrect.')
MSG_PT_0035 = _(
    'A template with "Workflow starter" in the list of performers '
    'can not be shared. Please replace the "workflow starter" with '
    'another team member.',
)
MSG_PT_0036 = _(
    'You should set the field api_name for performer with the type "field".',
)
MSG_PT_0037 = lambda name: format_lazy(
    _(
        'Some fields referenced in the description of task "{name}" '
        'do not exist.',
    ),
    name=name,
)
MSG_PT_0038 = lambda name: format_lazy(
    _('Some fields in task "{name}" do not exist.'),
    name=name,
)
MSG_PT_0039 = lambda name: format_lazy(
    _(
        'Task "{name}": If the task name contains only output fields, '
        'at least one field must be required.',
    ),
    name=name,
)
MSG_PT_0040 = _('Checklist items not exists or invalid.')
MSG_PT_0041 = lambda old_api_name, new_api_name: format_lazy(
    _(
        'You can\'t change api_name of an existing object. '
        'Old value: "{old}", new value: "{new}".',
    ),
    old=old_api_name,
    new=new_api_name,
)
# Translators: Add user field value in condition with not allowed user
MSG_PT_0043 = lambda task, user_id: format_lazy(
    _(
        'Task "{task}": user id "{user_id}" doesn\'t exist '
        'or can\'t be used in this condition.',
    ),
    task=task,
    user_id=user_id,
)
# Translators: Field type inconsistent with condition operator
MSG_PT_0044 = lambda task, operator, field_type: format_lazy(
    _(
        'Task "{task}": operator "{operator}" can\'t be use '
        'with type of field "{field_type}".',
    ),
    task=task,
    operator=operator,
    field_type=field_type,
)
MSG_PT_0045 = lambda task, selection_api_name: format_lazy(
    _(
        'Task "{task}": selection "{selection_api_name}" doesn\'t exist '
        'or can\'t be used in this condition.',
    ),
    selection_api_name=selection_api_name,
    task=task,
)
# Translators: Condition operator not provided
MSG_PT_0046 = lambda task, operator: format_lazy(
    _('Task "{task}": operator "{operator}" should have some value.'),
    operator=operator,
    task=task,
)
MSG_PT_0047 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": The checklist contains a duplicate api_name '
        '"{api_name}". Recreate the checklist or change its api_name.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0048 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": The checklist item contains a duplicate api_name '
        '"{api_name}". Recreate the item or change its api_name.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0049 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": The condition contains a duplicate api_name '
        '"{api_name}". Recreate the condition or change its api_name.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0050 = lambda name, field_name, api_name: format_lazy(
    _(
        'Task "{name}": Output field "{field_name}" contains a duplicate '
        'api_name "{api_name}". '
        'Change the api_name or recreate the output field.',
    ),
    name=name,
    api_name=api_name,
    field_name=field_name,
)
MSG_PT_0051 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": The condition predicate contains a duplicate api_name '
        '"{api_name}". Recreate the predicate or change its api_name.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0052 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": The due date contains a duplicate api_name '
        '"{api_name}". Recreate the due date or change its api_name.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0053 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": The condition rule contains a duplicate api_name '
        '"{api_name}". Recreate the rule or change its api_name.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0054 = lambda name, field_name, api_name, value: format_lazy(
    _(
        'Task "{name}": Option "{value}" of output field "{field_name}" '
        'contains a duplicate api_name "{api_name}". '
        'Change the api_name or recreate the option.',
    ),
    name=name,
    field_name=field_name,
    api_name=api_name,
    value=value,
)
MSG_PT_0055 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": Contains a duplicate api_name "{api_name}". '
        'Recreate the task or change its api_name.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0056 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": The performer contains a duplicate api_name '
        '"{api_name}". Recreate the performer or change its api_name.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0057 = _('Duplicate template owners in the add owners request.')
MSG_PT_0058 = lambda name, api_name: format_lazy(
    _(
        'Template "{name}": '
        'The owners contain a duplicate api_name "{api_name}". '
        'Change the duplicate api_name or specify different owners.',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0059 = lambda name, api_name: format_lazy(
    _(
        'Task "{name}": The "Return to" setting refers to a non-existent task '
        '(API name: "{api_name}").',
    ),
    name=name,
    api_name=api_name,
)
MSG_PT_0060 = lambda name: format_lazy(
    _('Task "{name}": Cannot be set to return to itself.'),
    name=name,
)
MSG_PT_0061 = lambda name: format_lazy(
    _('Task "{name}": Can be returned only to one of its ancestors.'),
    name=name,
)
MSG_PT_0062 = lambda task, group_id: format_lazy(
    _(
        'Task "{task}": Group ID "{group_id}" '
        'does not exist or cannot be used in this condition.',
    ),
    task=task,
    group_id=group_id,
)
# Translators: Number field validation
MSG_PT_0063 = _('The value must be a number.')
MSG_PT_0064 = lambda name: format_lazy(
    _(
        'Task condition "{name}": '
        'Only the "completed" operator is allowed for the "start_task" action',
    ),
    name=name,
)
MSG_PT_0065 = lambda name: format_lazy(
    _(
        'Task "{name}" has a circular dependency. '
        'Please change the "start after" condition.',
    ),
    name=name,
)
MSG_PT_0066 = lambda name: format_lazy(
    _(
        'Task "{name}": the "start after" condition '
        'points to a non-existent task. '
        'Please change the "start after" condition.',
    ),
    name=name,
)
MSG_PT_0067 = lambda name: format_lazy(
    _(
        'Task "{name}": the "check if" condition '
        'points to a non-existent task. '
        'Please change the "check if" condition.',
    ),
    name=name,
)
MSG_PT_0068 = lambda name: format_lazy(
    _(
        'Task "{name}": the "check if" condition '
        'points to a non ancestor task. '
        'Please change the "check if" condition.',
    ),
    name=name,
)
