import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_group,
    create_test_template,
)
from pneumatic_backend.accounts.services.group import UserGroupService
from pneumatic_backend.analytics.events import GroupsAnalyticsEvent
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.models.templates.owner import (
    TemplateOwner
)
from pneumatic_backend.processes.enums import OwnerType
from django.contrib.auth import get_user_model


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestUserGroupService:

    def test_init_service__ok(self):

        # arrange
        account = create_test_account()
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
        account = create_test_account()
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
        account = create_test_account()
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
            users=[request_user],
            photo=photo
        )

        # assert
        assert instance.name == name
        assert instance.photo == photo
        assert instance.account == account

    def test_create_related__with_users__ok(self):

        # arrange
        account = create_test_account()
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
        account = create_test_account()
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

    def test_create_actions__ok(self, mocker):
        # arrange
        user = create_test_user()
        group = create_test_group(user=user)
        is_superuser = False
        auth_type = AuthTokenType.API
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=auth_type,
        )

        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service._create_actions()

        # assert
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.created,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=None,
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=auth_type,
            is_superuser=is_superuser,
            new_users_ids=None,
            new_photo=None
        )

    def test_get_template_ids__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(user=user)
        template = create_test_template(user, is_active=True)

        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )

        service = UserGroupService(
            user=user,
            is_superuser=False,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        # act
        template_ids = service._get_template_ids()

        # assert
        assert len(template_ids) == 1
        assert template.id in template_ids

    def test_partial_update__with_template__ok(self, mocker):

        # arrange
        account = create_test_account()
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
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            name=group.name,
            photo=group.photo,
            users=[user.id],
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_called_once_with([template.id])
        group.refresh_from_db()
        assert group.users.all().count() == 1
        assert group.users.get(id=user.id)
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.updated,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[user.id],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
            new_name=None,
            new_photo=None,
            removed_users_ids=[],
            new_users_ids=[user.id],
        )

    def test_partial_update__without_template__ok(self, mocker):

        # arrange
        account = create_test_account()
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
            'UserGroupService._get_template_ids',
            return_value=[]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            name=group.name,
            photo=group.photo,
            users=[user.id],
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 1
        assert group.users.get(id=user.id)
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.updated,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[user.id],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
            new_name=None,
            new_photo=None,
            removed_users_ids=[],
            new_users_ids=[user.id],
        )

    def test_partial_update__all_fields__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        user_2 = create_test_user(account=account, email='test@test.app')
        group = create_test_group(user=user, users=[user])
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        new_name = 'New name group'
        photo = 'photo.jpg'
        get_template_ids_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            users=[user_2.id],
            name=new_name,
            photo=photo,
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 1
        assert group.users.get(id=user_2.id)
        assert group.name == new_name
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.updated,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[user_2.id],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
            new_name=new_name,
            new_photo=photo,
            removed_users_ids=[user.id],
            new_users_ids=[user_2.id],
        )

    def test_partial_update__added_users__ok(self, mocker):

        # arrange
        account = create_test_account()
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
            'UserGroupService._get_template_ids',
            return_value=[]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            name=group.name,
            photo=group.photo,
            users=[user.id],
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 1
        assert group.users.get(id=user.id)
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.updated,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[user.id],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
            new_name=None,
            new_photo=None,
            removed_users_ids=[],
            new_users_ids=[user.id],
        )

    def test_partial_update__removed_users__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(user=user, users=[user])
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
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            name=group.name,
            photo=group.photo,
            users=[],
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 0
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.updated,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
            new_name=None,
            new_photo=None,
            removed_users_ids=[user.id],
            new_users_ids=[],
        )

    def test_partial_update__name_changed__ok(self, mocker):

        # arrange
        account = create_test_account()
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
        new_name = 'New name group'
        get_template_ids_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            photo=group.photo,
            name=new_name,
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        group.refresh_from_db()
        assert group.name == new_name
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.updated,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
            new_name=new_name,
            new_photo=None,
            removed_users_ids=None,
            new_users_ids=None,
        )

    def test_partial_update__photo_changed__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(user=user)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        photo = 'photo.jpg'
        get_template_ids_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[]
        )
        update_workflow_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.group.'
            'update_workflow_owners.delay'
        )
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            name=group.name,
            photo=photo,
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.updated,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
            new_name=None,
            new_photo=photo,
            removed_users_ids=None,
            new_users_ids=None,
        )

    def test_partial_update__photo_delete__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        delete_photo = ''
        group = create_test_group(user=user, photo='photo.jpg')
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
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            name=group.name,
            photo=delete_photo,
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.updated,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=delete_photo,
            group_users=[],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
            new_name=None,
            new_photo=delete_photo,
            removed_users_ids=None,
            new_users_ids=None,
        )

    def test_partial_update__without_all_fields__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        photo = 'url'
        group = create_test_group(user=user, photo=photo)
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
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            name=group.name,
            photo=photo,
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 0
        analytics_mock.assert_not_called()

    def test_partial_update__empty_list_users__ok(self, mocker):
        # arrange
        account = create_test_account()
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
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.partial_update(
            name=group.name,
            users=[],
            force_save=True
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_called_once_with([template.id])
        group.refresh_from_db()
        assert group.users.all().count() == 0
        analytics_mock.assert_not_called()

    def test_delete__with_template__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user, is_active=True)
        group = create_test_group(user=user, users=[user])
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
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.delete()

        # assert
        get_list_template_ids_for_delete_group_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_called_once_with([template.id])
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.deleted,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[user.id],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
        )

    def test_delete__without_template__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        group = create_test_group(user=user, users=[user])
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
        analytics_mock = mocker.patch(
            'pneumatic_backend.analytics.tasks.track_group_analytics.delay'
        )

        # act
        service.delete()

        # assert
        get_list_template_ids_for_delete_group_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.deleted,
            user_id=user.id,
            user_email=user.email,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            group_photo=group.photo,
            group_users=[user.id],
            account_id=user.account_id,
            group_id=group.id,
            group_name=group.name,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
        )
