import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.accounts.enums import UserGroupType
from src.accounts.services.group import UserGroupService
from src.analysis.events import GroupsAnalyticsEvent
from src.authentication.enums import AuthTokenType
from src.notifications.tasks import (
    send_new_task_websocket,
    send_task_deleted_notification,
)
from src.processes.enums import (
    DirectlyStatus,
    FieldType,
    OwnerType,
    PerformerType,
    TaskStatus,
    WorkflowStatus,
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

        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
        )
        send_group_created_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_group_created_notification.delay',
        )

        # act
        service._create_actions()

        # assert
        analysis_mock.assert_called_once_with(
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
                'type': UserGroupType.REGULAR,
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
                    'manager_id': user_2.manager_id,
                    'subordinates_ids': [],
                }],
                'type': UserGroupType.REGULAR,
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
                'type': UserGroupType.REGULAR,
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_not_called()
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_not_called()
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
                    'manager_id': user.manager_id,
                    'subordinates_ids': [],
                }],
                'type': UserGroupType.REGULAR,
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
                    'manager_id': user.manager_id,
                    'subordinates_ids': [],
                }],
                'type': 'regular',
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
        analysis_mock = mocker.patch(
            'src.analysis.tasks.track_group_analytics.delay',
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
        analysis_mock.assert_called_once_with(
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
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_task_deleted_notification.delay',
        )

        # act
        service._send_users_notification(
            [user_removed.id],
            send_task_deleted_notification,
        )

        # assert
        send_task_deleted_notification_mock.assert_called_once_with(
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
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks'
            '.send_task_deleted_notification.delay',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_task_deleted_notification,
        )

        # assert
        send_task_deleted_notification_mock.assert_not_called()

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
        send_task_deleted_notification_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_task_deleted_notification',
        )

        # act
        service._send_users_notification(
            [user.id],
            send_task_deleted_notification,
        )

        # assert
        send_task_deleted_notification_mock.assert_not_called()

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
            '.send_task_deleted_notification.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_task_deleted_notification,
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
            '.send_task_deleted_notification.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_task_deleted_notification,
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
            '.send_task_deleted_notification.delay',
        )

        # act
        service._send_users_notification(
            [user_to_notify.id],
            send_task_deleted_notification,
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
        group2 = create_test_group(
            account=account,
            name='group 2',
            users=[user, owner],
        )

        workflow = create_test_workflow(owner, tasks_count=2)
        task = workflow.tasks.get(number=1)
        task.require_completion_by_all = True
        task.save()
        task.taskperformer_set.all().delete()

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
        other_user = create_test_admin(
            account=account,
            email='other@test.test',
        )

        group1 = create_test_group(account, users=[user, user2])
        group2 = create_test_group(
            account=account,
            name='group 2',
            users=[user, user3],
        )

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


def test_check_and_complete_tasks_no_matching_tasks__skip(mocker):

    """
    No matching tasks
    """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account)
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()


def test_check_and_complete_tasks__group_performer__ok(mocker):

    """
    Default parameters with matching task
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task,
        user=user,
        type=PerformerType.GROUP_USER,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_called_once_with(
        task_ids=[task.id],
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        account_id=account.id,
    )


def test_check_and_complete_tasks_multiple_matching_tasks_ok(mocker):

    """
    Multiple matching tasks
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    workflow_2 = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    task_2 = workflow_2.tasks.get(number=1)
    task_1.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task_1,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task_1,
        user=user,
        type=PerformerType.GROUP_USER,
    )
    task_2.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task_2,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task_2,
        user=user,
        type=PerformerType.GROUP_USER,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_called_once_with(
        task_ids=[task_1.id, task_2.id],
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        account_id=account.id,
    )


def test_check_and_complete_tasks_mixed_matching_tasks_ok(mocker):

    """
    Mixed matching and non-matching tasks
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    workflow_2 = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    task_2 = workflow_2.tasks.get(number=1)
    task_1.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task_1,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task_1,
        group=group,
        type=PerformerType.GROUP_USER,
    )
    task_2.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task_2,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task_2,
        group=group,
        type=PerformerType.GROUP_USER,
    )
    task_2.status = TaskStatus.COMPLETED
    task_2.save(update_fields=['status'])
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_called_once_with(
        task_ids=[task_1.id],
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        account_id=account.id,
    )


def test_check_and_complete_tasks__multiple_groups__ok(mocker):

    """
    Filters by instance id
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group_1 = create_test_group(account=account, users=[user])
    group_2 = create_test_group(
        account=account,
        name='Another group',
        users=[user],
    )
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    workflow_2 = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    task_2 = workflow_2.tasks.get(number=1)
    task_1.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task_1,
        group=group_1,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task_1,
        group=group_1,
        type=PerformerType.GROUP_USER,
    )
    task_2.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task_2,
        group=group_2,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task_2,
        group=group_2,
        type=PerformerType.GROUP_USER,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group_1,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_called_once_with(
        task_ids=[task_1.id],
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        account_id=account.id,
    )


