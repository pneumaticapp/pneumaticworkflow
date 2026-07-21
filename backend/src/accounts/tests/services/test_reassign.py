from unittest.mock import call

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from src.accounts.queries import DeleteUserFromTaskPerformerQuery
from src.accounts.services import exceptions
from src.accounts.services.reassign import ReassignService
from src.executor import RawSqlExecutor
from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission
from src.processes.enums import (
    ConditionAction,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
    WorkflowPermission,
)
from src.processes.models.templates.conditions import (
    ConditionTemplate,
    PredicateTemplate,
    RuleTemplate,
)
from src.processes.models.workflows.conditions import (
    Condition,
    Predicate,
    Rule,
)
from src.processes.models.workflows.task import TaskPerformer
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.workflow_permissions import (
    WorkflowPermissionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


class TestReassignService:

    def test_init__to_the_same_user__raise_exception(self):

        # arrange
        user = create_test_owner()

        # act
        with pytest.raises(exceptions.ReassignUserSameUser):
            ReassignService(old_user=user, new_user=user)

    def test_init__to_the_same_group__raise_exception(self):

        # arrange
        user = create_test_owner()
        group = create_test_group(user.account)

        # act
        with pytest.raises(exceptions.ReassignUserSameGroup):
            ReassignService(old_group=group, new_group=group)

    def test_init__only_old_group__raise_exception(self):

        # arrange
        user = create_test_owner()
        group = create_test_group(user.account)

        # act
        with pytest.raises(exceptions.ReassignNewUserDoesNotExist):
            ReassignService(old_group=group)

    def test_init__only_old_user__raise_exception(self):

        # arrange
        user = create_test_owner()

        # act
        with pytest.raises(exceptions.ReassignNewUserDoesNotExist):
            ReassignService(old_user=user)

    def test_init__only_new_group__raise_exception(self):

        # arrange
        user = create_test_owner()
        group = create_test_group(user.account)

        # act
        with pytest.raises(exceptions.ReassignOldUserDoesNotExist):
            ReassignService(new_group=group)

    def test_init__only_new_user__raise_exception(self):

        # arrange
        user = create_test_owner()

        # act
        with pytest.raises(exceptions.ReassignOldUserDoesNotExist):
            ReassignService(new_user=user)

    def test_reassign_everywhere__call_services_new_user__ok(self, mocker):

        # arrange
        account = create_test_account(
            name='transfer from',
        )
        new_user = create_test_user(
            account=account,
            email='test@test.test',
            is_account_owner=False,
        )
        deleted_user = create_test_user(
            account=account,
            email='deleted@test.test',
            is_account_owner=True,
        )
        reassign_in_raw_performer_templates_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performer_templates',
        )
        reassign_in_template_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_owners',
        )
        reassign_in_raw_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performers',
        )
        reassign_in_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_performers',
        )
        affected_template_ids_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_affected_template_ids',
        )
        affected_template_ids_mock.return_value = [1, 2]
        reassign_in_workflow_members_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_members',
        )
        reassign_in_workflow_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_owners',
        )
        reassign_in_template_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_conditions',
        )
        reassign_in_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_conditions',
        )
        complete_tasks_mock = mocker.patch(
            'src.accounts.services.reassign.complete_tasks',
        )
        on_commit_mock = mocker.patch(
            'src.accounts.services.reassign.transaction.on_commit',
        )
        service = ReassignService(
            old_user=deleted_user,
            new_user=new_user,
        )

        # act
        service.reassign_everywhere()

        # assert
        reassign_in_raw_performer_templates_mock.assert_called_once()
        reassign_in_template_owners_mock.assert_called_once()
        reassign_in_raw_performers_mock.assert_called_once()
        reassign_in_performers_mock.assert_called_once()
        affected_template_ids_mock.assert_called_once()
        reassign_in_workflow_members_mock.assert_called_once()
        reassign_in_workflow_owners_mock.assert_called_once_with([1, 2])
        reassign_in_template_conditions_mock.assert_called_once()
        reassign_in_conditions_mock.assert_called_once()
        on_commit_mock.call_args_list[-1][0][0]()
        complete_tasks_mock.delay.assert_called_once_with(
            user_id=new_user.id,
            is_superuser=False,
            auth_type='User',
        )

    def test_reassign_everywhere__call_services_new_group__ok(self, mocker):
        # arrange
        account = create_test_account(
            name='transfer from',
        )
        new_user = create_test_user(
            account=account,
            email='test@test.test',
            is_account_owner=False,
        )
        group = create_test_group(account, users=[new_user])
        deleted_user = create_test_user(
            account=account,
            email='deleted@test.test',
            is_account_owner=True,
        )
        reassign_in_raw_performer_templates_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performer_templates',
        )
        reassign_in_template_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_owners',
        )
        reassign_in_raw_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performers',
        )
        reassign_in_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_performers',
        )
        affected_template_ids_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_affected_template_ids',
        )
        affected_template_ids_mock.return_value = [1, 2]
        reassign_in_workflow_members_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_members',
        )
        reassign_in_workflow_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_owners',
        )
        reassign_in_template_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_conditions',
        )
        reassign_in_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_conditions',
        )
        complete_tasks_mock = mocker.patch(
            'src.accounts.services.reassign.complete_tasks',
        )
        on_commit_mock = mocker.patch(
            'src.accounts.services.reassign.transaction.on_commit',
        )
        service = ReassignService(
            old_user=deleted_user,
            new_group=group,
        )

        # act
        service.reassign_everywhere()

        # assert
        reassign_in_raw_performer_templates_mock.assert_called_once()
        reassign_in_template_owners_mock.assert_called_once()
        reassign_in_raw_performers_mock.assert_called_once()
        reassign_in_performers_mock.assert_called_once()
        affected_template_ids_mock.assert_called_once()
        reassign_in_workflow_members_mock.assert_called_once()
        reassign_in_workflow_owners_mock.assert_called_once_with([1, 2])
        reassign_in_template_conditions_mock.assert_called_once()
        reassign_in_conditions_mock.assert_called_once()
        on_commit_mock.call_args_list[-1][0][0]()
        complete_tasks_mock.delay.assert_called_once_with(
            user_id=new_user.id,
            is_superuser=False,
            auth_type='User',
        )

    def test_reassign_everywhere__call_services_new_group_users_null__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(
            name='transfer from',
        )
        new_user = create_test_user(
            account=account,
            email='test@test.test',
        )
        group = create_test_group(account)
        deleted_user = create_test_user(
            account=account,
            email='deleted@test.test',
            is_account_owner=True,
        )
        reassign_in_raw_performer_templates_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performer_templates',
        )
        reassign_in_template_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_owners',
        )
        reassign_in_raw_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performers',
        )
        reassign_in_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_performers',
        )
        affected_template_ids_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_affected_template_ids',
        )
        affected_template_ids_mock.return_value = [1, 2]
        reassign_in_workflow_members_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_members',
        )
        reassign_in_workflow_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_owners',
        )
        reassign_in_template_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_conditions',
        )
        reassign_in_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_conditions',
        )
        complete_tasks_mock = mocker.patch(
            'src.accounts.services.reassign.complete_tasks',
        )
        on_commit_mock = mocker.patch(
            'src.accounts.services.reassign.transaction.on_commit',
        )
        service = ReassignService(
            old_user=deleted_user,
            new_group=group,
        )

        # act
        service.reassign_everywhere()

        # assert
        reassign_in_raw_performer_templates_mock.assert_called_once()
        reassign_in_template_owners_mock.assert_called_once()
        reassign_in_raw_performers_mock.assert_called_once()
        reassign_in_performers_mock.assert_called_once()
        affected_template_ids_mock.assert_called_once()
        reassign_in_workflow_members_mock.assert_called_once()
        reassign_in_workflow_owners_mock.assert_called_once_with([1, 2])
        reassign_in_template_conditions_mock.assert_called_once()
        reassign_in_conditions_mock.assert_called_once()
        on_commit_mock.call_args_list[-1][0][0]()
        complete_tasks_mock.delay.assert_called_once_with(
            user_id=new_user.id,
            is_superuser=False,
            auth_type='User',
        )

    def test_reassign_in_raw_performer_templates__group_to_group__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_user(account=account)
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')
        template = create_test_template(user, tasks_count=1, is_active=True)
        task = template.tasks.get(number=1)
        task.raw_performers.all().delete()
        task.add_raw_performer(
            performer_type=PerformerType.GROUP,
            group=old_group,
        )

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupFromRawPerformerTemplateQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformerTemplate.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_raw_performer_templates()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_group.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            account=account,
        )
        update_mock.assert_called_once_with(group_id=new_group.id)

    def test_reassign_in_raw_performer_templates__group_to_user__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account=account, name='old_group')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupUserFromRawPerformerTemplateQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformerTemplate.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_raw_performer_templates()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_user.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            account=account,
        )
        update_mock.assert_called_once_with(
            type=PerformerType.USER,
            user_id=new_user.id,
            group_id=None,
        )

    def test_reassign_in_raw_performer_templates__user_to_group__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserGroupFromRawPerformerTemplateQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformerTemplate.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_raw_performer_templates()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_group.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            account=account,
        )
        update_mock.assert_called_once_with(
            type=PerformerType.GROUP,
            group_id=new_group.id,
            user_id=None,
        )

    def test_reassign_in_raw_performer_templates__user_to_user__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromRawPerformerTemplateQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformerTemplate.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_raw_performer_templates()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_user.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            account=account,
        )
        update_mock.assert_called_once_with(user_id=new_user.id)

    def test_reassign_in_raw_performers__group_to_group__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupFromRawPerformerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformer.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_raw_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_group.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            account=account,
        )
        update_mock.assert_called_once_with(group_id=new_group.id)

    def test_reassign_in_raw_performers__group_to_user__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_user(account=account)
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_user(account=account, email='new@example.com')
        template = create_test_template(user, tasks_count=1, is_active=True)
        workflow = create_test_workflow(template=template, user=user)
        task = workflow.tasks.get(number=1)
        task.raw_performers.all().delete()
        task.add_raw_performer(
            performer_type=PerformerType.GROUP,
            group_id=old_group.id,
        )

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupUserFromRawPerformerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformer.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_raw_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_user.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            account=account,
        )
        update_mock.assert_called_once_with(
            type=PerformerType.USER,
            user_id=new_user.id,
            group_id=None,
        )

    def test_reassign_in_raw_performers__user_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserGroupFromRawPerformerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformer.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_raw_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_group.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            account=account,
        )
        update_mock.assert_called_once_with(
            type=PerformerType.GROUP,
            group_id=new_group.id,
            user_id=None,
        )

    def test_reassign_in_raw_performers__user_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromRawPerformerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformer.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_raw_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_user.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            account=account,
        )
        update_mock.assert_called_once_with(user_id=new_user.id)

    def test_reassign_in_performers__group_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupFromTaskPerformerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TaskPerformer.objects.filter',
        )
        exclude_mock = filter_mock.return_value.exclude
        update_mock = exclude_mock.return_value.update

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_group.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            task__account=account,
        )
        exclude_mock.assert_called_once_with(
            task__status='completed',
        )
        update_mock.assert_called_once_with(
            group_id=new_group.id,
        )

    def test_reassign_in_performers__group_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupUserFromTaskPerformerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TaskPerformer.objects.filter',
        )
        exclude_mock = filter_mock.return_value.exclude
        update_mock = exclude_mock.return_value.update

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_user.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            task__account=account,
        )
        exclude_mock.assert_called_once_with(
            task__status='completed',
        )
        update_mock.assert_called_once_with(
            type=PerformerType.USER,
            user_id=new_user.id,
            group_id=None,
        )

    def test_reassign_in_performers__user_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserGroupFromTaskPerformerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TaskPerformer.objects.filter',
        )
        exclude_mock = filter_mock.return_value.exclude
        delete_mock = exclude_mock.return_value.delete
        update_mock = exclude_mock.return_value.update

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_group.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        assert filter_mock.call_args_list == [
            call(
                user_id=old_user.id,
                type=PerformerType.GROUP_USER,
                task__account=account,
            ),
            call(
                user_id=old_user.id,
                type=PerformerType.USER,
                task__account=account,
            ),
        ]
        assert exclude_mock.call_args_list == [
            call(task__status='completed'),
            call(task__status='completed'),
        ]
        delete_mock.assert_called_once_with()
        update_mock.assert_called_once_with(
            type=PerformerType.GROUP,
            group_id=new_group.id,
            user_id=None,
        )

    def test_reassign_in_performers__user_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromTaskPerformerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TaskPerformer.objects.filter',
        )
        exclude_mock = filter_mock.return_value.exclude
        delete_mock = exclude_mock.return_value.delete
        update_mock = exclude_mock.return_value.update

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_user.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        assert filter_mock.call_args_list == [
            call(
                user_id=old_user.id,
                type=PerformerType.GROUP_USER,
                task__account=account,
            ),
            call(
                user_id=old_user.id,
                type=PerformerType.USER,
                task__account=account,
            ),
        ]
        assert exclude_mock.call_args_list == [
            call(task__status='completed'),
            call(task__status='completed'),
        ]
        delete_mock.assert_called_once_with()
        update_mock.assert_called_once_with(
            user_id=new_user.id,
        )

    def test_reassign_in_template_owners__group_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupFromTemplateOwnerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TemplateOwner.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_template_owners()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_group.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            template__account=account,
        )
        update_mock.assert_called_once_with(
            group_id=new_group.id,
        )

    def test_reassign_in_template_owners__group_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupUserFromTemplateOwnerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TemplateOwner.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_template_owners()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_user.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            template__account=account,
        )
        update_mock.assert_called_once_with(
            type=PerformerType.USER,
            user_id=new_user.id,
            group_id=None,
        )

    def test_reassign_in_template_owners__user_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserGroupFromTemplateOwnerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TemplateOwner.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_template_owners()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_group.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            user=old_user,
            template__account=account,
        )
        update_mock.assert_called_once_with(
            type=PerformerType.GROUP,
            group_id=new_group.id,
            user_id=None,
        )

    def test_reassign_in_template_owners__user_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromTemplateOwnerQuery',
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'},
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute',
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TemplateOwner.objects.filter',
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_template_owners()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_user.id,
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'},
        )
        filter_mock.assert_called_once_with(
            user=old_user,
            template__account=account,
        )
        update_mock.assert_called_once_with(
            user=new_user,
        )

    def test_reassign_in_workflow_owners__with_template_ids__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_user(account=account)
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')
        template = create_test_template(user, tasks_count=1, is_active=True)

        update_task_mock = mocker.patch(
            'src.accounts.services.reassign.update_workflow_owners',
        )

        service = ReassignService(old_user=old_user, new_user=new_user)
        affected_template_ids = [template.id]

        # act
        service._reassign_in_workflow_owners(affected_template_ids)

        # assert
        update_task_mock.assert_called_once_with(
            template_ids=affected_template_ids,
        )

    def test_reassign_in_workflow_owners_with__empty_template_ids__ok(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        update_task_mock = mocker.patch(
            'src.accounts.services.reassign.update_workflow_owners',
        )

        service = ReassignService(old_user=old_user, new_user=new_user)
        affected_template_ids = []

        # act
        service._reassign_in_workflow_owners(affected_template_ids)

        # assert
        update_task_mock.assert_not_called()

    def test_affected_template_ids__with_old_user_ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')
        template1 = create_test_template(
            old_user,
            tasks_count=1,
            is_active=True,
        )

        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'Template.objects.filter',
        )
        distinct_mock = filter_mock.return_value.distinct
        values_list_mock = distinct_mock.return_value.values_list
        values_list_mock.return_value = [template1.id]

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        result = service._affected_template_ids()

        # assert
        assert result == [template1.id]
        filter_mock.assert_called_once_with(
            owners__user=old_user,
            owners__type=OwnerType.USER,
            account=account,
        )
        filter_mock.return_value.distinct.assert_called_once()
        values_list_mock.assert_called_once_with('id', flat=True)

    def test_affected_template_ids__with_old_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_user(account=account)
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_user(account=account, email='new@example.com')
        template1 = create_test_template(user, tasks_count=1, is_active=True)

        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'Template.objects.filter',
        )
        distinct_mock = filter_mock.return_value.distinct
        values_list_mock = distinct_mock.return_value.values_list
        values_list_mock.return_value = [template1.id]

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        result = service._affected_template_ids()

        # assert
        assert result == [template1.id]
        filter_mock.assert_called_once_with(
            owners__group=old_group,
            owners__type=OwnerType.GROUP,
            account=account,
        )
        filter_mock.return_value.distinct.assert_called_once()
        values_list_mock.assert_called_once_with('id', flat=True)

    def test_reassign_in_workflow_members__with_old_and_new_user__ok(
        self,
        mocker,
    ):
        """
        _reassign_in_workflow_members must sync performer sources
        synchronously (stale PERFORMER UOP cleared) and schedule
        attachment ACL sync via schedule_sync_*.
        """
        # arrange
        account = create_test_account(name='test_account')
        account_owner = create_test_user(account=account)
        old_user = create_test_user(
            account=account,
            email='old@example.com',
        )
        new_user = create_test_user(
            account=account,
            email='new@example.com',
        )
        workflow = create_test_workflow(
            user=account_owner,
            tasks_count=1,
        )

        WorkflowPermissionService(workflow).grant_view_bulk(
            user_ids=[old_user.id],
            source_type=PermissionSource.PERFORMER,
            source_id=0,
        )

        attach_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'schedule_sync_workflow_attachment_permissions',
        )

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_workflow_members(tp_workflow_ids=set())

        # assert
        assert not WorkflowPermissionService(workflow).has_view(
            user=old_user,
        )
        attach_mock.assert_called_once_with(workflow.id)

    def test_reassign_in_template_conditions__with_old_and_new_user__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_admin(account=account, email='old@example.com')
        new_user = create_test_admin(account=account, email='new@example.com')
        template = create_test_template(
            old_user,
            is_active=True,
            tasks_count=1,
        )
        task = template.tasks.get(number=1)
        condition_template = ConditionTemplate.objects.create(
            task=task,
            action=ConditionAction.SKIP_TASK,
            order=0,
            template=template,
        )
        rule_template = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_template,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user,
            template=template,
        )

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_template_conditions()

        # assert
        predicates = PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.USER,
            field='user_field',
            user=new_user,
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.group is None
        assert not PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user,
        ).exists()

    def test_reassign_in_template_conditions__with_old_and_new_group__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_admin(account=account, email='user@example.com')
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1,
        )
        task = template.tasks.get(number=1)
        condition_template = ConditionTemplate.objects.create(
            task=task,
            action=ConditionAction.SKIP_TASK,
            order=0,
            template=template,
        )
        rule_template = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_template,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group,
            template=template,
        )

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_template_conditions()

        # assert
        predicates = PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=new_group,
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.user is None
        assert not PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group,
        ).exists()

    def test_reassign_in_template_conditions__with_old_group_and_new_user__ok(
        self,
    ):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_admin(account=account, email='user@example.com')
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_admin(account=account, email='new@example.com')
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1,
        )
        task = template.tasks.get(number=1)
        condition_template = ConditionTemplate.objects.create(
            task=task,
            action=ConditionAction.SKIP_TASK,
            order=0,
            template=template,
        )
        rule_template = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_template,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group,
            template=template,
        )

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_template_conditions()

        # assert
        predicates = PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.USER,
            field='group_field',
            user=new_user,
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.group is None
        assert not PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group,
        ).exists()

    def test_reassign_in_template_conditions__with_old_user_and_new_group__ok(
        self,
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_admin(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')
        template = create_test_template(
            old_user,
            is_active=True,
            tasks_count=1,
        )
        task = template.tasks.get(number=1)
        condition_template = ConditionTemplate.objects.create(
            task=task,
            action=ConditionAction.SKIP_TASK,
            order=0,
            template=template,
        )
        rule_template = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_template,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user,
            template=template,
        )

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_template_conditions()

        # assert
        predicates = PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.GROUP,
            field='user_field',
            group=new_group,
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.user is None
        assert not PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user,
        ).exists()

    def test_reassign_in_conditions__with_old_and_new_user__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_admin(account=account, email='old@example.com')
        new_user = create_test_admin(account=account, email='new@example.com')
        workflow = create_test_workflow(user=old_user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        condition = Condition.objects.create(
            task=task,
            action=ConditionAction.SKIP_TASK,
            order=0,
        )
        rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=rule,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user,
        )

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_conditions()

        # assert
        predicates = Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.USER,
            field='user_field',
            user=new_user,
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.group is None
        assert not Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user,
        ).exists()

    def test_reassign_in_conditions__with_old_and_new_group__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_admin(account=account, email='user@example.com')
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        condition = Condition.objects.create(
            task=task,
            action=ConditionAction.SKIP_TASK,
            order=0,
        )
        rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=rule,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group,
        )

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_conditions()

        # assert
        predicates = Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=new_group,
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.user is None
        assert not Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group,
        ).exists()

    def test_reassign_in_conditions__with_old_group_and_new_user__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_admin(account=account, email='user@example.com')
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_admin(account=account, email='new@example.com')
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        condition = Condition.objects.create(
            task=task,
            action=ConditionAction.SKIP_TASK,
            order=0,
        )
        rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=rule,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group,
        )

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_conditions()

        # assert
        predicates = Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.USER,
            field='group_field',
            user=new_user,
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.group is None
        assert not Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group,
        ).exists()

    def test_reassign_in_conditions__with_old_user_and_new_group__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_admin(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')
        workflow = create_test_workflow(user=old_user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        condition = Condition.objects.create(
            task=task,
            action=ConditionAction.SKIP_TASK,
            order=0,
        )
        rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=rule,
            operator=PredicateOperator.EQUAL,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user,
        )

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_conditions()

        # assert
        predicates = Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.GROUP,
            field='user_field',
            group=new_group,
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.user is None
        assert not Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user,
        ).exists()

    def test_reassign_performers__user_group_user_to_user__ok(self):

        """
        old_user has USER + GROUP_USER → reassign to new_user
        → one USER on new_user, GROUP_USER of old_user is removed
        """

        # arrange
        account = create_test_account()
        old_user = create_test_owner(account=account)
        new_user = create_test_admin(account=account)
        workflow = create_test_workflow(user=old_user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=old_user.id,
            type=PerformerType.GROUP_USER,
            is_completed=True,
        )
        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_performers()

        # assert
        assert not TaskPerformer.objects.filter(
            task_id=task.id,
            user_id=old_user.id,
            type=PerformerType.GROUP_USER,
        ).exists()
        assert not TaskPerformer.objects.filter(
            task_id=task.id,
            user_id=old_user.id,
            type=PerformerType.USER,
        ).exists()
        assert (
            TaskPerformer.objects.filter(
                task_id=task.id,
                type=PerformerType.USER,
            ).count() == 1
        )
        user_performer = TaskPerformer.objects.get(
            task_id=task.id,
            type=PerformerType.USER,
        )
        assert user_performer.user_id == new_user.id

    def test_delete_user_task_perf_query__keeps_group_user__ok(self):

        """
        Conflicting USER on substitution + GROUP_USER on delete_id
        → DeleteUserFromTaskPerformerQuery deletes only USER conflict,
        GROUP_USER remains
        """

        # arrange
        account = create_test_account()
        old_user = create_test_owner(account=account)
        new_user = create_test_admin(account=account)
        workflow = create_test_workflow(user=old_user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            user_id=new_user.id,
            type=PerformerType.USER,
        )
        group_user_performer = TaskPerformer.objects.create(
            task_id=task.id,
            user_id=old_user.id,
            type=PerformerType.GROUP_USER,
            is_completed=True,
        )
        delete_query = DeleteUserFromTaskPerformerQuery(
            delete_id=old_user.id,
            substitution_id=new_user.id,
        )

        # act
        RawSqlExecutor.execute(*delete_query.get_sql())

        # assert
        assert not TaskPerformer.objects.filter(
            task_id=task.id,
            user_id=new_user.id,
            type=PerformerType.USER,
        ).exists()
        assert TaskPerformer.objects.filter(
            task_id=task.id,
            user_id=old_user.id,
            type=PerformerType.USER,
        ).exists()
        assert TaskPerformer.objects.filter(
            id=group_user_performer.id,
            type=PerformerType.GROUP_USER,
        ).exists()


