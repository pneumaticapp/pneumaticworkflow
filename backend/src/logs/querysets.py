from src.generics.querysets import (
    AccountBaseQuerySet,
)
from src.logs.enums import (
    AccountEventStatus,
    AccountEventType,
)


class AccountEventQuerySet(AccountBaseQuerySet):

    def type_system(self):
        return self.filter(event_type=AccountEventType.SYSTEM)

    def success(self):
        return self.filter(status=AccountEventStatus.SUCCESS)
