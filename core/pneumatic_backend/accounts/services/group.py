from typing import List, Optional
from pneumatic_backend.generics.base.service import BaseModelService
from pneumatic_backend.accounts.models import UserGroup
from pneumatic_backend.processes.models import TemplateOwner
from pneumatic_backend.processes.enums import (
    OwnerType
)
from pneumatic_backend.processes.tasks.update_workflow import (
    update_workflow_owners,
)


class UserGroupService(BaseModelService):

    def _get_template_ids(self):
        return list(TemplateOwner.objects.filter(
            type=OwnerType.GROUP,
            group=self.instance
        ).values_list('template_id', flat=True))

    def _create_instance(
        self,
        name: str,
        photo: Optional[str] = None,
        users: Optional[List[int]] = None,
        **kwargs
    ):
        self.instance = UserGroup.objects.create(
            name=name,
            photo=photo,
            account=self.account,
        )
        return self.instance

    def _create_related(
        self,
        users: Optional[List[int]] = None,
        **kwargs
    ):
        if users:
            self.instance.users.set(users)

    def partial_update(
        self,
        force_save=False,
        **update_kwargs
    ):
        users = update_kwargs.pop('users', None)
        if isinstance(users, list):
            template_ids = self._get_template_ids()
            if template_ids:
                update_workflow_owners.delay(template_ids)
            if users:
                self.instance.users.set(users)
            else:
                self.instance.users.clear()
        return super().partial_update(
            **update_kwargs,
            force_save=force_save
        )

    def delete(self):
        template_ids = self._get_template_ids()
        self.instance.delete()
        if template_ids:
            update_workflow_owners.delay(template_ids)
