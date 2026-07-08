import pytest
from django.contrib.contenttypes.models import ContentType

from src.accounts.services import exceptions
from src.accounts.services.reassign import ReassignService
from src.permissions.enums import PermissionSource
from src.permissions.models import UserObjectPermission
from src.processes.enums import (
    ConditionAction,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
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
        user = create_test_user()

        # act
        with pytest.raises(exceptions.ReassignUserSameUser):
            ReassignService(old_user=user, new_user=user)

    def test_init__to_the_same_group__raise_exception(self):

        # arrange
        user = create_test_user()
        group = create_test_group(user.account)

        # act
        with pytest.raises(exceptions.ReassignUserSameGroup):
            ReassignService(old_group=group, new_group=group)

    def test_init__only_old_group__raise_exception(self):

        # arrange
        user = create_test_user()
        group = create_test_group(user.account)

        # act
        with pytest.raises(exceptions.ReassignNewUserDoesNotExist):
            ReassignService(old_group=group)

    def test_init__only_old_user__raise_exception(self):

        # arrange
        user = create_test_user()

        # act
        with pytest.raises(exceptions.ReassignNewUserDoesNotExist):
            ReassignService(old_user=user)

    def test_init__only_new_group__raise_exception(self):

        # arrange
        user = create_test_user()
        group = create_test_group(user.account)

        # act
        with pytest.raises(exceptions.ReassignOldUserDoesNotExist):
            ReassignService(new_group=group)

    def test_init__only_new_user__raise_exception(self):

        # arrange
        user = create_test_user()

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
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            task__account=account,
        )
        exclude_mock.assert_called_once_with(
            task__status='completed',
        )
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
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            task__account=account,
        )
        exclude_mock.assert_called_once_with(
            task__status='completed',
        )
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
        on_commit_mock = mocker.patch(
            'src.accounts.services.reassign.transaction.on_commit',
        )

        service = ReassignService(old_user=old_user, new_user=new_user)
        affected_template_ids = [template.id]

        # act
        service._reassign_in_workflow_owners(affected_template_ids)

        # assert
        on_commit_mock.assert_called_once()
        on_commit_mock.call_args[0][0]()
        update_task_mock.delay.assert_called_once_with(
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
        update_task_mock.delay.assert_not_called()

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
        _reassign_in_workflow_members must schedule
        update_workflow_viewers via on_commit and NOT synchronously
        purge source-tracked view rows (PERFORMER etc.) — cleanup
        of stale rows for old_user is deferred to the async
        set_viewers() diff.
        """
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')
        workflow = create_test_workflow(user=old_user, tasks_count=1)

        WorkflowPermissionService(workflow).grant_view_bulk(
            [old_user.id],
            source_type=PermissionSource.PERFORMER,
            source_id=0,
        )

        update_task_mock = mocker.patch(
            'src.processes.tasks.update_workflow.update_workflow_viewers',
        )
        on_commit_mock = mocker.patch(
            'src.accounts.services.reassign.transaction.on_commit',
        )

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_workflow_members()

        # assert
        assert WorkflowPermissionService(workflow).has_view(old_user)
        on_commit_mock.assert_called_once()
        on_commit_mock.call_args[0][0]()
        update_task_mock.delay.assert_called_once_with([workflow.id])

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


def test_reassign_workflow_members__dispatches_async_task__ok(mocker):
    """
    _reassign_in_workflow_members must dispatch update_workflow_viewers
    via on_commit for all affected workflows and NOT synchronously
    delete source-tracked view_workflow rows — the async
    set_viewers() diff handles PERFORMER/TEMPLATE_OWNER cleanup.
    """

    # arrange
    account = create_test_account()
    old_user = create_test_owner(account=account)
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    workflow = create_test_workflow(user=old_user, tasks_count=1)

    assert WorkflowPermissionService(workflow).has_view(user=old_user)

    update_task_mock = mocker.patch(
        'src.processes.tasks.update_workflow.update_workflow_viewers',
    )
    on_commit_mock = mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members()

    # assert
    assert WorkflowPermissionService(workflow).has_view(user=old_user)

    on_commit_mock.assert_called_once()
    on_commit_mock.call_args[0][0]()
    update_task_mock.delay.assert_called_once_with([workflow.id])


def test_reassign_workflow_members__transfers_workflow_viewer__ok(mocker):
    """
    Legacy WORKFLOW_VIEWER rows have no source of truth, so they must
    be transferred synchronously from old_user to new_user; otherwise
    set_viewers() would preserve them on old_user and new_user would
    never receive them.
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
        old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    mocker.patch(
        'src.processes.tasks.update_workflow.update_workflow_viewers',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members()

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
    workflow, the old_user duplicate must be deleted (not left dangling)
    so the transfer UPDATE cannot violate the uniqueness constraint.
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
        old_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )
    perm_svc.grant_view(
        new_user,
        source_type=PermissionSource.WORKFLOW_VIEWER,
        source_id=workflow.pk,
    )

    mocker.patch(
        'src.processes.tasks.update_workflow.update_workflow_viewers',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )

    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_members()

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


def test_reassign_workflow_members__old_group_only__no_viewer_transfer(mocker):
    """
    Group reassign (no old_user) must not attempt WORKFLOW_VIEWER
    transfer — that source_type is user-only, and there is no
    old_user to read from.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_group = create_test_group(account, name='old grp')
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=account_owner, tasks_count=1)

    mocker.patch(
        'src.processes.tasks.update_workflow.update_workflow_viewers',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    transfer_mock = mocker.patch.object(
        ReassignService, '_transfer_workflow_viewer_rows',
    )

    service = ReassignService(old_group=old_group, new_group=new_group)

    # act
    service._reassign_in_workflow_members()

    # assert
    transfer_mock.assert_not_called()
    assert workflow.id is not None


def test_reassign_workflow_members__user_to_group__no_viewer_transfer(mocker):
    """
    When old_user is replaced by new_group (no new_user), legacy
    WORKFLOW_VIEWER rows cannot be transferred to a group (that
    source_type is user-only) and must be left untouched — the async
    set_viewers() diff preserves them via section 5.
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    old_user = create_test_admin(
        account=account, email='old@test.test',
    )
    new_group = create_test_group(account, name='new grp')
    workflow = create_test_workflow(user=account_owner, tasks_count=1)

    mocker.patch(
        'src.processes.tasks.update_workflow.update_workflow_viewers',
    )
    mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    transfer_mock = mocker.patch.object(
        ReassignService, '_transfer_workflow_viewer_rows',
    )

    service = ReassignService(old_user=old_user, new_group=new_group)

    # act
    service._reassign_in_workflow_members()

    # assert
    transfer_mock.assert_not_called()
    assert workflow.id is not None


def test_reassign_workflow_owners__uses_on_commit(mocker):
    """update_workflow_owners.delay must be wrapped in on_commit."""

    # arrange
    account = create_test_account()
    old_user = create_test_owner(account=account)
    new_user = create_test_admin(
        account=account, email='new@test.test',
    )
    on_commit_mock = mocker.patch(
        'src.accounts.services.reassign.transaction.on_commit',
    )
    service = ReassignService(old_user=old_user, new_user=new_user)

    # act
    service._reassign_in_workflow_owners(affected_template_ids=[1, 2])

    # assert
    on_commit_mock.assert_called_once()


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
