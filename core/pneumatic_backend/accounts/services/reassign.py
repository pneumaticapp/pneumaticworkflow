from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.accounts.queries import (
    DeleteUserFromConditionsQuery,
    DeleteUserFromRawPerformerQuery,
    DeleteUserFromRawPerformerTemplateQuery,
    DeleteUserFromTaskPerformerQuery,
    DeleteUserFromTemplateConditionsQuery,
    DeleteUserFromTemplateOwnerQuery,
    DeleteUserFromWorkflowMembersQuery
)
from pneumatic_backend.accounts.services import exceptions
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.processes.enums import FieldType
from pneumatic_backend.processes.models import (
    Predicate,
    PredicateTemplate,
    RawPerformer,
    RawPerformerTemplate,
    TaskPerformer,
    Template,
    Workflow
)
from pneumatic_backend.processes.tasks.tasks import complete_tasks

UserModel = get_user_model()


class ReassignService:

    """ Reassigns entities from one user to another user
        within the same account """

    def __init__(
        self,
        old_user: UserModel,
        new_user: Optional[UserModel] = None,
        is_superuser: bool = False,
        auth_type: AuthTokenType.LITERALS = AuthTokenType.USER,
    ):
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        self.old_user = old_user
        self.account = old_user.account
        self.new_user = new_user if new_user else self._get_user_to_reassign()
        if not self.new_user:
            raise exceptions.ReassignUserDoesNotExist()
        if self.new_user.account_id != self.old_user.account_id:
            raise exceptions.UserNotFoundException()

    def _get_user_to_reassign(self) -> Optional[UserModel]:

        """ Returns the user from the account who will inherit all
            active tasks from the transferred user """

        user_to_reassign = UserModel.objects.filter(
            account=self.account,
        ).exclude(
            id=self.old_user.id
        ).exclude(
            status=UserStatus.INACTIVE
        ).order_by(
            '-is_account_owner',
            '-is_admin',
            'id'
        ).first()
        if user_to_reassign and self.old_user.is_account_owner:
            user_to_reassign.is_account_owner = True
            user_to_reassign.save()
        return user_to_reassign

    def _reassign_in_raw_performer_templates(self):

        delete_query = DeleteUserFromRawPerformerTemplateQuery(
            user_to_delete=self.old_user.id,
            user_to_substitution=self.new_user.id,
        )
        RawSqlExecutor.execute(*delete_query.get_sql())
        RawPerformerTemplate.objects.filter(
            user_id=self.old_user.id,
            account=self.account
        ).update(user_id=self.new_user.id)

    def _reassign_in_raw_performers(self):

        delete_query = DeleteUserFromRawPerformerQuery(
            user_to_delete=self.old_user.id,
            user_to_substitution=self.new_user.id,
        )
        RawSqlExecutor.execute(*delete_query.get_sql())
        RawPerformer.objects.filter(
            user_id=self.old_user.id,
            account=self.account
        ).update(user_id=self.new_user.id)

    def _reassign_in_performers(self):

        delete_query = DeleteUserFromTaskPerformerQuery(
            user_to_delete=self.old_user.id,
            user_to_substitution=self.new_user.id,
        )
        RawSqlExecutor.execute(*delete_query.get_sql())
        TaskPerformer.objects.filter(
            user_id=self.old_user.id,
            task__account=self.account,
        ).update(user_id=self.new_user.id)

    def _reassign_in_template_owners(self):
        delete_query = DeleteUserFromTemplateOwnerQuery(
            user_to_delete=self.old_user.id,
            user_to_substitution=self.new_user.id,
        )
        RawSqlExecutor.execute(*delete_query.get_sql())
        Template.template_owners.through.objects.filter(
            user=self.old_user,
            template__account=self.account,
        ).update(user=self.new_user)

    def _reassign_in_workflow_members(self):

        delete_query = DeleteUserFromWorkflowMembersQuery(
            user_to_delete=self.old_user.id,
            user_to_substitution=self.new_user.id,
        )
        RawSqlExecutor.execute(*delete_query.get_sql())

        Workflow.members.through.objects.filter(
            user_id=self.old_user.id,
            workflow__account=self.account,
        ).update(user_id=self.new_user.id)

    def _reassign_in_template_conditions(self):

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
        if self.new_user:
            with transaction.atomic():
                self._reassign_in_raw_performer_templates()
                self._reassign_in_template_owners()
                self._reassign_in_raw_performers()
                self._reassign_in_performers()
                self._reassign_in_workflow_members()
                self._reassign_in_template_conditions()
                self._reassign_in_conditions()
                complete_tasks.delay(
                    user_id=self.new_user.id,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type
                )
