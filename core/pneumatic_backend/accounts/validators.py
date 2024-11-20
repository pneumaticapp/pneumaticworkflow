from pneumatic_backend.accounts.models import User
from pneumatic_backend.processes.models import (
    Task,
    TaskTemplate,
)


def user_is_performer(user: User):

    """ Returns True if tasks or tasktemplates where found
        where user is the last performer """

    if Task.objects.on_performer(
        user.id
    ).exclude_directly_deleted().raw_performers_count(
        1
    ).incompleted().exists():
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
