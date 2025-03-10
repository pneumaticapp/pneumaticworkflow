import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_group,
    create_test_template,
)
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.accounts.services import UserGroupService
from pneumatic_backend.processes.models.templates.owner import (
    TemplateOwner
)
from pneumatic_backend.processes.enums import OwnerType

pytestmark = pytest.mark.django_db


class TestUserGroupService:

    def test_init_service__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        request_user = create_test_user(account=account)
        is_superuser = False

        # act
        service = UserGroupService(
            user=request_user,
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
        )

        # assert
        assert service.account is account
        assert service.user == request_user
        assert service.is_superuser == is_superuser
        assert service.auth_type == AuthTokenType.USER

    def test_create_instance__only_required_fields__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        request_user = create_test_user(account=account)
        name = "Test Group"
        is_superuser = False
        service = UserGroupService(
            user=request_user,
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
        )

        # act
        instance = service._create_instance(name=name)

        # assert
        assert instance.name == name
        assert instance.account == account

    def test_create_instance__all_fields__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        request_user = create_test_user(account=account)
        photo = 'http://my.lovely.photo.png'
        name = "Test Group"
        is_superuser = False
        service = UserGroupService(
            user=request_user,
            is_superuser=is_superuser,
            auth_type=AuthTokenType.USER,
        )

        # act
        instance = service._create_instance(
            name=name,
            users=[request_user, ],
            photo=photo
        )

        # assert
        assert instance.name == name
        assert instance.photo == photo
        assert instance.account == account

    def test_create_related__with_users__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test@test.app')
        group = create_test_group(user=user)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        # act
        service._create_related(
            users=[user, user_2]
        )

        # assert
        group.refresh_from_db()
        assert group.users.all().count() == 2
        assert group.users.get(id=user.id)
        assert group.users.get(id=user_2.id)

    def test_create_related__without_users__ok(self):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        group = create_test_group(user=user)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        # act
        service._create_related()

        # assert
        group.refresh_from_db()
        assert group.users.all().count() == 0

    def test_partial_update__with_users_and_template__ok(self, mocker):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test@test.app')
        group = create_test_group(user=user)
        template = create_test_template(user, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        new_name = 'New name group'
        get_template_ids_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[template.id]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )

        # act
        service.partial_update(
            users=[user_2],
            name=new_name,
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_called_once_with([template.id])
        group.refresh_from_db()
        assert group.users.all().count() == 1
        assert group.users.get(id=user_2.id)
        assert group.name == new_name

    def test_partial_update__with_users_without_template__ok(self, mocker):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test@test.app')
        group = create_test_group(user=user)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        get_template_ids_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )

        # act
        service.partial_update(
            users=[user_2],
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 1
        assert group.users.get(id=user_2.id)

    def test_partial_update__without_users_and_template__ok(self, mocker):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        group = create_test_group(user=user)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        get_template_ids_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids'
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )

        # act
        service.partial_update(
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 0

    def test_partial_update__empty_list_users__ok(self, mocker):
        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        group = create_test_group(user=user)
        template = create_test_template(user, is_active=True)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        get_template_ids_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[template.id]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )

        # act
        service.partial_update(
            users=[],
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_called_once_with([template.id])
        group.refresh_from_db()
        assert group.users.all().count() == 0

    def test_delete__with_template__ok(self, mocker):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(user=user, is_active=True)
        group = create_test_group(user=user, users=[user, ])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        get_list_template_ids_for_delete_group_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[template.id]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )

        # act
        service.delete()

        # assert
        get_list_template_ids_for_delete_group_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_called_once_with([template.id])

    def test_delete__without_template__ok(self, mocker):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        group = create_test_group(user=user, users=[user, ])
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        get_list_template_ids_for_delete_group_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )

        # act
        service.delete()

        # assert
        get_list_template_ids_for_delete_group_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
