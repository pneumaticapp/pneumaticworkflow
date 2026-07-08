from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from src.accounts.models import UserGroup
from src.accounts.queries import (
    DeleteGroupFromConditionsQuery,
    DeleteGroupFromRawPerformerQuery,
    DeleteGroupFromRawPerformerTemplateQuery,
    DeleteGroupFromTaskPerformerQuery,
    DeleteGroupFromTemplateConditionsQuery,
    DeleteGroupFromTemplateOwnerQuery,
    DeleteGroupUserFromConditionsQuery,
    DeleteGroupUserFromRawPerformerQuery,
    DeleteGroupUserFromRawPerformerTemplateQuery,
    DeleteGroupUserFromTaskPerformerQuery,
    DeleteGroupUserFromTemplateConditionsQuery,
    DeleteGroupUserFromTemplateOwnerQuery,
    DeleteUserFromConditionsQuery,
    DeleteUserFromRawPerformerQuery,
    DeleteUserFromRawPerformerTemplateQuery,
    DeleteUserFromTaskPerformerQuery,
    DeleteUserFromTemplateConditionsQuery,
    DeleteUserFromTemplateOwnerQuery,
    DeleteUserGroupFromConditionsQuery,
    DeleteUserGroupFromRawPerformerQuery,
    DeleteUserGroupFromRawPerformerTemplateQuery,
    DeleteUserGroupFromTaskPerformerQuery,
    DeleteUserGroupFromTemplateConditionsQuery,
    DeleteUserGroupFromTemplateOwnerQuery,
)
from src.accounts.services import exceptions
from src.accounts.services.vacation import (
    VacationDelegationService,
)
from src.authentication.enums import AuthTokenType
from src.executor import RawSqlExecutor
from src.permissions.models import UserObjectPermission
from src.processes.enums import (
    OwnerType,
    PerformerType,
    PredicateType,
    TaskStatus,
)
from src.processes.models.templates.conditions import PredicateTemplate
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.models.templates.template import Template
from src.processes.models.workflows.conditions import Predicate
from src.processes.models.workflows.raw_performer import RawPerformer
from src.processes.models.workflows.task import TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.tasks.update_workflow import update_workflow_owners
from src.processes.tasks.tasks import complete_tasks
from src.processes.services.workflow_permissions import CODENAME_VIEW

UserModel = get_user_model()


