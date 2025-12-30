from typing_extensions import Literal


class SourceType:
    """
    File source types.
    Defines which entity the file is attached to.
    """
    ACCOUNT = 'Account'
    WORKFLOW = 'Workflow'
    TASK = 'Task'
    TEMPLATE = 'Template'

    CHOICES = (
        (ACCOUNT, 'Account'),
        (WORKFLOW, 'Workflow'),
        (TASK, 'Task'),
        (TEMPLATE, 'Template'),
    )
    LITERALS = Literal['Account', 'Workflow', 'Task', 'Template']


class AccessType:
    """
    File access types.
    PUBLIC - accessible to everyone
    ACCOUNT - accessible to all account users
    RESTRICTED - accessible only to specified users/groups
    """
    PUBLIC = 'public'
    ACCOUNT = 'account'
    RESTRICTED = 'restricted'

    CHOICES = (
        (PUBLIC, 'Public'),
        (ACCOUNT, 'Account'),
        (RESTRICTED, 'Restricted'),
    )
    LITERALS = Literal['public', 'account', 'restricted']
