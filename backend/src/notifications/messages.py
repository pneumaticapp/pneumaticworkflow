from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

MSG_NF_0001 = lambda reaction: _('Reacted {reaction} to your comment').format(
    reaction=reaction,
)
MSG_NF_0002 = _('You have a new task')
MSG_NF_0003 = _('Task was returned')
MSG_NF_0004 = _('Your task is overdue')
MSG_NF_0005 = _('You have been mentioned')
MSG_NF_0006 = _('You have a new comment')
MSG_NF_0007 = _('Workflow was snoozed')
MSG_NF_0008 = _('Workflow was resumed')
MSG_NF_0009 = _('Task due date was changed')
MSG_NF_0011 = lambda workflow_name, task_name: format_lazy(
    _('Workflow: {workflow_name}\nTask: {task_name}'),
    workflow_name=workflow_name,
    task_name=task_name,
)
MSG_NF_0012 = _('Task was completed')
MSG_NF_0013 = _('You have unread notifications')
MSG_NF_0014 = _('Password reset')
MSG_NF_0015 = _('Profile was deactivated')
MSG_NF_0016 = _('Profile was transfer')
MSG_NF_0017 = _('Profile was verify')
MSG_NF_0018 = _('Send workflows digest')
MSG_NF_0019 = _('Send tasks digest')
