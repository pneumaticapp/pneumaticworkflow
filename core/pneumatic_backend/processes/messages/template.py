from django.utils.translation import ugettext_lazy as _
from django.utils.text import format_lazy


MSG_PT_0001 = _('You can\'t pass "snooze" for the first step.')
MSG_PT_0002 = _(
    'You should set task performers before setting template to active.'
)
MSG_PT_0003 = _('One or more performers are repeated.')
MSG_PT_0004 = lambda name: _(
    'Some fields in the task "{name}" '
    'conditions don\'t exist or are used before assignment.'
).format(name=name)
MSG_PT_0005 = _('Selections can\'t be empty on radio or checkbox fields.')
MSG_PT_0006 = _('A field with a type \'User\' should be required.')
MSG_PT_0007 = _('Workflow template name is empty.')
MSG_PT_0008 = _(
    'Some of fields in "workflow template name" '
    'field(s) don\'t exist.'
)
MSG_PT_0009 = _(
    'If a "workflow template name" contains only an output fields,'
    'at least one of the fields must be required.'
)
MSG_PT_0010 = _('Kickoff form data not provided.')
MSG_PT_0011 = _('Kickoff form \'id\' has incorrect value.')
MSG_PT_0012 = _('Kickoff \'id\' not provided.')
MSG_PT_0013 = _('Tasks data not provided, one task required.')
MSG_PT_0014 = _('Incorrect tasks order.')
MSG_PT_0015 = lambda count: format_lazy(
    _(
        'The free plan allows {count} enabled templates.'
        'Please upgrade your plan or disable some unwanted templates.'
    ),
    count=count
)
MSG_PT_0016 = _('You should set \'template owners\' value.')
MSG_PT_0017 = _(
    'You have to upgrade your plan to the Premium, '
    'if you want to change template ownership.'
)
MSG_PT_0018 = _('You cannot remove yourself from template owners.')
MSG_PT_0019 = _('One or more template owners are incorrect.')
MSG_PT_0020 = _(
    'Public success url is available only for customers on Premium plan.'
)
MSG_PT_0021 = _('"Public success url" is an invalid format.')
MSG_PT_0022 = _(
    "Filters 'with_tasks_in_progress' and 'workflows_status'"
    "cannot be used at the same time."
)
MSG_PT_0023 = _('Permission denied. You are not a template owner.')
MSG_PT_0024 = _(
    'Inconsistent permission! Should use only for "workflow detail" actions.'
)
MSG_PT_0025 = _('The limit for creating a public id has been exceeded.')
MSG_PT_0026 = _('The limit for creating a embed id has been exceeded.')
# Translators: Template due date editor
MSG_PT_0027 = _('Expected date field api_name.')
# Translators: Template due date editor
MSG_PT_0028 = _(
    'Only the date fields from previous steps can be used in a due date.'
)
# Translators: Template due date editor
MSG_PT_0029 = _('Expected task api_name.')
MSG_PT_0030 = _('Only previous steps are allowed for a rule.')
MSG_PT_0031 = _('Only previous and current steps are allowed for a rule.')
# Translators: Template performer editor
MSG_PT_0032 = _(
    'You should set the user id for performer with the type "user".'
)
MSG_PT_0033 = _('Performer "id" should be a number.')
MSG_PT_0034 = _('One or more performers are incorrect.')
MSG_PT_0035 = _(
    'A template with "Workflow starter" in the list of performers '
    'can not be shared. Please replace the "workflow starter" '
    'with another team member.'
)
MSG_PT_0036 = _(
    'You should set the field api_name for performer with the type "field".'
)
MSG_PT_0037 = lambda number: format_lazy(
    _(
        'Step {number}: Some fields in the step description '
        'don\'t exist or are used before assignment.'
    ),
    number=number
)
MSG_PT_0038 = lambda number: format_lazy(
    _(
        'Step {number}: Field in step name '
        'don\'t exist or are used before assignment.'
    ),
    number=number
)
MSG_PT_0039 = lambda number: format_lazy(
    _(
        'Step {number}: If a step name contains only an output fields, '
        'at least one of the fields must be required.'
    ),
    number=number
)
MSG_PT_0040 = _('Checklist items not exists or invalid.')
MSG_PT_0041 = lambda old_api_name, new_api_name: format_lazy(
    _(
        'You can\'t change api_name of an existing object.'
        ' Old value: "{old}", new value: "{new}".'
    ),
    old=old_api_name,
    new=new_api_name
)
MSG_PT_0042 = _(
    'Workflow conditions are available only for customers on Premium plan.'
)
# Translators: Add user field value in condition with not allowed user
MSG_PT_0043 = lambda task, user_id: format_lazy(
    _(
        'Task "{task}": user id "{user_id}" doesn\'t exist '
        'or can\'t be used in this condition.'
    ),
    task=task,
    user_id=user_id
)
# Translators: Field type inconsistent with condition operator
MSG_PT_0044 = lambda task, operator, field_type: format_lazy(
    _(
        'Task "{task}": operator "{operator}" can\'t be use '
        'with type of field "{field_type}".'
    ),
    task=task,
    operator=operator,
    field_type=field_type,
)
MSG_PT_0045 = lambda task, selection_api_name: format_lazy(
    _(
        'Task "{task}": selection "{selection_api_name}" '
        'doesn\'t exist or can\'t be used in this condition.'
    ),
    selection_api_name=selection_api_name,
    task=task
)
# Translators: Condition operator not provided
MSG_PT_0046 = lambda task, operator: format_lazy(
    _('Task "{task}": operator "{operator}" should have some value.'),
    operator=operator,
    task=task
)
MSG_PT_0047 = lambda step_name, api_name: format_lazy(
    _(
        'Step "{step_name}": checklist contains a non-unique api_name '
        '"{api_name}". '
        'Recreate checklist or change it\'s api_name.'
    ),
    step_name=step_name,
    api_name=api_name,
)
MSG_PT_0048 = lambda step_name, api_name: format_lazy(
    _(
        'Step "{step_name}": checklist item contains a non-unique api_name '
        '"{api_name}". '
        'Recreate checklist item or change it\'s api_name.'
    ),
    step_name=step_name,
    api_name=api_name,
)
MSG_PT_0049 = lambda step_name, api_name: format_lazy(
    _(
        'Step "{step_name}": condition contains a non-unique api_name '
        '"{api_name}". '
        'Recreate condition or change it\'s api_name.'
    ),
    step_name=step_name,
    api_name=api_name,
)
MSG_PT_0050 = lambda step_name, name, api_name: format_lazy(
    _(
        '{step_name}: output field "{name}" contains a non-unique '
        'api_name "{api_name}". '
        'Change the api_name or recreate output field.'
    ),
    step_name=step_name,
    api_name=api_name,
    name=name,
)
MSG_PT_0051 = lambda step_name, api_name: format_lazy(
    _(
        'Step "{step_name}": condition predicate contains a non-unique '
        'api_name "{api_name}". '
        'Recreate condition predicate or change it\'s api_name.'
    ),
    step_name=step_name,
    api_name=api_name,
)
MSG_PT_0052 = lambda step_name, api_name: format_lazy(
    _(
        'Step "{step_name}": due date contains a non-unique '
        'api_name "{api_name}". '
        'Recreate due date or change it\'s api_name.'
    ),
    step_name=step_name,
    api_name=api_name,
)
MSG_PT_0053 = lambda step_name, api_name: format_lazy(
    _(
        'Step "{step_name}": condition rule contains a non-unique api_name '
        '"{api_name}". '
        'Recreate condition rule or change it\'s api_name.'
    ),
    step_name=step_name,
    api_name=api_name,
)
MSG_PT_0054 = lambda step_name, name, api_name, value: format_lazy(
    _(
        '{step_name}: output field "{name}" option "{value}" '
        'contains a non-unique api_name "{api_name}". '
        'Change the api_name or recreate option.'
    ),
    step_name=step_name,
    name=name,
    api_name=api_name,
    value=value
)
MSG_PT_0055 = lambda step_name, api_name: format_lazy(
    _(
        'Step "{step_name}": contains a non-unique api_name "{api_name}". '
        'Recreate step or change it\'s api_name.'
    ),
    step_name=step_name,
    api_name=api_name,
)
MSG_PT_0056 = lambda step_name, api_name: format_lazy(
    _(
        'Step "{step_name}": performer contains a non-unique api_name '
        '"{api_name}". '
        'Recreate performer or change it\'s api_name.'
    ),
    step_name=step_name,
    api_name=api_name
)
