import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from pneumatic_backend.accounts.enums import (
    NotificationStatus,
    NotificationType,
)
from pneumatic_backend.accounts.models import (
    APIKey,
    Notification
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.accounts.tokens import (
    DigestUnsubscribeToken,
    UnsubscribeEmailToken,
)
from pneumatic_backend.analytics.enums import MailoutType
from pneumatic_backend.authentication.tokens import PneumaticToken
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.models import (
    Delay,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_workflow,
)
from pneumatic_backend.accounts.messages import (
    MSG_A_0008,
    MSG_A_0014,
)
from pneumatic_backend.utils.dates import date_format


pytestmark = pytest.mark.django_db


class TestAPIKeyGenerationView:

    def test_api_token_created(self, api_client, identify_mock):

        user = create_test_user()
        api_key = APIKey.objects.create(
            user=user,
            name=user.get_full_name(),
            account_id=user.account_id,
            key=PneumaticToken.create(user, for_api_key=True)
        )

        api_client.token_authenticate(user)
        response = api_client.get('/accounts/api-key')

        token = response.data.get('token')
        assert api_key.key == token


class TestUnsubscribeDigestView:

    def test_unsubscribe_ok(self, mocker, api_client):
        user = create_test_user()
        token = str(DigestUnsubscribeToken.for_user(user))
        response_content = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0014}
        """
        analytics_mock = mocker.patch(
            'pneumatic_backend.accounts.views.unsubscribes.'
            'AnalyticService.users_digest'
        )

        # act
        response = api_client.get(
            f'/accounts/digest/unsubscribe?token={token}',
        )

        assert response.status_code == 200
        assert response.content == bytes(response_content, 'UTF-8')

        user.refresh_from_db()
        assert user.is_digest_subscriber is False
        analytics_mock.assert_called_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )

    def test_unsub_incorrect_token(self, api_client):
        user = create_test_user()
        response = api_client.get('/accounts/digest/unsubscribe?token=12345')
        response_message = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0008}
        """

        assert response.status_code == 200
        assert response.content == bytes(response_message, 'UTF-8')

        user.refresh_from_db()
        assert user.is_digest_subscriber is True

    def test_unsub_no_token(self, api_client):
        user = create_test_user()
        response_message = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0008}
        """

        response = api_client.get('/accounts/digest/unsubscribe')

        assert response.status_code == 200
        assert response.content == bytes(response_message, 'UTF-8')

        user.refresh_from_db()
        assert user.is_digest_subscriber is True


class TestUnsubscribeEmailView:
    @pytest.mark.parametrize(
        'email_type', [
            MailoutType.TASKS_DIGEST,
            MailoutType.WF_DIGEST,
            MailoutType.COMMENTS,
            MailoutType.NEW_TASK,
        ]
    )
    def test_unsub(
        self,
        api_client,
        email_type,
    ):
        # arrange
        user = create_test_user()
        token = str(UnsubscribeEmailToken.create_token(
            user_id=user.id,
            email_type=email_type,
        ))
        response_content = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0014}
        """

        # act
        response = api_client.get(
            f'/accounts/emails/unsubscribe?token={token}',
        )

        assert response.status_code == 200
        assert response.content == bytes(response_content, 'UTF-8')

        user.refresh_from_db()
        attribute = MailoutType.MAP[email_type]
        assert getattr(user, attribute, None) is False

    def test_unsub_incorrect_token(self, api_client):
        # arrange
        user = create_test_user()
        response_message = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0008}
        """

        # act
        response = api_client.get('/accounts/emails/unsubscribe?token=12345')

        # assert
        assert response.status_code == 200
        assert response.content == bytes(response_message, 'UTF-8')

        user.refresh_from_db()
        assert user.is_digest_subscriber is True
        assert user.is_tasks_digest_subscriber is True
        assert user.is_comments_mentions_subscriber is True
        assert user.is_new_tasks_subscriber is True
        assert user.is_complete_tasks_subscriber is True
        assert user.is_newsletters_subscriber is True
        assert user.is_special_offers_subscriber is True

    def test_unsub_no_token(self, api_client):
        # arrange
        user = create_test_user()
        response_message = f"""
        <script>
            setTimeout("location.href = '{settings.FRONTEND_URL}';",3000);
        </script>
        {MSG_A_0008}
        """

        # act
        response = api_client.get('/accounts/emails/unsubscribe')

        # assert
        assert response.status_code == 200
        assert response.content == bytes(response_message, 'UTF-8')

        user.refresh_from_db()
        assert user.is_digest_subscriber is True
        assert user.is_tasks_digest_subscriber is True
        assert user.is_comments_mentions_subscriber is True
        assert user.is_new_tasks_subscriber is True
        assert user.is_complete_tasks_subscriber is True
        assert user.is_newsletters_subscriber is True
        assert user.is_special_offers_subscriber is True


class TestUserNotifications:

    def test_list__type_comment__ok(self, api_client):

        # arrange
        user = create_test_user()
        user_author = create_test_user(
            email='t@t.t',
            account=user.account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        notification = Notification.objects.create(
            task_id=task.id,
            user_id=user.id,
            account_id=user.account.id,
            type=NotificationType.COMMENT,
            text='text',
            author_id=user_author.id
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/accounts/notifications')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        data = response.data[0]
        assert data['id'] == notification.id
        assert data['text'] == notification.text
        assert data['type'] == notification.type
        assert data['datetime'] == (
            notification.datetime.strftime(date_format)
        )
        assert data['datetime_tsp'] == notification.datetime.timestamp()
        assert data['status'] == notification.status
        assert data['author'] == user_author.id
        assert data['task']['id'] == task.id
        assert data['task']['name'] == task.name
        assert data['workflow']['id'] == workflow.id
        assert data['workflow']['name'] == workflow.name

    def test_list__type_delay__ok(self, api_client):

        # arrange
        user = create_test_user()
        user_author = create_test_user(
            email='t@t.t',
            account=user.account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=timedelta(days=1)
        )
        notification = Notification.objects.create(
            task_id=task.id,
            user_id=user.id,
            account_id=user.account.id,
            type=NotificationType.DELAY_WORKFLOW,
            text='text',
            author_id=user_author.id
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/accounts/notifications')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        data = response.data[0]
        assert data['id'] == notification.id
        assert data['text'] == notification.text
        assert data['type'] == notification.type
        assert data['datetime'] == (
            notification.datetime.strftime(date_format)
        )
        assert data['datetime_tsp'] == notification.datetime.timestamp()
        assert data['status'] == notification.status
        assert data['author'] == user_author.id
        assert data['workflow']['id'] == workflow.id
        assert data['workflow']['name'] == workflow.name
        assert data['task']['id'] == task.id
        assert data['task']['name'] == task.name
        assert data['task']['delay']['estimated_end_date'] == (
            delay.estimated_end_date.strftime(date_format)
        )
        assert data['task']['delay']['estimated_end_date_tsp'] == (
            delay.estimated_end_date.timestamp()
        )
        assert data['task']['delay']['duration'] == '1 00:00:00'

    def test_list__type_delay_resumed__ok(self, api_client):

        # arrange
        user = create_test_user()
        user_author = create_test_user(
            email='t@t.t',
            account=user.account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            end_date=(timezone.now() + timedelta(hours=2)),
            duration=timedelta(days=1)
        )
        delay = Delay.objects.create(
            task=task,
            start_date=timezone.now(),
            duration=timedelta(hours=1),
            end_date=(timezone.now() + timedelta(seconds=5)),
        )
        Notification.objects.create(
            task_id=task.id,
            user_id=user.id,
            account_id=user.account.id,
            type=NotificationType.DELAY_WORKFLOW,
            text='text',
            author_id=user_author.id
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/accounts/notifications')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        data = response.data[0]
        assert data['task']['delay']['estimated_end_date'] == (
            delay.estimated_end_date.strftime(date_format)
        )
        assert data['task']['delay']['estimated_end_date_tsp'] == (
            delay.estimated_end_date.timestamp()
        )
        assert data['task']['delay']['duration'] == '01:00:00'

    def test_list__type_due_date_changed__ok(self, api_client):

        # arrange
        user = create_test_user()
        user_author = create_test_user(
            email='t@t.t',
            account=user.account,
            is_account_owner=False
        )
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        task.due_date = timezone.now() + timedelta(hours=1)
        task.save(update_fields=['due_date'])

        notification = Notification.objects.create(
            task_id=task.id,
            user_id=user.id,
            account_id=user.account.id,
            type=NotificationType.DUE_DATE_CHANGED,
            author_id=user_author.id
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/accounts/notifications')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        data = response.data[0]
        assert data['id'] == notification.id
        assert data['type'] == NotificationType.DUE_DATE_CHANGED
        assert data['datetime'] == (
            notification.datetime.strftime(date_format)
        )
        assert data['datetime_tsp'] == notification.datetime.timestamp()
        assert data['author'] == user_author.id
        assert data['status'] == NotificationStatus.NEW
        assert data['task']['id'] == task.id
        assert data['task']['name'] == task.name
        str_due_date = task.due_date.strftime(date_format)
        assert data['task']['due_date'] == str_due_date
        assert data['workflow']['id'] == workflow.id
        assert data['workflow']['name'] == workflow.name

    def test_list__pagination__return_first_page(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        notification_1 = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )
        notification_1.datetime = datetime.now() + timedelta(seconds=1)
        notification_1.save()
        notification_2 = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )
        notification_2.datetime = datetime.now() + timedelta(seconds=2)
        notification_2.save()
        notification_3 = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )
        notification_3.datetime = datetime.now() + timedelta(seconds=3)
        notification_3.save()

        # act
        response = api_client.get(
            '/accounts/notifications',
            data={
              'limit': 1,
              'offset': 1,
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 3
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == notification_2.id

    def test_list__filter_new__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
            status=NotificationStatus.READ
        )
        notification = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )

        # act
        response = api_client.get(
            '/accounts/notifications',
            data={'status': NotificationStatus.NEW}
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == notification.id

    def test_count__filter_new__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
            status=NotificationStatus.READ
        )
        Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )

        # act
        response = api_client.get(
            '/accounts/notifications/count',
            data={'status': NotificationStatus.NEW}
        )

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_list__ordering_datetime_desc__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
            status=NotificationStatus.READ
        )
        notification = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )

        # act
        response = api_client.get(
            '/accounts/notifications?ordering=-datetime'
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == notification.id

    def test_list__ordering_datetime_asc__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        notification = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )
        Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )

        # act
        response = api_client.get('/accounts/notifications?ordering=datetime')
        assert response.status_code == 200
        assert response.data[0]['id'] == notification.id

    def test_delete__ok(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        notification = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )

        # act
        response = api_client.delete(
            f'/accounts/notifications/{notification.id}'
        )

        # assert
        assert response.status_code == 204
        assert Notification.objects.filter(
            id=notification.id
        ).exists() is False

    def test_delete__not_exist_notification__not_found(self, api_client):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.delete('/accounts/notifications/99999')

        # assert
        assert response.status_code == 404

    def test_list__not_authorized_user__unauthorized(self, api_client):

        # act
        response = api_client.get('/accounts/notifications')

        # assert
        assert response.status_code == 401


class TestNotificationsReadView:

    def test_read(self, api_client):

        # arrange
        user = create_test_user()
        n1 = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
            status=NotificationStatus.READ
        )
        n2 = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.SYSTEM,
        )
        n3 = Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.COMMENT,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/notifications/read',
            data={
                'notifications': [n1.id, n2.id, n3.id]
            }
        )

        # assert
        assert response.status_code == 204
        assert user.notifications.exclude_read().exists() is False

    def test_read__empty_list__ok(self, api_client):

        # arrange
        user = create_test_user()
        Notification.objects.create(
            user=user,
            account=user.account,
            type=NotificationType.COMMENT,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.post(
            '/accounts/notifications/read',
            data={
                'notifications': []
            }
        )

        # assert
        assert response.status_code == 204
        assert user.notifications.exclude_read().count() == 1

    def test_read__not_authorized_user__unauthorized(self, api_client):
        # act
        response = api_client.post('/accounts/notifications/read')

        # assert
        assert response.status_code == 401