def test_reassign_workflow_members__syncs_performer_sources__ok(mocker):
    """
    _reassign_in_workflow_members must sync performer sources
    synchronously (stale PERFORMER UOP cleared) and schedule
    attachment ACL sync via schedule_sync_*.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    workflow = create_test_workflow(
        user=account_owner, tasks_count=1,
    )

    WorkflowPermissionService(workflow).grant_view_bulk(
        user_ids=[old_user.id],
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
    assert WorkflowPermissionService(workflow).has_view(user=old_user)

    attach_mock = mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    assert not WorkflowPermissionService(workflow).has_view(
        user=old_user,
    )
    attach_mock.assert_called_once_with(workflow.id)


def test_reassign_workflow_members__transfers_workflow_viewer__ok(mocker):
    """
    Legacy WORKFLOW_VIEWER rows have no source of truth, so they must
    be transferred synchronously from old_user to new_user; otherwise
    sync_performer_sources() would preserve them on old_user and
    new_user would never receive them.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    WorkflowPermissionService(workflow).grant_view(
        user=old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    assert UserObjectPermission.objects.filter(
        user=new_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()


def test_reassign_workflow_members__viewer_conflict__resolved(mocker):
    """
    When new_user already has a WORKFLOW_VIEWER row for the same
    workflow, the old_user duplicate must be deleted (not left
    dangling) so the transfer UPDATE cannot violate the uniqueness
    constraint.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    perm_svc = WorkflowPermissionService(workflow)
    perm_svc.grant_view(
        user=old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    perm_svc.grant_view(
        user=new_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    new_user_rows = UserObjectPermission.objects.filter(
        user=new_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).count()
    old_user_rows = UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).count()
    assert new_user_rows == 1
    assert old_user_rows == 0


def test_reassign_workflow_members__old_group_only__no_viewer_transfer(
    mocker,
):
    """
    Group reassign (no old_user) must not attempt WORKFLOW_VIEWER
    transfer or revoke — that source_type is user-only, and there
    is no old_user to read from.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_group = create_test_group(account, name='old grp')
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=account_owner, tasks_count=1)

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    transfer_mock = mocker.patch.object(
        ReassignService, '_transfer_workflow_viewer_rows',
    )
    revoke_mock = mocker.patch.object(
        ReassignService, '_revoke_workflow_viewer_rows',
    )

    service = ReassignService(old_group=old_group, new_group=new_group)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    transfer_mock.assert_not_called()
    revoke_mock.assert_not_called()
    assert workflow.id is not None


def test_reassign_workflow_members__user_to_group__revokes_viewer__ok(
    mocker,
):
    """
    user→group: legacy WORKFLOW_VIEWER cannot move to a group and
    must be revoked from old_user so view access is not retained
    after process roles were reassigned.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    WorkflowPermissionService(workflow).grant_view(
        user=old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert not WorkflowPermissionService(workflow).has_view(
        user=old_user,
    )


def test_reassign_workflow_members__user_to_group__calls_revoke_not_transfer(
    mocker,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_group = create_test_group(account, name='new grp')
    create_test_workflow(user=account_owner, tasks_count=1)

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    transfer_mock = mocker.patch.object(
        ReassignService, '_transfer_workflow_viewer_rows',
    )
    revoke_mock = mocker.patch.object(
        ReassignService, '_revoke_workflow_viewer_rows',
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    transfer_mock.assert_not_called()
    revoke_mock.assert_called_once_with()


def test_reassign_workflow_members__user_to_group__preserves_mention__ok(
    mocker,
):
    """MENTION is independent of reassign — comment still mentions user."""

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    comment_id = 9001
    perm_svc = WorkflowPermissionService(workflow)
    perm_svc.grant_view(
        user=old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    perm_svc.grant_view(
        user=old_user,
        source_type=PermissionSource.MENTION,
        source_id=comment_id,
    )

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.MENTION,
        source_id=comment_id,
    ).exists()
    assert WorkflowPermissionService(workflow).has_view(user=old_user)


def test_reassign_workflow_members__user_to_user__preserves_mention__ok(
    mocker,
):
    """MENTION stays on old_user after user→user reassign.

    Comment text still mentions the original user; view from MENTION
    is independent of performer/viewer transfer.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old_m@test.test',
    )
    new_user = create_test_admin(
        account=account, email='new_m@test.test',
    )
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    comment_id = 9002
    WorkflowPermissionService(workflow).grant_view(
        user=old_user,
        source_type=PermissionSource.MENTION,
        source_id=comment_id,
    )
    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    assert UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.MENTION,
        source_id=comment_id,
    ).exists()
    assert not UserObjectPermission.objects.filter(
        user=new_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.MENTION,
        source_id=comment_id,
    ).exists()
    assert WorkflowPermissionService(workflow).has_view(user=old_user)


