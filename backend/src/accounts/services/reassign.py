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
from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission
from src.processes.enums import (
    OwnerType,
    PerformerType,
    PredicateType,
    TaskStatus,
    WorkflowPermission,
)
from src.processes.models.templates.conditions import PredicateTemplate
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.models.templates.template import Template
from src.processes.models.workflows.conditions import Predicate
from src.processes.models.workflows.raw_performer import RawPerformer
from src.processes.models.workflows.task import TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.tasks.tasks import complete_tasks
from src.processes.tasks.update_workflow import (
    sync_workflow_performer_permissions,
    update_workflow_owners,
)

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
                permission__codename=WorkflowPermission.VIEW,
            ).values_list('object_pk', flat=True)
            workflow_ids.update(int(pk) for pk in uop_pks)

        if self.old_group:
            uop_group_pks = UserObjectPermission.objects.filter(
                source_type=PermissionSource.PERFORMER_GROUP,
                source_id=self.old_group.id,
                content_type=ct,
                permission__codename=WorkflowPermission.VIEW,
            ).values_list('object_pk', flat=True)
            workflow_ids.update(int(pk) for pk in uop_group_pks)

        return list(workflow_ids)

    def _reassign_in_workflow_members(self):
        """Update Guardian view_workflow permissions.

        PERFORMER / PERFORMER_GROUP rows are realigned synchronously
        via ``sync_performer_sources()`` so the old user/group loses
        view access before the request returns (no async privilege
        window). Attachment ACL is refreshed asynchronously.

        Legacy WORKFLOW_VIEWER rows have no source of truth to
        rebuild from:
        - user→user: transfer old_user → new_user
        - user→group: revoke on old_user (cannot move to a group)
        MENTION rows are left untouched (comment still mentions user).
        """
        affected_workflow_ids = self._affected_workflow_ids()

        if self.old_user and self.new_user:
            self._transfer_workflow_viewer_rows()
        elif self.old_user and self.new_group:
            self._revoke_workflow_viewer_rows()

        if not affected_workflow_ids:
            return

        live_wf_ids = list(
            Workflow.objects.filter(
                id__in=affected_workflow_ids,
                is_deleted=False,
            ).values_list('id', flat=True),
        )
        for wf_id in live_wf_ids:
            transaction.on_commit(
                lambda _id=wf_id: (
                    sync_workflow_performer_permissions.delay(_id)
                ),
            )

    def _workflow_viewer_base_qs(self):
        ct = ContentType.objects.get_for_model(Workflow)
        return UserObjectPermission.objects.filter(
            content_type=ct,
            permission__codename=WorkflowPermission.VIEW,
            source_type=PermissionSource.WORKFLOW_VIEWER,
        )

    def _transfer_workflow_viewer_rows(self):
        """Reassign legacy WORKFLOW_VIEWER rows old_user -> new_user.

        Uses UPDATE (not delete + insert) to preserve source_id
        and avoid unique-constraint conflicts when new_user already
        has a WORKFLOW_VIEWER row for the same workflow.

        Conflicting rows (new_user already viewer of the same
        workflow) are removed for old_user first, so the UPDATE
        cannot violate the (user, permission, ct, object_pk,
        source_type, source_id) uniqueness constraint.
        """
        base_qs = self._workflow_viewer_base_qs()
        conflicting_object_pks = list(
            base_qs.filter(user=self.new_user).values_list(
                'object_pk', flat=True,
            ),
        )
        if conflicting_object_pks:
            base_qs.filter(
                user=self.old_user,
                object_pk__in=conflicting_object_pks,
            ).delete()
        base_qs.filter(user=self.old_user).update(user=self.new_user)

    def _revoke_workflow_viewer_rows(self):
        """Drop legacy WORKFLOW_VIEWER rows for old_user.

        Used on user→group reassign: viewer source is user-only and
        cannot be transferred to a group. Leaving rows would keep
        view access after the user's process roles were reassigned.
        Does not touch MENTION / TEMPLATE_OWNER / PERFORMER* rows.
        """
        self._workflow_viewer_base_qs().filter(
            user=self.old_user,
        ).delete()

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
        """Rebuild Guardian change_workflow permissions synchronously.

        TemplateOwner rows are already updated in this transaction,
        so ``set_view_and_change`` sees the new owners immediately —
        no async privilege window for change_workflow.
        """
        if not affected_template_ids:
            return
        update_workflow_owners(template_ids=affected_template_ids)

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
