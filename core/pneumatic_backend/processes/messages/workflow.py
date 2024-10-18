from django.utils.translation import ugettext_lazy as _
from django.utils.text import format_lazy

MSG_PW_0001 = _(
    'Saving files is not available, file storage does\'t '
    'configured. Contact support.'
)
MSG_PW_0003 = _('Only "snoozed" workflows can be resumed.')
MSG_PW_0004 = _('You need to resume the workflow before completing the task.')
MSG_PW_0005 = _('Task is skipped and cannot be completed.')  # TODO Not used
MSG_PW_0006 = _(
    'Check off all the items in the checklist before completing the task.'
)
MSG_PW_0007 = _('You have already completed this task.')
MSG_PW_0008 = _('You have already completed this workflow.')
MSG_PW_0009 = _('You are not allowed to finish this workflow.')
MSG_PW_0010 = _('Task already completed.')  # TODO Not used
MSG_PW_0011 = _('You don\'t have permission for complete the task.')
MSG_PW_0012 = _('The task cannot be returned.')
# Translators: Task return api
MSG_PW_0013 = _('The supplied task number is incorrect.')
# Translators: Create / delete task performer action
MSG_PW_0014 = _('The user with the specified credentials not found.')
# Translators: Create / delete task guests action
MSG_PW_0015 = _(
    'You have reached the limit of the number of guest performers.'
)
# Translators: Create / delete task performer action
MSG_PW_0016 = _('Deleting the last performer is not allowed.')
MSG_PW_0017 = _('Completed workflow cannot be changed.')
# Translators: Create / delete task performer or fill checklist actions
MSG_PW_0018 = _('Available for current task only.')
MSG_PW_0019 = _(
    'You need to be added to the task as a performer '
    'to check off this checklist item.'
)
MSG_PW_0020 = _(
    'You need to resume the workflow before check off this checklist item.'
)
MSG_PW_0021 = _('Permission denied.')
# Translators: Workflows / Templates / Highlights filter by template steps
MSG_PW_0022 = _(
    "Filters 'with_tasks_in_progress' and 'is_running_workflows' "
    "cannot be used at the same time."
)
# Translators:
MSG_PW_0023 = _('Please fill in the required fields.')
MSG_PW_0024 = lambda arg: format_lazy(
    _('Wrong argument format: "{arg}".'),
    arg=arg
)
# Translators: String field validation
MSG_PW_0025 = _('Value should be a string.')
# Translators: String field length validation
MSG_PW_0026 = lambda limit: format_lazy(
    _('The value of the field exceeds the limit of {limit} characters.'),
    limit=limit
)
# Translators: Dropdown / radio / checkbox selections validation
MSG_PW_0028 = _('Selection with the given id does not exist.')
# Translators: Checkbox selections validation
MSG_PW_0029 = _('Checkbox value should be a list.')
# Translators: Checkbox selections validation
MSG_PW_0030 = _('Checkbox value contains invalid selections.')
# Translators: Checkbox selections validation
MSG_PW_0031 = _('Checkbox value contains non existent selections.')
# Translators: Date field validation
MSG_PW_0032 = _('Date value should be a string. Format: MM/DD/YYYY.')
# Translators: Date field validation
MSG_PW_0033 = _('Invalid date format. Should be MM/DD/YYYY.')
# Translators: URL field validation
MSG_PW_0034 = _('URL field value should be a string.')
# Translators: URL field validation
MSG_PW_0035 = _('The URL is invalid.')
# Translators: File field validation
MSG_PW_0036 = _('File value should be a list of integers.')
# Translators: File field validation
MSG_PW_0037 = _('Attachment not found.')
# Translators: User field validation
MSG_PW_0038 = _('The value must be the ID of an existing account user.')
MSG_PW_0039 = _('Account user with given id does not exist.')
MSG_PW_0040 = _('Save attachments failed. Service unavailable.')
MSG_PW_0041 = _('Blob object doesn\'t exist.')
MSG_PW_0042 = _('AI service is temporarily unavailable.')
# Translators: AI template generation
MSG_PW_0043 = _('Could not create template from given description.')
MSG_PW_0044 = _(
    'You\'ve reached the limit for free AI powered template generation '
    'requests, sign up for a premium account to get unlimited access.'
)
# Translators: Bad AI prompt
MSG_PW_0045 = _(
    'Something seems to be wrong with your input, '
    'please try re phrasing your process name and description.'
)
# Translators: Need configure AI from admin
MSG_PW_0046 = _(
    'You need to set up a system prompt for template generation. '
    'Contact administrator.'
)
# Translators: Comment create validation
MSG_PW_0047 = _('You need to specify the comment text or attachments.')
MSG_PW_0048 = _('You cannot write a comment on a completed workflow.')
MSG_PW_0049 = _('You cannot change a deleted comment.')
MSG_PW_0050 = lambda bytes_limit: format_lazy(
    _('The size limit for attachments is {mb} Mb.'),
    mb=bytes_limit/(1024*1024)
)
# Translators: Set task / workflow due date
MSG_PW_0051 = _('Due date should be greater than current.')
# Translators: Starting workflow. Validate user field
MSG_PW_0052 = _('Field with type "User" should be required.')
# Translators: Starting workflow. Validate user field
MSG_PW_0053 = _(
    'The default value for a field with type "User" should be an integer.'
)
MSG_PW_0054 = _('The user for a field with type "User" does not exist.')
# Translators: Starting workflow. Validate dropdown / radio / checkbox
MSG_PW_0055 = _('Field selections not provided.')
MSG_PW_0056 = _('Checklist element length limit exceeded. Limit 2000 chars.')
# Translators: Task list filter by performer
MSG_PW_0057 = _('Filter by "assigned_to" is only allowed for the admin.')
MSG_PW_0058 = _('Checklist item with given id not found.')
# Translators: System template creation validation
MSG_PW_0059 = _('You can\'t pass the `id` field.')
# Translators: System template creation validation
MSG_PW_0060 = _('Radio and checkbox fields must have non-empty selections.')
# Translators: System template kickoff creation validation
MSG_PW_0061 = _('Value should be a object.')
# Translators: System template fields creation validation
MSG_PW_0062 = _('Value should be a list.')
# Translators: System template tasks creation validation
MSG_PW_0063 = _('Incorrect order of tasks.')
# Translators: System template tasks description creation validation
MSG_PW_0064 = lambda tasks_numbers: format_lazy(
    _(
        'Some fields in tasks descriptions don\'t exist or are used '
        'before assignment. Tasks number(s): {tasks_numbers}.'
    ),
    tasks_numbers=(
        tasks_numbers if isinstance(tasks_numbers, int)
        else ', '.join(str(e) for e in tasks_numbers)
    )
)
# Translators: System template creation validation
MSG_PW_0065 = _('You must pass an "api_name" into every field you declare.')
MSG_PW_0066 = _(
    'Your template is disabled. Please, enable this template before running.'
)
MSG_PW_0067 = _(
    'Only "in-progress" workflows can be filtered by current performer.'
)
MSG_PW_0068 = _('You can\'t snooze the first task in a workflow.')
MSG_PW_0069 = _('You should provide "due_date" or "due_date_tsp" field.')
MSG_PW_0070 = _(
    'The task can\'t be completed until all the embedded workflows are done.'
)
MSG_PW_0071 = _(
    'The task can\'t be returned until all the embedded workflows are done.'
)
MSG_PW_0072 = _('Snoozed workflow cannot be changed.')
MSG_PW_0073 = _('Completed task cannot be changed.')
MSG_PW_0074 = _(
    'Creation of a embedded workflows is available only '
    'to the current task of workflow.'
)
MSG_PW_0075 = _(
    'You need to be added to the task as a performer '
    'in order to create a embedded workflows.'
)
