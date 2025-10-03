import pytest
from src.processes.tests.fixtures import (
    create_test_template,
    create_test_workflow,
    create_test_user,
    create_test_account,
    create_test_group,
    create_test_admin
)
from src.accounts.services.reassign import ReassignService
from src.accounts.services import exceptions
from src.processes.enums import (
    PerformerType,
    OwnerType,
    PredicateType,
    PredicateOperator,
    ConditionAction,
)
from src.processes.models import (
    Condition,
    Rule,
    Predicate,
    Workflow,
    ConditionTemplate,
    RuleTemplate,
    PredicateTemplate
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
            is_account_owner=False
        )
        deleted_user = create_test_user(
            account=account,
            email='deleted@test.test',
            is_account_owner=True
        )
        reassign_in_raw_performer_templates_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performer_templates'
        )
        reassign_in_template_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_owners'
        )
        reassign_in_raw_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performers'
        )
        reassign_in_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_performers'
        )
        affected_template_ids_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_affected_template_ids'
        )
        affected_template_ids_mock.return_value = [1, 2]
        reassign_in_workflow_members_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_members'
        )
        reassign_in_workflow_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_owners'
        )
        reassign_in_template_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_conditions'
        )
        reassign_in_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_conditions'
        )
        complete_tasks_mock = mocker.patch(
            'src.processes.tasks.tasks.'
            'complete_tasks.delay'
        )
        service = ReassignService(
            old_user=deleted_user,
            new_user=new_user
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
        complete_tasks_mock.assert_called_once_with(
            user_id=new_user.id,
            is_superuser=False,
            auth_type='User'
        )

    def test_reassign_everywhere__call_services_new_group__ok(self, mocker):
        # arrange
        account = create_test_account(
            name='transfer from',
        )
        new_user = create_test_user(
            account=account,
            email='test@test.test',
            is_account_owner=False
        )
        group = create_test_group(account, users=[new_user])
        deleted_user = create_test_user(
            account=account,
            email='deleted@test.test',
            is_account_owner=True
        )
        reassign_in_raw_performer_templates_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performer_templates'
        )
        reassign_in_template_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_owners'
        )
        reassign_in_raw_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performers'
        )
        reassign_in_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_performers'
        )
        affected_template_ids_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_affected_template_ids'
        )
        affected_template_ids_mock.return_value = [1, 2]
        reassign_in_workflow_members_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_members'
        )
        reassign_in_workflow_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_owners'
        )
        reassign_in_template_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_conditions'
        )
        reassign_in_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_conditions'
        )
        complete_tasks_mock = mocker.patch(
            'src.processes.tasks.tasks.'
            'complete_tasks.delay'
        )
        service = ReassignService(
            old_user=deleted_user,
            new_group=group
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
        complete_tasks_mock.assert_called_once_with(
            user_id=new_user.id,
            is_superuser=False,
            auth_type='User'
        )

    def test_reassign_everywhere__call_services_new_group_users_null__ok(
        self,
        mocker
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
            is_account_owner=True
        )
        reassign_in_raw_performer_templates_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performer_templates'
        )
        reassign_in_template_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_owners'
        )
        reassign_in_raw_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performers'
        )
        reassign_in_performers_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_performers'
        )
        affected_template_ids_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_affected_template_ids'
        )
        affected_template_ids_mock.return_value = [1, 2]
        reassign_in_workflow_members_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_members'
        )
        reassign_in_workflow_owners_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_owners'
        )
        reassign_in_template_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_conditions'
        )
        reassign_in_conditions_mock = mocker.patch(
            'src.accounts.services.reassign.ReassignService.'
            '_reassign_in_conditions'
        )
        complete_tasks_mock = mocker.patch(
            'src.processes.tasks.tasks.'
            'complete_tasks.delay'
        )
        service = ReassignService(
            old_user=deleted_user,
            new_group=group
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
        complete_tasks_mock.assert_called_once_with(
            user_id=new_user.id,
            is_superuser=False,
            auth_type='User'
        )

    def test_reassign_in_raw_performer_templates__group_to_group__ok(
        self,
        mocker
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
            group=old_group
        )

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupFromRawPerformerTemplateQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformerTemplate.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_raw_performer_templates()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_group.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            account=account
        )
        update_mock.assert_called_once_with(group_id=new_group.id)

    def test_reassign_in_raw_performer_templates__group_to_user__ok(
        self,
        mocker
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account=account, name='old_group')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupUserFromRawPerformerTemplateQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformerTemplate.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_raw_performer_templates()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_user.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            account=account
        )
        update_mock.assert_called_once_with(
            type=PerformerType.USER,
            user_id=new_user.id,
            group_id=None
        )

    def test_reassign_in_raw_performer_templates__user_to_group__ok(
        self,
        mocker
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserGroupFromRawPerformerTemplateQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformerTemplate.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_raw_performer_templates()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_group.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            account=account
        )
        update_mock.assert_called_once_with(
            type=PerformerType.GROUP,
            group_id=new_group.id,
            user_id=None
        )

    def test_reassign_in_raw_performer_templates__user_to_user__ok(
        self,
        mocker
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromRawPerformerTemplateQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformerTemplate.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_raw_performer_templates()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_user.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            account=account
        )
        update_mock.assert_called_once_with(user_id=new_user.id)

    def test_reassign_in_raw_performers__group_to_group__ok(
        self,
        mocker
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupFromRawPerformerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformer.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_raw_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_group.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            account=account
        )
        update_mock.assert_called_once_with(group_id=new_group.id)

    def test_reassign_in_raw_performers__group_to_user__ok(
        self,
        mocker
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
            group_id=old_group.id
        )

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupUserFromRawPerformerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformer.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_raw_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_user.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            account=account
        )
        update_mock.assert_called_once_with(
            type=PerformerType.USER,
            user_id=new_user.id,
            group_id=None
        )

    def test_reassign_in_raw_performers__user_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserGroupFromRawPerformerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformer.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_raw_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_group.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            account=account
        )
        update_mock.assert_called_once_with(
            type=PerformerType.GROUP,
            group_id=new_group.id,
            user_id=None
        )

    def test_reassign_in_raw_performers__user_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromRawPerformerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawPerformer.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_raw_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_user.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            account=account
        )
        update_mock.assert_called_once_with(user_id=new_user.id)

    def test_reassign_in_performers__group_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupFromTaskPerformerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TaskPerformer.objects.filter'
        )
        exclude_mock = filter_mock.return_value.exclude
        update_mock = exclude_mock.return_value.update

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_group.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            task__account=account
        )
        exclude_mock.assert_called_once_with(
            task__status='completed'
        )
        update_mock.assert_called_once_with(
            group_id=new_group.id
        )

    def test_reassign_in_performers__group_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupUserFromTaskPerformerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TaskPerformer.objects.filter'
        )
        exclude_mock = filter_mock.return_value.exclude
        update_mock = exclude_mock.return_value.update

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_user.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            task__account=account
        )
        exclude_mock.assert_called_once_with(
            task__status='completed'
        )
        update_mock.assert_called_once_with(
            type=PerformerType.USER,
            user_id=new_user.id,
            group_id=None
        )

    def test_reassign_in_performers__user_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserGroupFromTaskPerformerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TaskPerformer.objects.filter'
        )
        exclude_mock = filter_mock.return_value.exclude
        update_mock = exclude_mock.return_value.update

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_group.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            task__account=account
        )
        exclude_mock.assert_called_once_with(
            task__status='completed'
        )
        update_mock.assert_called_once_with(
            type=PerformerType.GROUP,
            group_id=new_group.id,
            user_id=None
        )

    def test_reassign_in_performers__user_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromTaskPerformerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TaskPerformer.objects.filter'
        )
        exclude_mock = filter_mock.return_value.exclude
        update_mock = exclude_mock.return_value.update

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_performers()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_user.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            task__account=account
        )
        exclude_mock.assert_called_once_with(
            task__status='completed'
        )
        update_mock.assert_called_once_with(
            user_id=new_user.id
        )

    def test_reassign_in_template_owners__group_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupFromTemplateOwnerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TemplateOwner.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_group=new_group)

        # act
        service._reassign_in_template_owners()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_group.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            template__account=account
        )
        update_mock.assert_called_once_with(
            group_id=new_group.id
        )

    def test_reassign_in_template_owners__group_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteGroupUserFromTemplateOwnerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TemplateOwner.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_group=old_group, new_user=new_user)

        # act
        service._reassign_in_template_owners()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_group.id,
            substitution_id=new_user.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            group_id=old_group.id,
            template__account=account
        )
        update_mock.assert_called_once_with(
            type=PerformerType.USER,
            user_id=new_user.id,
            group_id=None
        )

    def test_reassign_in_template_owners__user_to_group__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserGroupFromTemplateOwnerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TemplateOwner.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_group=new_group)

        # act
        service._reassign_in_template_owners()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_group.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user=old_user,
            template__account=account
        )
        update_mock.assert_called_once_with(
            type=PerformerType.GROUP,
            group_id=new_group.id,
            user_id=None
        )

    def test_reassign_in_template_owners__user_to_user__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromTemplateOwnerQuery'
        )
        query_mock.return_value.get_sql.return_value = (
            'SQL_QUERY', {'params': 'values'}
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'TemplateOwner.objects.filter'
        )
        update_mock = filter_mock.return_value.update

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_template_owners()

        # assert
        query_mock.assert_called_once_with(
            delete_id=old_user.id,
            substitution_id=new_user.id
        )
        query_mock.return_value.get_sql.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user=old_user,
            template__account=account
        )
        update_mock.assert_called_once_with(
            user=new_user
        )

    def test_reassign_in_workflow_owners__with_template_ids__ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_user(account=account)
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')
        template = create_test_template(user, tasks_count=1, is_active=True)

        workflow_owners_filter_mock = mocker.patch(
            'src.processes.models.'
            'Workflow.owners.through.objects.filter'
        )
        workflow_owners_delete_mock = (
            workflow_owners_filter_mock.return_value.delete
        )
        update_query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'UpdateWorkflowOwnersQuery.__init__',
            return_value=None
        )
        query_insert_sql_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'UpdateWorkflowOwnersQuery.insert_sql',
            return_value=('SQL_QUERY', {'params': 'values'})
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )

        service = ReassignService(old_user=old_user, new_user=new_user)
        affected_template_ids = [template.id]

        # act
        service._reassign_in_workflow_owners(affected_template_ids)

        # assert
        workflow_owners_filter_mock.assert_called_once_with(
            workflow__template_id__in=affected_template_ids,
            workflow__account=account
        )
        workflow_owners_delete_mock.assert_called_once()
        update_query_mock.assert_called_once_with(template_id=template.id)
        query_insert_sql_mock.assert_called_once_with()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )

    def test_reassign_in_workflow_owners_with__empty_template_ids__ok(
        self,
        mocker
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        workflow_owners_filter_mock = mocker.patch(
            'src.processes.models.'
            'Workflow.owners.through.objects.filter'
        )
        workflow_owners_delete_mock = (
            workflow_owners_filter_mock.return_value.delete
        )
        query_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'UpdateWorkflowOwnersQuery.insert_sql',
            return_value=('SQL_QUERY', {'params': 'values'})
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )

        service = ReassignService(old_user=old_user, new_user=new_user)
        affected_template_ids = []

        # act
        service._reassign_in_workflow_owners(affected_template_ids)

        # assert
        workflow_owners_filter_mock.assert_not_called()
        workflow_owners_delete_mock.assert_not_called()
        query_mock.assert_not_called()
        sql_execute_mock.assert_not_called()

    def test_affected_template_ids__with_old_user_ok(self, mocker):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')
        template1 = create_test_template(
            old_user,
            tasks_count=1,
            is_active=True
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
            account=account
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
            account=account
        )
        filter_mock.return_value.distinct.assert_called_once()
        values_list_mock.assert_called_once_with('id', flat=True)

    def test_reassign_in_workflow_members__with_old_and_new_user__ok(
        self,
        mocker
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_user(account=account, email='old@example.com')
        new_user = create_test_user(account=account, email='new@example.com')

        query_init_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromWorkflowMembersQuery.__init__',
            return_value=None
        )
        query_get_sql_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'DeleteUserFromWorkflowMembersQuery.get_sql',
            return_value=('SQL_QUERY', {'params': 'values'})
        )
        sql_execute_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'RawSqlExecutor.execute'
        )
        filter_mock = mocker.patch(
            'src.accounts.services.reassign.'
            'Workflow.members.through.objects.filter',
            return_value=Workflow.members.through.objects.none()
        )
        update_mock = mocker.patch.object(
            filter_mock.return_value, 'update'
        )

        service = ReassignService(old_user=old_user, new_user=new_user)

        # act
        service._reassign_in_workflow_members()

        # assert
        query_init_mock.assert_called_once_with(
            user_to_delete=old_user.id,
            user_to_substitution=new_user.id
        )
        query_get_sql_mock.assert_called_once()
        sql_execute_mock.assert_called_once_with(
            'SQL_QUERY', {'params': 'values'}
        )
        filter_mock.assert_called_once_with(
            user_id=old_user.id,
            workflow__account=account
        )
        update_mock.assert_called_once_with(user_id=new_user.id)

    def test_reassign_in_template_conditions__with_old_and_new_user__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_admin(account=account, email='old@example.com')
        new_user = create_test_admin(account=account, email='new@example.com')
        template = create_test_template(
            old_user,
            is_active=True,
            tasks_count=1
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
            user=new_user
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.group is None
        assert not PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user
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
            tasks_count=1
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
            group=new_group
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.user is None
        assert not PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group
        ).exists()

    def test_reassign_in_template_conditions__with_old_group_and_new_user__ok(
        self
    ):
        # arrange
        account = create_test_account(name='test_account')
        user = create_test_admin(account=account, email='user@example.com')
        old_group = create_test_group(account, name='old_group')
        new_user = create_test_admin(account=account, email='new@example.com')
        template = create_test_template(
            user,
            is_active=True,
            tasks_count=1
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
            user=new_user
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.group is None
        assert not PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group
        ).exists()

    def test_reassign_in_template_conditions__with_old_user_and_new_group__ok(
        self
    ):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_admin(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')
        template = create_test_template(
            old_user,
            is_active=True,
            tasks_count=1
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
            group=new_group
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.user is None
        assert not PredicateTemplate.objects.filter(
            rule=rule_template,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user
        ).exists()

    def test_reassign_in_conditions__with_old_and_new_user__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_admin(account=account, email='old@example.com')
        new_user = create_test_admin(account=account, email='new@example.com')
        workflow = create_test_workflow(old_user, tasks_count=1)
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
            user=new_user
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.group is None
        assert not Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user
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
            group=new_group
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.user is None
        assert not Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group
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
            user=new_user
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.group is None
        assert not Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.GROUP,
            field='group_field',
            group=old_group
        ).exists()

    def test_reassign_in_conditions__with_old_user_and_new_group__ok(self):
        # arrange
        account = create_test_account(name='test_account')
        old_user = create_test_admin(account=account, email='old@example.com')
        new_group = create_test_group(account, name='new_group')
        workflow = create_test_workflow(old_user, tasks_count=1)
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
            group=new_group
        )
        assert predicates.count() == 1
        updated_predicate = predicates.first()
        assert updated_predicate.user is None
        assert not Predicate.objects.filter(
            rule=rule,
            field_type=PredicateType.USER,
            field='user_field',
            user=old_user
        ).exists()
