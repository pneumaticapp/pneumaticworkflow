from os import environ as env
from typing_extensions import Literal


class NotificationMethod:

    new_task = 'new_task'
    new_task_websocket = 'new_task_websocket'
    returned_task = 'returned_task'
    removed_task = 'removed_task'
    overdue_task = 'overdue_task'
    complete_task = 'complete_task'
    mention = 'mention'
    comment = 'comment'
    delay_workflow = 'delay_workflow'
    guest_new_task = 'guest_new_task'
    resume_workflow = 'resume_workflow'
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

    LITERALS = Literal[
        new_task,
        new_task_websocket,
        returned_task,
        removed_task,
        overdue_task,
        mention,
        comment,
        delay_workflow,
        guest_new_task,
        resume_workflow,
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
    ]


class EmailTemplate:

    RESET_PASSWORD = 'reset_password'
    USER_DEACTIVATED = 'user_deactivated'
    NEW_TASK = 'new_task'
    COMPLETE_TASK = 'complete_task'
    TASK_RETURNED = 'task_returned'
    ACCOUNT_VERIFICATION = 'account_verification'
    WORKFLOWS_DIGEST = 'digest'
    TASKS_DIGEST = 'tasks_digest'
    USER_TRANSFER = 'user_transfer'
    UNREAD_NOTIFICATIONS = 'unread_notifications'
    GUEST_NEW_TASK = 'guest_new_task'
    OVERDUE_TASK = 'overdue_task'
    MENTION = 'mention'

    LITERALS = Literal[
        RESET_PASSWORD,
        USER_DEACTIVATED,
        NEW_TASK,
        COMPLETE_TASK,
        TASK_RETURNED,
        ACCOUNT_VERIFICATION,
        WORKFLOWS_DIGEST,
        TASKS_DIGEST,
        USER_TRANSFER,
        UNREAD_NOTIFICATIONS,
        GUEST_NEW_TASK,
        OVERDUE_TASK,
        MENTION,
    ]


cio_template_ids = {
    EmailTemplate.RESET_PASSWORD: env.get('CIO_TEMPLATE__RESET_PASSWORD'),
    EmailTemplate.USER_DEACTIVATED: env.get('CIO_TEMPLATE__USER_DEACTIVATED'),
    EmailTemplate.NEW_TASK: env.get('CIO_TEMPLATE__NEW_TASK'),
    EmailTemplate.TASK_RETURNED: env.get('CIO_TEMPLATE__TASK_RETURNED'),
    EmailTemplate.ACCOUNT_VERIFICATION: env.get(
        'CIO_TEMPLATE__ACCOUNT_VERIFICATION',
    ),
    EmailTemplate.WORKFLOWS_DIGEST: env.get('CIO_TEMPLATE__WORKFLOWS_DIGEST'),
    EmailTemplate.TASKS_DIGEST: env.get('CIO_TEMPLATE__TASKS_DIGEST'),
    EmailTemplate.USER_TRANSFER: env.get('CIO_TEMPLATE__USER_TRANSFER'),
    EmailTemplate.UNREAD_NOTIFICATIONS: env.get(
        'CIO_TEMPLATE__UNREAD_NOTIFICATIONS',
    ),
    EmailTemplate.GUEST_NEW_TASK: env.get('CIO_TEMPLATE__GUEST_NEW_TASK'),
    EmailTemplate.OVERDUE_TASK: env.get('CIO_TEMPLATE__OVERDUE_TASK'),
    EmailTemplate.MENTION: env.get('CIO_TEMPLATE__MENTION'),
}
