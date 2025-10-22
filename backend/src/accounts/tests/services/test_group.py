import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.accounts.services.group import UserGroupService
from src.analytics.events import GroupsAnalyticsEvent
from src.authentication.enums import AuthTokenType
from src.notifications.tasks import (
    send_new_task_websocket,
    send_removed_task_notification,
)
from src.processes.enums import (
    DirectlyStatus,
    FieldType,
    OwnerType,
    PerformerType,
    TaskStatus,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestUserGroupService:

    def test_init_service__ok(self):

        # arrange
        account = create_test_account()
        request_user = create_test_admin(account=account)
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
        request_user = create_test_admin(account=account)
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
        request_user = create_test_admin(account=account)
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
            photo=photo,
        )

        # assert
        assert instance.name == name
        assert instance.photo == photo
        assert instance.account == account

    def test_create_related__with_users__ok(self):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_2 = create_test_admin(account=account, email='user2@test.test')
        group = create_test_group(account)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        # act
        service._create_related(
            users=[user, user_2],
        )

        # assert
        group.refresh_from_db()
        assert group.users.all().count() == 2
        assert group.users.get(id=user.id)
        assert group.users.get(id=user_2.id)

    def test_create_related__without_users__ok(self):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
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
        user = create_test_admin()
        group = create_test_group(user.account)
        is_superuser = False
        auth_type = AuthTokenType.API
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=auth_type,
        )

        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_group_created_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_created_notification.delay',
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
            new_photo=None,
        )
        send_group_created_mock.assert_called_once_with(
            logging=user.account.log_api_requests,
            account_id=user.account_id,
            group_data={
                'id': group.id,
                'name': group.name,
                'photo': group.photo,
                'users': [],
            },
        )

    def test_get_template_ids__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
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
        user = create_test_admin(account=account)
        group = create_test_group(account)
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
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[template.id],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            name=group.name,
            photo=group.photo,
            users=[user.id],
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_called_once_with([template.id])
        task_field_filter_mock.assert_not_called()
        task_field_filter_mock.return_value.update.assert_not_called()
        send_added_users_notifications_mock.assert_called_once_with([user.id])
        send_removed_users_notifications_mock.assert_not_called()
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
        send_group_updated_mock.assert_called_once()

    def test_partial_update__without_template__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        get_template_ids_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            name=group.name,
            photo=group.photo,
            users=[user.id],
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        send_added_users_notifications_mock.assert_called_once_with([user.id])
        send_removed_users_notifications_mock.assert_not_called()
        task_field_filter_mock.assert_not_called()
        task_field_filter_mock.return_value.update.assert_not_called()
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
        send_group_updated_mock.assert_called_once()

    def test_partial_update__all_fields__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_2 = create_test_admin(account=account, email='user2@test.test')
        group = create_test_group(account, users=[user])
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
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            users=[user_2.id],
            name=new_name,
            photo=photo,
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        send_added_users_notifications_mock.assert_called_once_with(
            [user_2.id],
        )
        send_removed_users_notifications_mock.assert_called_once_with(
            [user.id],
        )
        task_field_filter_mock.assert_called_once_with(
            type=FieldType.USER,
            group_id=group.id,
        )
        task_field_filter_mock.return_value.update.assert_called_once_with(
            value=new_name,
        )
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
        send_group_updated_mock.assert_called_once_with(
            logging=user.account.log_api_requests,
            account_id=user.account_id,
            group_data={
                'id': group.id,
                'name': group.name,
                'photo': group.photo,
                'users': [{
                    'id': user_2.id,
                    'first_name': user_2.first_name,
                    'last_name': user_2.last_name,
                    'email': user_2.email,
                    'photo': user_2.photo,
                    'is_admin': user_2.is_admin,
                    'is_account_owner': user_2.is_account_owner,
                }],
            },
        )

    def test_partial_update__added_users__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        get_template_ids_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            name=group.name,
            photo=group.photo,
            users=[user.id],
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        send_added_users_notifications_mock.assert_called_once_with([user.id])
        send_removed_users_notifications_mock.assert_not_called()
        task_field_filter_mock.assert_not_called()
        task_field_filter_mock.return_value.update.assert_not_called()
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
        send_group_updated_mock.assert_called_once()

    def test_partial_update__removed_users__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account, users=[user])
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        get_template_ids_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            name=group.name,
            photo=group.photo,
            users=[],
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        task_field_filter_mock.assert_not_called()
        task_field_filter_mock.return_value.update.assert_not_called()
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
        send_group_updated_mock.assert_called_once()

    def test_partial_update__name_changed__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
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
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            photo=group.photo,
            name=new_name,
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        send_added_users_notifications_mock.assert_not_called()
        send_removed_users_notifications_mock.assert_not_called()
        task_field_filter_mock.assert_called_once_with(
            type=FieldType.USER,
            group_id=group.id,
        )
        task_field_filter_mock.return_value.update.assert_called_once_with(
            value=new_name,
        )
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
        send_group_updated_mock.assert_called_once_with(
            logging=user.account.log_api_requests,
            account_id=user.account_id,
            group_data={
                'id': group.id,
                'name': group.name,
                'photo': group.photo,
                'users': [],
            },
        )

    def test_partial_update__photo_changed__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        photo = 'photo.jpg'
        get_template_ids_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            name=group.name,
            photo=photo,
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        send_added_users_notifications_mock.assert_not_called()
        send_removed_users_notifications_mock.assert_not_called()
        task_field_filter_mock.assert_not_called()
        task_field_filter_mock.return_value.update.assert_not_called()
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
        send_group_updated_mock.assert_called_once()

    def test_partial_update__photo_delete__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        delete_photo = ''
        group = create_test_group(account, photo='photo.jpg')
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        get_template_ids_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            name=group.name,
            photo=delete_photo,
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        send_added_users_notifications_mock.assert_not_called()
        send_removed_users_notifications_mock.assert_not_called()
        task_field_filter_mock.assert_not_called()
        task_field_filter_mock.return_value.update.assert_not_called()
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
        send_group_updated_mock.assert_called_once()

    def test_partial_update__without_all_fields__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        photo = 'url'
        group = create_test_group(account, photo=photo)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        get_template_ids_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            name=group.name,
            photo=photo,
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        send_added_users_notifications_mock.assert_not_called()
        send_removed_users_notifications_mock.assert_not_called()
        task_field_filter_mock.assert_not_called()
        task_field_filter_mock.return_value.update.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 0
        analytics_mock.assert_not_called()
        send_group_updated_mock.assert_called_once()

    def test_partial_update__empty_list_users__ok(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
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
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        task_field_filter_mock = mocker.patch(
            'src.accounts.services.group'
            '.TaskField.objects.filter',
            return_value=mocker.Mock(update=mocker.Mock(return_value=None)),
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_added_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_added_users_notifications',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_updated_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_updated_notification.delay',
        )

        # act
        service.partial_update(
            name=group.name,
            users=[],
            force_save=True,
        )

        # assert
        get_template_ids_mock.assert_not_called()
        update_workflow_owners_mock.assert_not_called()
        task_field_filter_mock.assert_not_called()
        task_field_filter_mock.return_value.update.assert_not_called()
        send_added_users_notifications_mock.assert_not_called()
        send_removed_users_notifications_mock.assert_not_called()
        group.refresh_from_db()
        assert group.users.all().count() == 0
        analytics_mock.assert_not_called()
        send_group_updated_mock.assert_called_once()

    def test_delete__with_template__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        template = create_test_template(user=user, is_active=True)
        group = create_test_group(account, users=[user])
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
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[template.id],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_deleted_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_deleted_notification.delay',
        )

        # act
        service.delete()

        # assert
        send_removed_users_notifications_mock.assert_called_once_with(
            [user.id],
        )
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
        send_group_deleted_mock.assert_called_once_with(
            logging=user.account.log_api_requests,
            account_id=user.account_id,
            group_data={
                'id': group.id,
                'name': group.name,
                'photo': group.photo,
                'users': [{
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'photo': user.photo,
                    'is_admin': user.is_admin,
                    'is_account_owner': user.is_account_owner,
                }],
            },
        )

    def test_delete__without_template__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account, users=[user])
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        get_list_template_ids_for_delete_group_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )
        send_group_deleted_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_deleted_notification.delay',
        )

        # act
        service.delete()

        # assert
        send_removed_users_notifications_mock.assert_called_once_with(
            [user.id],
        )
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
        send_group_deleted_mock.assert_called_once_with(
            logging=user.account.log_api_requests,
            account_id=user.account_id,
            group_data={
                'id': group.id,
                'name': group.name,
                'photo': group.photo,
                'users': [{
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'photo': user.photo,
                    'is_admin': user.is_admin,
                    'is_account_owner': user.is_account_owner,
                }],
            },
        )

    def test_delete__with_users__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account, users=[user])
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        get_list_template_ids_for_delete_group_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )

        # act
        service.delete()

        # assert
        send_removed_users_notifications_mock.assert_called_once_with(
            [user.id],
        )
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

    def test_delete__without_users__ok(self, mocker):

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )

        get_list_template_ids_for_delete_group_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._get_template_ids',
            return_value=[],
        )
        update_workflow_owners_mock = mocker.patch(
            'src.accounts.services.group.'
            'update_workflow_owners.delay',
        )
        analytics_mock = mocker.patch(
            'src.analytics.tasks.track_group_analytics.delay',
        )
        send_removed_users_notifications_mock = mocker.patch(
            'src.accounts.services.group.'
            'UserGroupService._send_removed_users_notifications',
        )

        # act
        service.delete()

        # assert
        send_removed_users_notifications_mock.assert_not_called()
        get_list_template_ids_for_delete_group_mock.assert_called_once_with()
        update_workflow_owners_mock.assert_not_called()
        analytics_mock.assert_called_once_with(
            event=GroupsAnalyticsEvent.deleted,
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
        )

    def test_send_added_users_notifications__user_not_in_group__send(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_add = create_test_admin(
            account=account,
            email='user_add@test.test',
        )
        group = create_test_group(account, users=[user_add.id])
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user_add.id],
            send_new_task_websocket,
        )

        # assert
        send_new_task_websocket_mock.assert_called_once_with(
            logging=account.log_api_requests,
            task_id=task.id,
            recipients=[
                (
                    user_add.id,
                    user_add.email,
                    user_add.is_new_tasks_subscriber,
                ),
            ],
            account_id=account.id,
        )

    def test_send_added_users_notifications__no_tasks__not_send(self, mocker):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account, users=[user.id])
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_new_task_websocket_mock = mocker.patch(
            'src.notifications.tasks.send_new_task_websocket',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_new_task_websocket,
        )

        # assert
        send_new_task_websocket_mock.assert_not_called()

    def test_send_added_users_notifications__single_workflow_multi_task__send(
        self,
        mocker,
    ):
        """ Tests notification for a user added to a group that performs
            multiple tasks in one workflow. Only the current task triggers
            a notification due to sequential task execution. """

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_to_notify = create_test_admin(
            account=account,
            email="user_to_notify@test.test",
        )
        group = create_test_group(account, users=[user_to_notify.id])
        workflow = create_test_workflow(user, tasks_count=2)
        task1 = workflow.tasks.get(number=1)
        task2 = workflow.tasks.get(number=2)
        TaskPerformer.objects.create(
            task_id=task1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task2.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            task_id=task1.id,
            recipients=[(
                user_to_notify.id,
                user_to_notify.email,
                user_to_notify.is_new_tasks_subscriber,
            )],
            account_id=account.id,
        )

    def test_send_added_users_notifications__multiple_workflows__send(
        self,
        mocker,
    ):
        """ Tests notifications for a user added to a group performing tasks
            in multiple workflows. Notifications are sent for the current task
            of each workflow. """
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_to_notify = create_test_admin(
            account=account,
            email="user_to_notify@test.test",
        )
        group = create_test_group(account, users=[user_to_notify.id])
        workflow = create_test_workflow(user, tasks_count=1)
        task1 = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        workflow2 = create_test_workflow(user, tasks_count=1)
        task2 = workflow2.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task2.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_new_task_websocket,
        )

        # assert
        assert send_notification_mock.call_count == 2
        send_notification_mock.assert_has_calls([
            mocker.call(
                logging=account.log_api_requests,
                task_id=task1.id,
                recipients=[(
                    user_to_notify.id,
                    user_to_notify.email,
                    user_to_notify.is_new_tasks_subscriber,
                )],
                account_id=account.id,
            ),
            mocker.call(
                logging=account.log_api_requests,
                task_id=task2.id,
                recipients=[(
                    user_to_notify.id,
                    user_to_notify.email,
                    user_to_notify.is_new_tasks_subscriber,
                )],
                account_id=account.id,
            ),
        ])

    def test_send_added_users_notifications__multiple_workflows_template__send(
        self,
        mocker,
    ):
        """ Tests notifications for a user added to a group performing tasks
            in multiple workflows created from a template. Notifications
            are sent for the current task of each workflow. """

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_to_notify = create_test_admin(
            account=account,
            email="user_to_notify@test.test",
        )
        group = create_test_group(account, users=[user_to_notify.id])
        template = create_test_template(user, tasks_count=1, is_active=True)
        workflow = create_test_workflow(template=template, user=user)
        task1 = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        workflow2 = create_test_workflow(template=template, user=user)
        task2 = workflow2.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task2.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_new_task_websocket,
        )

        # assert
        assert send_notification_mock.call_count == 2
        send_notification_mock.assert_has_calls([
            mocker.call(
                logging=account.log_api_requests,
                task_id=task1.id,
                recipients=[(
                    user_to_notify.id,
                    user_to_notify.email,
                    user_to_notify.is_new_tasks_subscriber,
                )],
                account_id=account.id,
            ),
            mocker.call(
                logging=account.log_api_requests,
                task_id=task2.id,
                recipients=[(
                    user_to_notify.id,
                    user_to_notify.email,
                    user_to_notify.is_new_tasks_subscriber,
                )],
                account_id=account.id,
            ),
        ])

    def test_send_removed_users_notifications__user_not_performer__send(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_removed = create_test_admin(
            account=account,
            email="user_removed@test.test",
        )
        group = create_test_group(account)
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_removed_task_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_notification.delay',
        )

        # act
        service._send_users_notification(
            [user_removed.id],
            send_removed_task_notification,
        )

        # assert
        send_removed_task_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            task_id=task.id,
            recipients=[(user_removed.id, user_removed.email)],
            account_id=account.id,
        )

    def test_send_removed_users_notifications__user_in_performer__not_send(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_removed_task_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_notification.delay',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_removed_task_notification,
        )

        # assert
        send_removed_task_notification_mock.assert_not_called()

    def test_send_removed_users_notifications__no_tasks__not_send(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        group = create_test_group(account)
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_removed_task_notification_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_removed_task_notification',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_removed_task_notification,
        )

        # assert
        send_removed_task_notification_mock.assert_not_called()

    def test_send_removed_users_notifications__single_workflow__send(
        self,
        mocker,
    ):
        """ Tests notification of the removal of users from the group that
            performs multiple tasks in one workflow. Only the current task
            triggers a notification due to sequential task execution. """

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_to_notify = create_test_admin(
            account=account,
            email="user_to_notify@test.test",
        )
        group = create_test_group(account)
        workflow = create_test_workflow(user, tasks_count=2)
        task1 = workflow.tasks.get(number=1)
        task2 = workflow.tasks.get(number=2)
        TaskPerformer.objects.create(
            task_id=task1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        TaskPerformer.objects.create(
            task_id=task2.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_notification.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_removed_task_notification,
        )

        # assert
        send_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            task_id=task1.id,
            recipients=[(user_to_notify.id, user_to_notify.email)],
            account_id=account.id,
        )

    def test_send_removed_users_notifications__multiple_workflows__send(
        self,
        mocker,
    ):
        """ Tests notifications of the removal of users from the group
            performing tasks in multiple workflows. Notifications are sent for
            the current task of each workflow. """
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_to_notify = create_test_admin(
            account=account,
            email="user_to_notify@test.test",
        )
        group = create_test_group(account)
        workflow = create_test_workflow(user, tasks_count=1)
        task1 = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        workflow2 = create_test_workflow(user, tasks_count=1)
        task2 = workflow2.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task2.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_notification.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_removed_task_notification,
        )

        # assert
        assert send_notification_mock.call_count == 2
        send_notification_mock.assert_has_calls([
            mocker.call(
                logging=account.log_api_requests,
                task_id=task1.id,
                recipients=[(user_to_notify.id, user_to_notify.email)],
                account_id=account.id,
            ),
            mocker.call(
                logging=account.log_api_requests,
                task_id=task2.id,
                recipients=[(user_to_notify.id, user_to_notify.email)],
                account_id=account.id,
            ),
        ])

    def test_send_removed_users_notifications__multi_workflows_template__send(
        self,
        mocker,
    ):
        """ Tests notifications  of the removal of users from the group
            performing tasks in multiple workflows created from a template.
            Notifications are sent for the current task of each workflow. """

        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user_to_notify = create_test_admin(
            account=account,
            email="user_to_notify@test.test",
        )
        group = create_test_group(account)
        template = create_test_template(user, tasks_count=1, is_active=True)
        workflow = create_test_workflow(template=template, user=user)
        task1 = workflow.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task1.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        workflow2 = create_test_workflow(template=template, user=user)
        task2 = workflow2.tasks.get(number=1)
        TaskPerformer.objects.create(
            task_id=task2.id,
            type=PerformerType.GROUP,
            group_id=group.id,
        )
        is_superuser = False
        service = UserGroupService(
            user=user,
            is_superuser=is_superuser,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_removed_task_notification.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_removed_task_notification,
        )

        # assert
        assert send_notification_mock.call_count == 2
        send_notification_mock.assert_has_calls([
            mocker.call(
                logging=account.log_api_requests,
                task_id=task1.id,
                recipients=[(user_to_notify.id, user_to_notify.email)],
                account_id=account.id,
            ),
            mocker.call(
                logging=account.log_api_requests,
                task_id=task2.id,
                recipients=[(user_to_notify.id, user_to_notify.email)],
                account_id=account.id,
            ),
        ])

    def test_send_users_notification__group_performer_completed__not_send(
        self,
        mocker,
    ):
        """Group performer has already completed the task"""
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user2 = create_test_admin(account=account, email='user2@test.test')
        other_user = create_test_admin(
            account=account,
            email='other@test.test',
        )
        group = create_test_group(account, users=[user, user2])

        template = create_test_template(other_user, tasks_count=1)
        workflow = create_test_workflow(other_user, template=template)
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group,
            is_completed=True,
            directly_status=DirectlyStatus.CREATED,
        )

        service = UserGroupService(
            user=user,
            is_superuser=False,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user.id, user2.id],
            send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_not_called()

    def test_send_users_notification__task_completed_status__not_send(
        self,
        mocker,
    ):
        """Task status is completed"""
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        other_user = create_test_admin(
            account=account,
            email='other@test.test',
        )
        group = create_test_group(account, users=[user])

        template = create_test_template(other_user, tasks_count=1)
        workflow = create_test_workflow(other_user, template=template)
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group,
            is_completed=False,
            directly_status=DirectlyStatus.CREATED,
        )

        task.status = TaskStatus.COMPLETED
        task.date_completed = timezone.now()
        task.save(update_fields=['status', 'date_completed'])

        service = UserGroupService(
            user=user,
            is_superuser=False,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_not_called()

    def test_send_users_notification__rcba_partial_completion__send(
        self,
        mocker,
    ):
        """Task with require_completion_by_all: group not completed,
        another performer completed"""
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user2 = create_test_admin(account=account, email='user2@test.test')
        other_user = create_test_admin(account=account,
                                       email='other@test.test')
        group = create_test_group(account, users=[user2])

        template = create_test_template(other_user, tasks_count=1)
        task_template = template.tasks.get(number=1)
        task_template.require_completion_by_all = True
        task_template.save()

        workflow = create_test_workflow(other_user, template=template)
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group,
            is_completed=False,
            directly_status=DirectlyStatus.CREATED,
        )

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.USER,
            user=user,
            is_completed=True,
            directly_status=DirectlyStatus.CREATED,
        )

        service = UserGroupService(
            user=user,
            is_superuser=False,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user2.id],
            send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            task_id=task.id,
            recipients=[(
                user2.id,
                user2.email,
                user2.is_new_tasks_subscriber,
            )],
            account_id=account.id,
        )

    def test_send_users_notification__user_in_completed_group__not_send(
        self,
        mocker,
    ):
        """User doesn't receive notifications if they are in another
        group that has completed the task"""

        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user = create_test_admin(account=account)

        group1 = create_test_group(account, users=[user])
        group2 = create_test_group(account, users=[user, owner])

        workflow = create_test_workflow(owner, tasks_count=2)
        task = workflow.tasks.get(number=1)
        task.require_completion_by_all = True
        task.save()
        task.performers.all().delete()

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group1,
            is_completed=True,
        )

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group2,
            is_completed=False,
        )

        service = UserGroupService(
            user=owner,
            is_superuser=False,
            instance=group2,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            user_ids=[user.id],
            send_notification_task=send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_not_called()

    def test_send_users_notification__user_in_uncompleted_groups__not_send(
        self,
        mocker,
    ):
        """User doesn't receive notifications if they are in another
        group that hasn't completed the task"""
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        user2 = create_test_admin(account=account, email='user2@test.test')
        user3 = create_test_admin(account=account, email='user3@test.test')
        other_user = create_test_admin(account=account,
                                       email='other@test.test')

        group1 = create_test_group(account, users=[user, user2])
        group2 = create_test_group(account, users=[user, user3])

        template = create_test_template(other_user, tasks_count=1)
        workflow = create_test_workflow(other_user, template=template)
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group1,
            is_completed=False,
            directly_status=DirectlyStatus.CREATED,
        )

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group2,
            is_completed=False,
            directly_status=DirectlyStatus.CREATED,
        )

        service = UserGroupService(
            user=user,
            is_superuser=False,
            instance=group2,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user.id, user3.id],
            send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_called_once_with(
            logging=account.log_api_requests,
            task_id=task.id,
            recipients=[(
                user3.id,
                user3.email,
                user3.is_new_tasks_subscriber,
            )],
            account_id=account.id,
        )

    def test_send_users_notification__performer_deleted__not_send(
        self,
        mocker,
    ):
        """Deleted performer - no notification sent"""
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        other_user = create_test_admin(account=account,
                                       email='other@test.test')
        group = create_test_group(account, users=[user])

        template = create_test_template(other_user, tasks_count=1)
        workflow = create_test_workflow(other_user, template=template)
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group,
            is_completed=False,
            directly_status=DirectlyStatus.DELETED,
        )

        service = UserGroupService(
            user=user,
            is_superuser=False,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_not_called()

    @pytest.mark.parametrize(
        'task_status',
        [
            TaskStatus.PENDING,
            TaskStatus.DELAYED,
            TaskStatus.SKIPPED,
        ],
    )
    def test_send_users_notification__task_non_running_status__not_send(
        self,
        task_status,
        mocker,
    ):
        """Task in non-RUNNING status"""
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        other_user = create_test_admin(
            account=account,
            email='other@test.test',
        )
        group = create_test_group(account, users=[user])

        template = create_test_template(other_user, tasks_count=1)
        workflow = create_test_workflow(other_user, template=template)
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group,
            is_completed=False,
            directly_status=DirectlyStatus.CREATED,
        )

        task.status = task_status
        task.save()

        service = UserGroupService(
            user=user,
            is_superuser=False,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_not_called()

    def test_send_users_notification__deleted_task__no_notification(
        self,
        mocker,
    ):
        """Deleted task - no notification sent"""
        # arrange
        account = create_test_account()
        user = create_test_admin(account=account)
        other_user = create_test_admin(account=account,
                                       email='other@test.test')
        group = create_test_group(account, users=[user])

        template = create_test_template(other_user, tasks_count=1)
        workflow = create_test_workflow(other_user, template=template)
        task = workflow.tasks.get(number=1)

        TaskPerformer.objects.create(
            task=task,
            type=PerformerType.GROUP,
            group=group,
            is_completed=False,
            directly_status=DirectlyStatus.CREATED,
        )

        task.delete()

        service = UserGroupService(
            user=user,
            is_superuser=False,
            instance=group,
            auth_type=AuthTokenType.USER,
        )
        send_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_new_task_websocket.delay',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_new_task_websocket,
        )

        # assert
        send_notification_mock.assert_not_called()