def test_check_and_complete_tasks__two_workflows_two_tasks__ok(mocker):

    """
    Two workflows on same account
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow_1 = create_test_workflow(user=owner, tasks_count=1)
    workflow_2 = create_test_workflow(user=owner, tasks_count=1)
    task_1 = workflow_1.tasks.get(number=1)
    task_2 = workflow_2.tasks.get(number=1)
    task_1.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task_1,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task_1,
        user=user,
        type=PerformerType.GROUP_USER,
    )
    task_2.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task_2,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task_2,
        user=user,
        type=PerformerType.GROUP_USER,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_called_once_with(
        task_ids=[task_1.id, task_2.id],
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        account_id=account.id,
    )


def test_check_and_complete_tasks__group_and_user_performer__ok(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task,
        user=user,
        type=PerformerType.USER,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_called_once_with(
        task_ids=[task.id],
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        account_id=account.id,
    )


@pytest.mark.parametrize('status', TaskStatus.INACTIVE_STATUS)
def test_check_and_complete_tasks_not_active_task__skip(
    status,
    mocker,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.status = status
    task.save(update_fields=['status'])
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task,
        user=user,
        type=PerformerType.GROUP_USER,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()


@pytest.mark.parametrize(
    'status',
    (WorkflowStatus.DONE, WorkflowStatus.DELAYED),
)
def test_check_and_complete_tasks__non_running_workflow__skip(
    status,
    mocker,
):

    """
    Excludes non-running workflow
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        status=status,
    )
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()


def test_check_and_complete_tasks__group_non_performer__skip(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    create_test_workflow(user=owner, tasks_count=1)
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()


def test_check_and_complete_tasks__completed_performer__skip(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
        is_completed=True,
    )
    TaskPerformer.objects.create(
        task=task,
        user_id=user.id,
        type=PerformerType.GROUP_USER,
        is_completed=True,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()


def test_check_and_complete_tasks__rcba_and_completed_performer__skip(mocker):

    """
    Excludes completed performer when all must complete
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
        is_completed=True,
    )
    TaskPerformer.objects.create(
        task=task,
        user=user,
        type=PerformerType.GROUP_USER,
        is_completed=True,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()


def test_check_and_complete_tasks__rcba__ok(mocker):

    """
    Excludes completed performer when all must complete
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.require_completion_by_all = True
    task.save(update_fields=['require_completion_by_all'])
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
    )
    TaskPerformer.objects.create(
        task=task,
        user=user,
        type=PerformerType.GROUP_USER,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_called_once_with(
        task_ids=[task.id],
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        account_id=account.id,
    )


def test_check_and_complete_tasks__directly_deleted_performer__skip(mocker):

    """
    Excludes deleted direct performer
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account, users=[user])
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=group,
        type=PerformerType.GROUP,
        directly_status=DirectlyStatus.DELETED,
    )
    TaskPerformer.objects.create(
        task=task,
        user=user,
        type=PerformerType.GROUP_USER,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()


def test_check_and_complete_tasks__other_group_performer__skip(mocker):

    """
    Excludes group performer when instance group is not the performer
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    group = create_test_group(account=account)
    other_group = create_test_group(
        account=account,
        name='Other group',
    )
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=other_group,
        type=PerformerType.GROUP,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()


def test_check_and_complete_tasks__other_account_task__skip(mocker):

    """
    Excludes task from another account
    """

    # arrange
    account_1 = create_test_account()
    user = create_test_admin(account=account_1)
    group = create_test_group(account=account_1)
    account_2 = create_test_account(name='Another account')
    owner_2 = create_test_owner(
        account=account_2,
        email='owner2@pneumatic.app',
    )
    other_group = create_test_group(account=account_2)
    workflow = create_test_workflow(user=owner_2, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.taskperformer_set.all().delete()
    TaskPerformer.objects.create(
        task=task,
        group=other_group,
        type=PerformerType.GROUP,
    )
    check_and_complete_tasks_delay_mock = mocker.patch(
        target='src.accounts.services.group.check_and_complete_tasks.delay',
    )
    service = UserGroupService(
        user=user,
        instance=group,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._check_and_complete_tasks()

    # assert
    check_and_complete_tasks_delay_mock.assert_not_called()
