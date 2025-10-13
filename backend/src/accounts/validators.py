from src.accounts.models import User
from src.processes.enums import TaskStatus
from src.processes.models.workflows.task import Task
from src.processes.models.templates.task import TaskTemplate


def user_is_last_performer(user: User):

    """ Returns True if tasks or tasktemplates where found
        where user is the last performer """

    if (
        Task.objects.on_performer(user.id)
        .exclude_directly_deleted()
        .raw_performers_count(1)
        .filter(
            status__in=(
                TaskStatus.PENDING,
                TaskStatus.DELAYED,
                TaskStatus.ACTIVE,
            ),
        ).exists()
    ):
        return True
    if (
        TaskTemplate.objects
            .filter(template__is_active=True)
            .on_raw_performer(user.id)
            .raw_performers_count(1)
            .exists()
    ):
        return True
    return False
