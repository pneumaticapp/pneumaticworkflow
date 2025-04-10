from typing import List, Optional
from pneumatic_backend.generics.base.service import BaseModelService
from pneumatic_backend.accounts.models import UserGroup
from pneumatic_backend.processes.models import TemplateOwner, TaskPerformer
from pneumatic_backend.processes.enums import (
    OwnerType,
    PerformerType
)
from pneumatic_backend.processes.tasks.update_workflow import (
    update_workflow_owners,
)


class UserGroupService(BaseModelService):

    def _get_template_ids(self):
        template_owner_ids = TemplateOwner.objects.filter(
            type=OwnerType.GROUP,
            group=self.instance,
            is_deleted=False
        ).values_list('template_id', flat=True)
        task_performer_template_ids = TaskPerformer.objects.filter(
            type=PerformerType.GROUP,
            group=self.instance,
            is_deleted=False
        ).exclude_directly_deleted().select_related(
            'task__workflow'
        ).values_list(
            'task__workflow__template_id', flat=True
        ).distinct()
        template_ids = (
            list(set(template_owner_ids) | set(task_performer_template_ids))
        )
        return template_ids

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
            if users:
                self.instance.users.set(users)
            else:
                self.instance.users.clear()
            template_ids = self._get_template_ids()
            if template_ids:
                update_workflow_owners.delay(template_ids)
        return super().partial_update(
            **update_kwargs,
            force_save=force_save
        )

    def delete(self):
        template_ids = self._get_template_ids()
        self.instance.delete()
        if template_ids:
            update_workflow_owners.delay(template_ids)
