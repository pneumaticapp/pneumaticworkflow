from pneumatic_backend.consumers import PneumaticBaseConsumer


class NotificationsConsumer(PneumaticBaseConsumer):

    classname = 'notifications'


class NewTaskConsumer(PneumaticBaseConsumer):

    classname = 'new_task'


class RemovedTaskConsumer(PneumaticBaseConsumer):

    classname = 'removed_task'


class WorkflowEventConsumer(PneumaticBaseConsumer):

    classname = 'workflow_event'
