from pneumatic_backend.accounts.models import Account, User
from pneumatic_backend.processes.models import (
    Task,
    TaskTemplate,
)


class PayWallValidator:

    @staticmethod
    def is_active_templates_limit_reached(account: Account):
        if account.active_templates >= account.max_active_templates:
            return account.is_free
        return False


def user_is_performer(user: User):

    """ Returns True if tasks or tasktemplates where found
        where user is the last performer """

    if Task.objects.on_performer(
        user.id
    ).exclude_directly_deleted().raw_performers_count(
        1
    ).incompleted().exists():
        return True
    if TaskTemplate.objects.active_templates().on_raw_performer(
        user.id
    ).raw_performers_count(1).exists():
        return True
    return False