def test_reassign_workflow_members__user_to_group__preserves_template_owner(
    mocker,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    perm_svc = WorkflowPermissionService(workflow)
    perm_svc.grant_view(
        user=old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    perm_svc.grant_change(
        user=old_user,
        source_type=PermissionSource.TEMPLATE_OWNER,
        source_id=workflow.template_id or 0,
    )

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.TEMPLATE_OWNER,
    ).exists()
    assert WorkflowPermissionService(workflow).has_change(user=old_user)


def test_reassign_workflow_members__user_to_group__multiple_workflows__ok(
    mocker,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_group = create_test_group(account, name='new grp')
    workflow_1 = create_test_workflow(user=account_owner, tasks_count=1)
    workflow_2 = create_test_workflow(user=account_owner, tasks_count=1)
    for workflow in (workflow_1, workflow_2):
        WorkflowPermissionService(workflow).grant_view(
            user=old_user,
            source_type=PermissionSource.WORKFLOW_VIEWER,
            source_id=workflow.pk,
        )

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert not WorkflowPermissionService(workflow_1).has_view(
        user=old_user,
    )
    assert not WorkflowPermissionService(workflow_2).has_view(
        user=old_user,
    )


def test_reassign_workflow_members__user_to_group__no_viewer_rows__ok(
    mocker,
):
    """Revoke is a no-op when old_user has no WORKFLOW_VIEWER rows."""

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=account_owner, tasks_count=1)

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(workflow.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()


def test_reassign_workflow_members__group_to_user__no_viewer_revoke(
    mocker,
):
    """group→user has no old_user WORKFLOW_VIEWER to revoke/transfer."""

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_group = create_test_group(account, name='old grp')
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    create_test_workflow(user=account_owner, tasks_count=1)

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    transfer_mock = mocker.patch.object(
        ReassignService, '_transfer_workflow_viewer_rows',
    )
    revoke_mock = mocker.patch.object(
        ReassignService, '_revoke_workflow_viewer_rows',
    )

    service = ReassignService(old_group=old_group, new_user=new_user)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    transfer_mock.assert_not_called()
    revoke_mock.assert_not_called()


def test_reassign_workflow_members__user_to_user__calls_transfer_not_revoke(
    mocker,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    create_test_workflow(user=account_owner, tasks_count=1)

    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    transfer_mock = mocker.patch.object(
        ReassignService, '_transfer_workflow_viewer_rows',
    )
    revoke_mock = mocker.patch.object(
        ReassignService, '_revoke_workflow_viewer_rows',
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    transfer_mock.assert_called_once_with()
    revoke_mock.assert_not_called()


def test_transfer_workflow_viewer__scopes_to_account__ok(mocker):
    """user→user must not transfer WORKFLOW_VIEWER outside account."""

    # arrange
    account_a = create_test_account(name='account_a')
    account_b = create_test_account(name='account_b')
    owner_a = create_test_owner(
        account=account_a, email='owner_a@test.test',
    )
    owner_b = create_test_owner(
        account=account_b, email='owner_b@test.test',
    )
    old_user = create_test_admin(
        account=account_a, email='old@a.test',
    )
    new_user = create_test_admin(
        account=account_a, email='new@a.test',
    )
    wf_a = create_test_workflow(user=owner_a, tasks_count=1)
    wf_b = create_test_workflow(user=owner_b, tasks_count=1)
    WorkflowPermissionService(wf_a).grant_view(
        user=old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=wf_a.pk,
    )
    # Bypass grant_view account guard to simulate orphan UOP
    ct = ContentType.objects.get_for_model(Workflow)
    view_perm = Permission.objects.get(
        content_type=ct,
        codename=WorkflowPermission.VIEW,
    )
    UserObjectPermission.objects.create(
        user=old_user,
        permission=view_perm,
        content_type=ct,
        object_pk=str(wf_b.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=wf_b.pk,
    )
    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    assert UserObjectPermission.objects.filter(
        user=new_user,
        content_type=ct,
        object_pk=str(wf_a.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(wf_a.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(wf_b.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert not UserObjectPermission.objects.filter(
        user=new_user,
        content_type=ct,
        object_pk=str(wf_b.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()


def test_revoke_workflow_viewer__scopes_to_account__ok(mocker):
    """user→group must not revoke WORKFLOW_VIEWER outside account."""

    # arrange
    account_a = create_test_account(name='account_a')
    account_b = create_test_account(name='account_b')
    owner_a = create_test_owner(
        account=account_a, email='owner_a2@test.test',
    )
    owner_b = create_test_owner(
        account=account_b, email='owner_b2@test.test',
    )
    old_user = create_test_admin(
        account=account_a, email='old@a.test',
    )
    new_group = create_test_group(account_a, name='new grp')
    wf_a = create_test_workflow(user=owner_a, tasks_count=1)
    wf_b = create_test_workflow(user=owner_b, tasks_count=1)
    WorkflowPermissionService(wf_a).grant_view(
        user=old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=wf_a.pk,
    )
    ct = ContentType.objects.get_for_model(Workflow)
    view_perm = Permission.objects.get(
        content_type=ct,
        codename=WorkflowPermission.VIEW,
    )
    UserObjectPermission.objects.create(
        user=old_user,
        permission=view_perm,
        content_type=ct,
        object_pk=str(wf_b.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=wf_b.pk,
    )
    mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=set())

    # assert
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(wf_a.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        object_pk=str(wf_b.pk),
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()


def test_affected_workflow_ids__scopes_to_account__ok():
    """Performer sync must not target workflows from other accounts."""

    # arrange
    account_a = create_test_account(name='account_a')
    account_b = create_test_account(name='account_b')
    owner_a = create_test_owner(
        account=account_a, email='owner_a3@test.test',
    )
    owner_b = create_test_owner(
        account=account_b, email='owner_b3@test.test',
    )
    old_user = create_test_admin(
        account=account_a, email='old@a.test',
    )
    new_user = create_test_admin(
        account=account_a, email='new@a.test',
    )
    wf_a = create_test_workflow(user=owner_a, tasks_count=1)
    wf_b = create_test_workflow(user=owner_b, tasks_count=1)
    WorkflowPermissionService(wf_a).grant_view(
        user=old_user,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
    ct = ContentType.objects.get_for_model(Workflow)
    view_perm = Permission.objects.get(
        content_type=ct,
        codename=WorkflowPermission.VIEW,
    )
    UserObjectPermission.objects.create(
        user=old_user,
        permission=view_perm,
        content_type=ct,
        object_pk=str(wf_b.pk),
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    affected = service._affected_workflow_ids(tp_workflow_ids=set())

    # assert
    assert wf_a.id in affected
    assert wf_b.id not in affected


def test_revoke_workflow_viewer_rows__only_viewer_source__ok():
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    other_user = create_test_admin(
        account=account, email='other@test.test',
    )
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=account_owner, tasks_count=1)
    perm_svc = WorkflowPermissionService(workflow)
    perm_svc.grant_view(
        user=old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    task = workflow.tasks.get(number=1)
    perm_svc.grant_view(
        user=old_user,
        source_type=PermissionSource.PERFORMER,
        source_id=task.id,
    )
    perm_svc.grant_view(
        user=other_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._revoke_workflow_viewer_rows()

    # assert
    ct = ContentType.objects.get_for_model(Workflow)
    assert not UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()
    assert UserObjectPermission.objects.filter(
        user=old_user,
        content_type=ct,
        source_type=PermissionSource.PERFORMER,
    ).exists()
    assert UserObjectPermission.objects.filter(
        user=other_user,
        content_type=ct,
        source_type=PermissionSource.WORKFLOW_VIEWER,
    ).exists()


def test_reassign_workflow_owners__calls_sync(mocker):
    """update_workflow_owners must be called synchronously."""

    # arrange
    account = create_test_account()
    old_user = create_test_owner(account=account)
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    update_mock = mocker.patch(
        'src.accounts.services.reassign.update_workflow_owners',
    )
    on_commit_mock = mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_owners(affected_template_ids=[1, 2])

    # assert
    update_mock.assert_called_once_with(template_ids=[1, 2])
    on_commit_mock.assert_not_called()


def test_reassign_everywhere__complete_tasks_uses_on_commit(mocker):
    """complete_tasks.delay must be wrapped in on_commit."""

    # arrange
    account = create_test_account()
    old_user = create_test_owner(account=account)
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    mocker.patch.object(
        ReassignService, '_reassign_in_raw_performer_templates',
    )
    mocker.patch.object(
        ReassignService, '_reassign_in_template_owners',
    )
    mocker.patch.object(
        ReassignService, '_reassign_in_raw_performers',
    )
    mocker.patch.object(
        ReassignService, '_reassign_in_performers',
    )
    mocker.patch.object(
        ReassignService, '_affected_template_ids',
        return_value=[1],
    )
    mocker.patch.object(
        ReassignService, '_reassign_in_workflow_members',
    )
    mocker.patch.object(
        ReassignService, '_reassign_in_workflow_owners',
    )
    mocker.patch.object(
        ReassignService, '_reassign_in_template_conditions',
    )
    mocker.patch.object(
        ReassignService, '_reassign_in_conditions',
    )
    mocker.patch.object(
        ReassignService, '_cleanup_personal_groups',
    )
    on_commit_mock = mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service.reassign_everywhere()

    # assert
    assert on_commit_mock.call_count == 1


def test_tp_affected_workflow_ids__empty_group__ok():
    """Empty group has no UOP rows; TaskPerformer is source of truth.

    _tp_affected_workflow_ids must be called BEFORE
    _reassign_in_performers so it queries the old identity.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_group = create_test_group(account, name='old grp', users=[])
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(task=task).delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=old_group.id,
    )
    service = ReassignService(old_group=old_group, new_group=new_group)

    # act
    tp_ids = service._tp_affected_workflow_ids()

    # assert
    assert workflow.id in tp_ids


def test_affected_workflow_ids__merges_tp_and_uop__ok():
    """_affected_workflow_ids unions TaskPerformer IDs with UOP IDs."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    wf_uop = create_test_workflow(user=owner, tasks_count=1)
    wf_tp = create_test_workflow(user=owner, tasks_count=1)
    WorkflowPermissionService(wf_uop).grant_view(
        user=old_user,
        source_type=PermissionSource.PERFORMER,
        source_id=0,
    )
    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    affected = service._affected_workflow_ids(
        tp_workflow_ids={wf_tp.id},
    )

    # assert
    assert wf_uop.id in affected
    assert wf_tp.id in affected


def test_reassign_workflow_members__empty_group_to_group__syncs__ok(
    mocker,
):
    """group→group on empty old_group must sync PERFORMER_GROUP view."""

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    member = create_test_admin(
        account=account, email='member@test.test',
    )
    old_group = create_test_group(account, name='old grp', users=[])
    new_group = create_test_group(
        account, name='new grp', users=[member],
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.filter(task=task).delete()
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=old_group.id,
    )
    attach_mock = mocker.patch(
        'src.accounts.services.reassign.'
        'schedule_sync_workflow_attachment_permissions',
    )
    service = ReassignService(old_group=old_group, new_group=new_group)
    tp_ids = service._tp_affected_workflow_ids()
    service._reassign_in_performers()

    # act
    service._reassign_in_workflow_members(tp_workflow_ids=tp_ids)

    # assert
    assert WorkflowPermissionService(workflow).has_view(user=member)
    attach_mock.assert_called_once_with(workflow.id)
