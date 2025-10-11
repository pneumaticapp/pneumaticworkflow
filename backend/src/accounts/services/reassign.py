from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from src.accounts.models import UserGroup
from src.accounts.queries import (
    DeleteUserFromConditionsQuery,
    DeleteUserFromRawPerformerQuery,
    DeleteUserFromRawPerformerTemplateQuery,
    DeleteUserFromTemplateConditionsQuery,
    DeleteUserFromWorkflowMembersQuery,
    DeleteUserGroupFromRawPerformerQuery,
    DeleteGroupFromRawPerformerQuery,
    DeleteGroupUserFromRawPerformerQuery,
    DeleteGroupFromRawPerformerTemplateQuery,
    DeleteGroupUserFromRawPerformerTemplateQuery,
    DeleteUserGroupFromRawPerformerTemplateQuery,
    DeleteGroupFromTaskPerformerQuery,
    DeleteGroupUserFromTaskPerformerQuery,
    DeleteUserGroupFromTaskPerformerQuery,
    DeleteUserFromTaskPerformerQuery,
    DeleteGroupFromTemplateOwnerQuery,
    DeleteGroupUserFromTemplateOwnerQuery,
    DeleteUserGroupFromTemplateOwnerQuery,
    DeleteUserFromTemplateOwnerQuery,
)
from src.accounts.services import exceptions
from src.authentication.enums import AuthTokenType
from src.executor import RawSqlExecutor
from src.processes.enums import (
    FieldType,
    PerformerType,
    OwnerType,
    TaskStatus,
)
from src.processes.models import (
    Predicate,
    PredicateTemplate,
    RawPerformer,
    RawPerformerTemplate,
    TaskPerformer,
    TemplateOwner,
    Workflow,
    Template,
)
from src.processes.queries import UpdateWorkflowOwnersQuery
from src.processes.tasks.tasks import complete_tasks

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
            raise exceptions.ReassignOldUserDoesNotExist()

        if not (new_user or new_group):
            raise exceptions.ReassignNewUserDoesNotExist()

        if old_user and new_user and old_user == new_user:
            raise exceptions.ReassignUserSameUser()

        if old_group and new_group and old_group == new_group:
            raise exceptions.ReassignUserSameGroup()

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

    def _reassign_in_workflow_members(self):
        if self.old_user and self.new_user:
            delete_query = DeleteUserFromWorkflowMembersQuery(
                user_to_delete=self.old_user.id,
                user_to_substitution=self.new_user.id,
            )
            RawSqlExecutor.execute(*delete_query.get_sql())

            Workflow.members.through.objects.filter(
                user_id=self.old_user.id,
                workflow__account=self.account,
            ).update(user_id=self.new_user.id)

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
        if not affected_template_ids:
            return

        with transaction.atomic():
            Workflow.owners.through.objects.filter(
                workflow__template_id__in=affected_template_ids,
                workflow__account=self.account,
            ).delete()

            for template_id in affected_template_ids:
                query = UpdateWorkflowOwnersQuery(
                    template_id=template_id,
                )
                RawSqlExecutor.execute(*query.insert_sql())

    def _reassign_in_template_conditions(self):
        if self.old_user and self.new_user:
            delete_query = DeleteUserFromTemplateConditionsQuery(
                user_to_delete=str(self.old_user.id),
                user_to_substitution=str(self.new_user.id),
            )
            RawSqlExecutor.execute(*delete_query.get_sql())
            PredicateTemplate.objects.filter(
                field_type=FieldType.USER,
                value=self.old_user.id,
            ).update(value=self.new_user.id)

    def _reassign_in_conditions(self):
        if self.old_user and self.new_user:
            delete_query = DeleteUserFromConditionsQuery(
                user_to_delete=str(self.old_user.id),
                user_to_substitution=str(self.new_user.id),
            )
            RawSqlExecutor.execute(*delete_query.get_sql())
            Predicate.objects.filter(
                field_type=FieldType.USER,
                value=self.old_user.id,
            ).update(value=self.new_user.id)

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
            if self.new_user:
                user_id = self.new_user.id
            elif self.new_group and self.new_group.users.exists():
                user_id = self.new_group.users.first().id
            else:
                user_id = self.account.get_owner().id
            complete_tasks.delay(
                user_id=user_id,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
