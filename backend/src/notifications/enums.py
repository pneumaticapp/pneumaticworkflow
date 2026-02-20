from os import environ as env

from typing_extensions import Literal


class NotificationMethod:

    new_task = 'new_task'
    new_task_websocket = 'new_task_websocket'
    returned_task = 'returned_task'
    removed_task = 'removed_task'
    task_reminder = 'task_reminder'
    overdue_task = 'overdue_task'
    complete_task = 'complete_task'
    mention = 'mention'
    comment = 'comment'
    delay_workflow = 'delay_workflow'
    guest_new_task = 'guest_new_task'
    resume_workflow = 'resume_workflow'
    complete_workflow = 'complete_workflow'
    unread_notifications = 'unread_notifications'
    due_date_changed = 'due_date_changed'
    system = 'system'
    urgent = 'urgent'
    not_urgent = 'not_urgent'
    workflow_event = 'workflow_event'
    reaction = 'reaction'
    reset_password = 'reset_password'
    group_created = 'group_created'
    group_updated = 'group_updated'
    group_deleted = 'group_deleted'
    user_created = 'user_created'
    user_updated = 'user_updated'
    user_deleted = 'user_deleted'
    workflows_digest = 'workflows_digest'
    tasks_digest = 'tasks_digest'
    user_deactivated = 'user_deactivated'
    user_transfer = 'user_transfer'
    verification = 'verification'
    invite = 'invite'

    LITERALS = Literal[
        new_task,
        new_task_websocket,
        returned_task,
        removed_task,
        task_reminder,
        overdue_task,
        complete_task,
        mention,
        comment,
        delay_workflow,
        guest_new_task,
        resume_workflow,
        complete_workflow,
        unread_notifications,
        due_date_changed,
        system,
        urgent,
        not_urgent,
        workflow_event,
        reaction,
        reset_password,
        group_created,
        group_updated,
        group_deleted,
        user_created,
        user_updated,
        user_deleted,
        workflows_digest,
        tasks_digest,
        user_deactivated,
        user_transfer,
        verification,
        invite,
    ]


class EmailProvider:

    CUSTOMERIO = 'customerio'
    SMTP = 'smtp'

    LITERALS = Literal[
        CUSTOMERIO,
        SMTP,
    ]


class EmailType:

    RESET_PASSWORD = 'reset_password'
    USER_DEACTIVATED = 'user_deactivated'
    NEW_TASK = 'new_task'
    TASK_RETURNED = 'task_returned'
    TASK_REMINDER = 'task_reminder'
    ACCOUNT_VERIFICATION = 'account_verification'
    WORKFLOWS_DIGEST = 'digest'
    TASKS_DIGEST = 'tasks_digest'
    USER_TRANSFER = 'user_transfer'
    UNREAD_NOTIFICATIONS = 'unread_notifications'
    GUEST_NEW_TASK = 'guest_new_task'
    OVERDUE_TASK = 'overdue_task'
    MENTION = 'mention'
    INVITE = 'invite'
    COMPLETE_WORKFLOW = 'complete_workflow'

    LITERALS = Literal[
        RESET_PASSWORD,
        USER_DEACTIVATED,
        NEW_TASK,
        TASK_RETURNED,
        TASK_REMINDER,
        ACCOUNT_VERIFICATION,
        WORKFLOWS_DIGEST,
        TASKS_DIGEST,
        USER_TRANSFER,
        UNREAD_NOTIFICATIONS,
        GUEST_NEW_TASK,
        OVERDUE_TASK,
        MENTION,
        INVITE,
        COMPLETE_WORKFLOW,
    ]

    CHOICES = [
        (RESET_PASSWORD, 'Reset Password'),
        (USER_DEACTIVATED, 'User Deactivated'),
        (NEW_TASK, 'New Task'),
        (TASK_RETURNED, 'Task Returned'),
        (TASK_REMINDER, 'Task Remainder'),
        (ACCOUNT_VERIFICATION, 'Account Verification'),
        (WORKFLOWS_DIGEST, 'Workflows Digest'),
        (TASKS_DIGEST, 'Tasks Digest'),
        (USER_TRANSFER, 'User Transfer'),
        (UNREAD_NOTIFICATIONS, 'Unread Notifications'),
        (GUEST_NEW_TASK, 'Guest New Task'),
        (OVERDUE_TASK, 'Overdue Task'),
        (MENTION, 'Mention'),
        (INVITE, 'Invite'),
        (COMPLETE_WORKFLOW, 'Complete Workflow'),
    ]


cio_template_ids = {
    EmailType.RESET_PASSWORD: env.get('CIO_TEMPLATE__RESET_PASSWORD'),
    EmailType.USER_DEACTIVATED: env.get('CIO_TEMPLATE__USER_DEACTIVATED'),
    EmailType.NEW_TASK: env.get('CIO_TEMPLATE__NEW_TASK'),
    EmailType.TASK_RETURNED: env.get('CIO_TEMPLATE__TASK_RETURNED'),
    EmailType.TASK_REMINDER: env.get('CIO_TEMPLATE__TASK_REMINDER'),
    EmailType.ACCOUNT_VERIFICATION: env.get(
        'CIO_TEMPLATE__ACCOUNT_VERIFICATION',
    ),
    EmailType.WORKFLOWS_DIGEST: env.get('CIO_TEMPLATE__WORKFLOWS_DIGEST'),
    EmailType.TASKS_DIGEST: env.get('CIO_TEMPLATE__TASKS_DIGEST'),
    EmailType.USER_TRANSFER: env.get('CIO_TEMPLATE__USER_TRANSFER'),
    EmailType.UNREAD_NOTIFICATIONS: env.get(
        'CIO_TEMPLATE__UNREAD_NOTIFICATIONS',
    ),
    EmailType.GUEST_NEW_TASK: env.get('CIO_TEMPLATE__GUEST_NEW_TASK'),
    EmailType.OVERDUE_TASK: env.get('CIO_TEMPLATE__OVERDUE_TASK'),
    EmailType.MENTION: env.get('CIO_TEMPLATE__MENTION'),
    EmailType.COMPLETE_WORKFLOW: env.get('CIO_TEMPLATE__COMPLETE_WORKFLOW'),
}

email_titles = {
    NotificationMethod.new_task: "You've been assigned a task",
    NotificationMethod.returned_task: 'A task was returned to you',
    NotificationMethod.overdue_task: 'You Have an Overdue Task',
    NotificationMethod.guest_new_task: "Has Invited You to the",
    NotificationMethod.unread_notifications: 'You have unread notifications',
    NotificationMethod.reset_password: 'Forgot Your Password?',
    NotificationMethod.mention: 'You have been mentioned',
    NotificationMethod.workflows_digest: 'Workflows Weekly Digest',
    NotificationMethod.tasks_digest: 'Tasks Weekly Digest',
    NotificationMethod.user_deactivated: (
        'Your Pneumatic profile was deactivated.'
    ),
    NotificationMethod.user_transfer: 'invited you to join team on Pneumatic!',
    NotificationMethod.verification: 'Welcome to Pneumatic!',
    NotificationMethod.invite: (
        "✅ You've been invited to join your team in Pneumatic"
    ),
    NotificationMethod.complete_workflow: 'Workflow completed',
    NotificationMethod.task_reminder: (
        'Reminder: you have unfinished tasks in Pneumatic'
    ),
}