class ReassignService:
    """
    Reassigns entities from one performer (user or group) to another
    performer (user or group) within the same account
    """

    def __init__(
        self,
        old_user: Optional[UserModel] = None,
        new_user: Optional[UserModel] = None,
        old_group: Optional[UserGroup] = None,
        new_group: Optional[UserGroup] = None,
        is_superuser: bool = False,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER,
    ):
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        self.old_user = old_user
        self.new_user = new_user
        self.old_group = old_group
        self.new_group = new_group

        if not (old_user or old_group):
            raise exceptions.ReassignOldUserDoesNotExist

        if not (new_user or new_group):
            raise exceptions.ReassignNewUserDoesNotExist

        if old_user and new_user and old_user == new_user:
            raise exceptions.ReassignUserSameUser

        if old_group and new_group and old_group == new_group:
            raise exceptions.ReassignUserSameGroup

        if old_user:
            self.account = old_user.account
        else:
            self.account = old_group.account

    def _reassign_in_raw_performer_templates(self):
        if self.old_group:
            if self.new_group:
                delete_query = DeleteGroupFromRawPerformerTemplateQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                RawPerformerTemplate.objects.filter(
                    group_id=self.old_group.id,
                    account=self.account,
                ).update(
                    group_id=self.new_group.id,
                )
            elif self.new_user:
                delete_query = DeleteGroupUserFromRawPerformerTemplateQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                RawPerformerTemplate.objects.filter(
                    group_id=self.old_group.id,
                    account=self.account,
                ).update(
                    type=PerformerType.USER,
                    user_id=self.new_user.id,
                    group_id=None,
                )
        elif self.old_user:
            if self.new_group:
                delete_query = DeleteUserGroupFromRawPerformerTemplateQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                RawPerformerTemplate.objects.filter(
                    user_id=self.old_user.id,
                    account=self.account,
                ).update(
                    type=PerformerType.GROUP,
                    group_id=self.new_group.id,
                    user_id=None,
                )
            elif self.new_user:
                delete_query = DeleteUserFromRawPerformerTemplateQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                RawPerformerTemplate.objects.filter(
                    user_id=self.old_user.id,
                    account=self.account,
                ).update(user_id=self.new_user.id)

    def _reassign_in_raw_performers(self):
        if self.old_group:
            if self.new_group:
                delete_query = DeleteGroupFromRawPerformerQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                RawPerformer.objects.filter(
                    group_id=self.old_group.id,
                    account=self.account,
                ).update(
                    group_id=self.new_group.id,
                )
            elif self.new_user:
                delete_query = DeleteGroupUserFromRawPerformerQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                RawPerformer.objects.filter(
                    group_id=self.old_group.id,
                    account=self.account,
                ).update(
                    type=PerformerType.USER,
                    user_id=self.new_user.id,
                    group_id=None,
                )
        elif self.old_user:
            if self.new_group:
                delete_query = DeleteUserGroupFromRawPerformerQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                RawPerformer.objects.filter(
                    user_id=self.old_user.id,
                    account=self.account,
                ).update(
                    type=PerformerType.GROUP,
                    group_id=self.new_group.id,
                    user_id=None,
                )
            elif self.new_user:
                delete_query = DeleteUserFromRawPerformerQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                RawPerformer.objects.filter(
                    user_id=self.old_user.id,
                    account=self.account,
                ).update(user_id=self.new_user.id)

    def _reassign_in_performers(self):
        if self.old_group:
            if self.new_group:
                delete_query = DeleteGroupFromTaskPerformerQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                TaskPerformer.objects.filter(
                    group_id=self.old_group.id,
                    task__account=self.account,
                ).exclude(
                    task__status=TaskStatus.COMPLETED,
                ).update(
                    group_id=self.new_group.id,
                )
            elif self.new_user:
                delete_query = DeleteGroupUserFromTaskPerformerQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                TaskPerformer.objects.filter(
                    group_id=self.old_group.id,
                    task__account=self.account,
                ).exclude(
                    task__status=TaskStatus.COMPLETED,
                ).update(
                    type=PerformerType.USER,
                    user_id=self.new_user.id,
                    group_id=None,
                )
        elif self.old_user:
            if self.new_group:
                delete_query = DeleteUserGroupFromTaskPerformerQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                TaskPerformer.objects.filter(
                    user_id=self.old_user.id,
                    task__account=self.account,
                ).exclude(
                    task__status=TaskStatus.COMPLETED,
                ).update(
                    type=PerformerType.GROUP,
                    group_id=self.new_group.id,
                    user_id=None,
                )
            elif self.new_user:
                delete_query = DeleteUserFromTaskPerformerQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                TaskPerformer.objects.filter(
                    user_id=self.old_user.id,
                    task__account=self.account,
                ).exclude(
                    task__status=TaskStatus.COMPLETED,
                ).update(user_id=self.new_user.id)

    def _reassign_in_template_owners(self):
        if self.old_group:
            if self.new_group:
                delete_query = DeleteGroupFromTemplateOwnerQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                TemplateOwner.objects.filter(
                    group_id=self.old_group.id,
                    template__account=self.account,
                ).update(
                    group_id=self.new_group.id,
                )
            elif self.new_user:
                delete_query = DeleteGroupUserFromTemplateOwnerQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                TemplateOwner.objects.filter(
                    group_id=self.old_group.id,
                    template__account=self.account,
                ).update(
                    type=PerformerType.USER,
                    user_id=self.new_user.id,
                    group_id=None,
                )
        elif self.old_user:
            if self.new_group:
                delete_query = DeleteUserGroupFromTemplateOwnerQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                TemplateOwner.objects.filter(
                    user=self.old_user,
                    template__account=self.account,
                ).update(
                    type=PerformerType.GROUP,
                    group_id=self.new_group.id,
                    user_id=None,
                )
            elif self.new_user:
                delete_query = DeleteUserFromTemplateOwnerQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                TemplateOwner.objects.filter(
                    user=self.old_user,
                    template__account=self.account,
                ).update(user=self.new_user)

    def _affected_workflow_ids(self) -> list:
        """Find all workflows where the old user/group had view permissions."""
        ct = ContentType.objects.get_for_model(Workflow)
        workflow_ids = set()

        if self.old_user:
            uop_pks = UserObjectPermission.objects.filter(
                user=self.old_user,
                content_type=ct,
                permission__codename=CODENAME_VIEW,
            ).values_list('object_pk', flat=True)
            workflow_ids.update(int(pk) for pk in uop_pks)

        if self.old_group:
            from src.permissions.models import (  # noqa: PLC0415
                GroupObjectPermission,
            )
            gop_pks = GroupObjectPermission.objects.filter(
                group=self.old_group,
                content_type=ct,
                permission__codename=CODENAME_VIEW,
            ).values_list('object_pk', flat=True)
            workflow_ids.update(int(pk) for pk in gop_pks)

        return list(workflow_ids)

    def _reassign_in_workflow_members(self):
        """Update Guardian view_workflow permissions.

        Rebuilds view permissions for all workflows
        affected by this reassignment.
        """
        affected_workflow_ids = self._affected_workflow_ids()

        # Delete old permissions synchronously
        ct = ContentType.objects.get_for_model(Workflow)
        if self.old_user:
            UserObjectPermission.objects.filter(
                user=self.old_user,
                content_type=ct,
                permission__codename=CODENAME_VIEW,
            ).delete()
        if self.old_group:
            from src.permissions.models import (  # noqa: PLC0415
                GroupObjectPermission,
            )
            GroupObjectPermission.objects.filter(
                group=self.old_group,
                content_type=ct,
                permission__codename=CODENAME_VIEW,
            ).delete()

        # Dispatch async task to recalculate viewers
        if affected_workflow_ids:
            from src.processes.tasks.update_workflow import (  # noqa: PLC0415
                update_workflow_viewers,
            )
            transaction.on_commit(
                lambda: update_workflow_viewers.delay(affected_workflow_ids),
            )

    def _affected_template_ids(self):
        affected_template_ids = []

        if self.old_user and not self.old_group:
            affected_template_ids = list(
                Template.objects.filter(
                    owners__user=self.old_user,
                    owners__type=OwnerType.USER,
                    account=self.account,
                ).distinct().values_list('id', flat=True),
            )
        elif self.old_group and not self.old_user:
            affected_template_ids = list(
                Template.objects.filter(
                    owners__group=self.old_group,
                    owners__type=OwnerType.GROUP,
                    account=self.account,
                ).distinct().values_list('id', flat=True),
            )
        return affected_template_ids

    def _reassign_in_workflow_owners(self, affected_template_ids: list):
        """Rebuild Guardian change_workflow permissions via celery task.

        Uses on_commit to ensure the task runs after the enclosing
        transaction commits, preventing stale reads.
        """
        if not affected_template_ids:
            return
        transaction.on_commit(
            lambda: update_workflow_owners.delay(
                template_ids=affected_template_ids,
            ),
        )

    def _reassign_in_template_conditions(self):
        if self.old_group:
            if self.new_group:
                delete_query = DeleteGroupFromTemplateConditionsQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                PredicateTemplate.objects.filter(
                    field_type=PredicateType.GROUP,
                    group=self.old_group,
                ).update(
                    group=self.new_group,
                )
            elif self.new_user:
                delete_query = DeleteGroupUserFromTemplateConditionsQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                PredicateTemplate.objects.filter(
                    field_type=PredicateType.GROUP,
                    group=self.old_group,
                ).update(
                    field_type=PredicateType.USER,
                    user=self.new_user,
                    group=None,
                )
        elif self.old_user:
            if self.new_group:
                delete_query = DeleteUserGroupFromTemplateConditionsQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                PredicateTemplate.objects.filter(
                    field_type=PredicateType.USER,
                    user=self.old_user,
                ).update(
                    field_type=PredicateType.GROUP,
                    group=self.new_group,
                    user=None,
                )
            elif self.new_user:
                delete_query = DeleteUserFromTemplateConditionsQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                PredicateTemplate.objects.filter(
                    field_type=PredicateType.USER,
                    user=self.old_user,
                ).update(user=self.new_user)

    def _reassign_in_conditions(self):
        if self.old_group:
            if self.new_group:
                delete_query = DeleteGroupFromConditionsQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                Predicate.objects.filter(
                    field_type=PredicateType.GROUP,
                    group=self.old_group,
                ).update(
                    group=self.new_group,
                )
            elif self.new_user:
                delete_query = DeleteGroupUserFromConditionsQuery(
                    delete_id=self.old_group.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                Predicate.objects.filter(
                    field_type=PredicateType.GROUP,
                    group=self.old_group,
                ).update(
                    field_type=PredicateType.USER,
                    user=self.new_user,
                    group=None,
                )
        elif self.old_user:
            if self.new_group:
                delete_query = DeleteUserGroupFromConditionsQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_group.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                Predicate.objects.filter(
                    field_type=PredicateType.USER,
                    user=self.old_user,
                ).update(
                    field_type=PredicateType.GROUP,
                    group=self.new_group,
                    user=None,
                )
            elif self.new_user:
                delete_query = DeleteUserFromConditionsQuery(
                    delete_id=self.old_user.id,
                    substitution_id=self.new_user.id,
                )
                RawSqlExecutor.execute(*delete_query.get_sql())
                Predicate.objects.filter(
                    field_type=PredicateType.USER,
                    user=self.old_user,
                ).update(user=self.new_user)

    def _cleanup_personal_groups(self):
        """Remove old_user from personal (vacation) groups.

        If the group becomes empty after removal, auto-deactivate
        vacation for the group owner.
        """
        if not self.old_user:
            return
        VacationDelegationService.clear_substitute_groups(self.old_user)

    def reassign_everywhere(self):
        with transaction.atomic():
            self._reassign_in_raw_performer_templates()
            self._reassign_in_raw_performers()
            self._reassign_in_performers()
            affected_template_ids = self._affected_template_ids()
            self._reassign_in_template_owners()
            self._reassign_in_workflow_owners(affected_template_ids)
            self._reassign_in_workflow_members()
            self._reassign_in_template_conditions()
            self._reassign_in_conditions()
            self._cleanup_personal_groups()
            if self.new_user:
                user_id = self.new_user.id
            elif self.new_group and self.new_group.users.exists():
                user_id = self.new_group.users.first().id
            else:
                user_id = self.account.get_owner().id
            transaction.on_commit(
                lambda: complete_tasks.delay(
                    user_id=user_id,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                ),
            )
