from datetime import timedelta

import pytest
from django.utils import timezone

from src.accounts.enums import (
    NotificationStatus,
    NotificationType,
)
from src.accounts.models import Notification
from src.accounts.serializers.notifications import (
    NotificationTaskSerializer,
    NotificationWorkflowSerializer,
)
from src.processes.models.workflows.task import (
    Delay,
)
from src.processes.tests.fixtures import (
    create_test_not_admin,
    create_test_owner,
    create_test_workflow,
)
from src.utils.dates import date_format

pytestmark = pytest.mark.django_db


def test_list__type_comment__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    user_author = create_test_not_admin(
        email='author@test.com',
        account=user.account,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    notification = Notification.objects.create(
        task_json=NotificationTaskSerializer(
            instance=task,
            notification_type=NotificationType.COMMENT,
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data,
        user_id=user.id,
        account_id=user.account.id,
        type=NotificationType.COMMENT,
        text='text',
        author_id=user_author.id,
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
    assert data['datetime_tsp'] == (
        notification.datetime.timestamp()
    )
    assert data['status'] == notification.status
    assert data['author'] == user_author.id
    assert data['task']['id'] == task.id
    assert data['task']['name'] == task.name
    assert data['workflow']['id'] == workflow.id
    assert data['workflow']['name'] == workflow.name


def test_list__type_delay__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    user_author = create_test_not_admin(
        email='author@test.com',
        account=user.account,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1),
        workflow=workflow,
    )
    notification = Notification.objects.create(
        task_json=NotificationTaskSerializer(
            instance=task,
            notification_type=(
                NotificationType.DELAY_WORKFLOW
            ),
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data,
        user_id=user.id,
        account_id=user.account.id,
        type=NotificationType.DELAY_WORKFLOW,
        text='text',
        author_id=user_author.id,
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
    assert data['datetime_tsp'] == (
        notification.datetime.timestamp()
    )
    assert data['status'] == notification.status
    assert data['author'] == user_author.id
    assert data['task']['id'] == task.id
    assert data['task']['name'] == task.name
    assert data['task']['delay']['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )
    assert data['task']['delay']['duration'] == '1 00:00:00'
    assert data['workflow']['id'] == workflow.id
    assert data['workflow']['name'] == workflow.name


def test_list__type_delay_resumed__ok(api_client, identify_mock, mocker):

    # arrange
    now = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=now)
    user = create_test_owner()
    user_author = create_test_not_admin(
        email='author@test.com',
        account=user.account,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        end_date=(timezone.now() + timedelta(hours=2)),
        duration=timedelta(days=1),
        workflow=workflow,
    )
    delay = Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(hours=1),
        workflow=workflow,
    )
    Notification.objects.create(
        task_json=NotificationTaskSerializer(
            instance=task,
            notification_type=(
                NotificationType.DELAY_WORKFLOW
            ),
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data,
        user_id=user.id,
        account_id=user.account.id,
        type=NotificationType.DELAY_WORKFLOW,
        text='text',
        author_id=user_author.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/notifications')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['task']['delay']['estimated_end_date_tsp'] == (
        delay.estimated_end_date.timestamp()
    )
    assert data['task']['delay']['duration'] == '01:00:00'


def test_list__type_due_date_changed__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    user_author = create_test_not_admin(
        email='author@test.com',
        account=user.account,
    )
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.first()
    task.due_date = timezone.now() + timedelta(hours=1)
    task.save(update_fields=['due_date'])
    notification = Notification.objects.create(
        task_json=NotificationTaskSerializer(
            instance=task,
            notification_type=(
                NotificationType.DUE_DATE_CHANGED
            ),
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data,
        user_id=user.id,
        account_id=user.account.id,
        type=NotificationType.DUE_DATE_CHANGED,
        author_id=user_author.id,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/notifications')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == notification.id
    assert data['type'] == (
        NotificationType.DUE_DATE_CHANGED
    )
    assert data['datetime'] == (
        notification.datetime.strftime(date_format)
    )
    assert data['datetime_tsp'] == (
        notification.datetime.timestamp()
    )
    assert data['author'] == user_author.id
    assert data['status'] == NotificationStatus.NEW
    assert data['task']['id'] == task.id
    assert data['task']['name'] == task.name
    assert data['task']['due_date_tsp'] == (
        task.due_date.timestamp()
    )
    assert data['workflow']['id'] == workflow.id
    assert data['workflow']['name'] == workflow.name


def test_list__pagination_offset__ok(api_client, identify_mock, mocker):

    # arrange
    now = timezone.now()
    mocker.patch('django.utils.timezone.now', return_value=now)
    user = create_test_owner()
    api_client.token_authenticate(user)
    notification_1 = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
    )
    notification_1.datetime = (
        timezone.now() + timedelta(seconds=1)
    )
    notification_1.save()
    notification_2 = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
    )
    notification_2.datetime = (
        timezone.now() + timedelta(seconds=2)
    )
    notification_2.save()
    notification_3 = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
    )
    notification_3.datetime = (
        timezone.now() + timedelta(seconds=3)
    )
    notification_3.save()

    # act
    response = api_client.get(
        '/accounts/notifications',
        data={
            'limit': 1,
            'offset': 1,
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == (
        notification_2.id
    )


def test_list__filter_new__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
        status=NotificationStatus.READ,
    )
    notification = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
    )

    # act
    response = api_client.get(
        '/accounts/notifications',
        data={'status': NotificationStatus.NEW},
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == notification.id


def test_list__ordering_datetime_desc__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
        status=NotificationStatus.READ,
    )
    notification = Notification.objects.create(
        user=user,
        account=user.account,
        type=NotificationType.SYSTEM,
    )

    # act
    response = api_client.get(
        '/accounts/notifications?ordering=-datetime',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == notification.id


def test_list__ordering_datetime_asc__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
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
    response = api_client.get(
        '/accounts/notifications?ordering=datetime',
    )

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == notification.id


def test_list__remove_task__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    user_author = create_test_not_admin(
        email='author@test.com',
        account=user.account,
    )
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=1),
        workflow=workflow,
    )
    notification = Notification.objects.create(
        task_json=NotificationTaskSerializer(
            instance=task,
            notification_type=(
                NotificationType.DELAY_WORKFLOW
            ),
        ).data,
        workflow_json=NotificationWorkflowSerializer(
            instance=task.workflow,
        ).data,
        user_id=user.id,
        account_id=user.account.id,
        type=NotificationType.DELAY_WORKFLOW,
        text='text',
        author_id=user_author.id,
    )
    task.delete()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/notifications')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data = response.data[0]
    assert data['id'] == notification.id
    assert data['task']['id'] == task.id
    assert data['task']['name'] == task.name


def test_list__not_authenticated__unauthorized(
    api_client,
    identify_mock,
):

    # arrange

    # act
    response = api_client.get('/accounts/notifications')

    # assert
    assert response.status_code == 401
