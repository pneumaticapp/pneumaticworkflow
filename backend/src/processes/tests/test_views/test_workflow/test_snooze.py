import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from src.analytics.customerio.tests.fixtures import \
    create_test_account
from src.processes.enums import (
    WorkflowStatus,
    OwnerType,
    TaskStatus,
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template, create_test_owner, create_test_admin
)
from src.processes.services.exceptions import (
    WorkflowActionServiceException
)
from src.utils.validation import ErrorCode
from src.processes.models import TemplateOwner
from src.generics.messages import MSG_GE_0007


pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test_snooze__body__ok(api_client):

    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': date.timestamp()}
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == workflow.id
    assert response.data['name'] == workflow.name
    assert response.data['status'] == WorkflowStatus.DELAYED
    assert response.data['description'] == workflow.description
    assert response.data['finalizable'] is False
    assert response.data['is_external'] is False
    assert response.data['is_urgent'] is False
    assert response.data['is_legacy_template'] is False
    assert response.data['legacy_template_name'] is None
    kickoff = workflow.kickoff_instance
    assert response.data['kickoff']['id'] == kickoff.id

    assert response.data['workflow_starter'] == user.id

    task_data = response.data['tasks'][0]
    assert task_data['id'] == task.id
    assert task_data['name'] == task.name
    assert task_data['api_name'] == task.api_name
    assert task_data['description'] == task.description
    assert task_data['number'] == task.number
    assert task_data['delay']['duration'] is not None
    assert task_data['delay']['start_date'] is not None
    assert task_data['delay']['end_date'] is None
    assert task_data['delay']['estimated_end_date']
    assert task_data['due_date_tsp'] is None
    assert task_data['date_started_tsp'] == task.date_started.timestamp()
    assert task_data['checklists_total'] == 0
    assert task_data['checklists_marked'] == 0
    assert task_data['status'] == TaskStatus.DELAYED
    assert task_data['performers'] == [
        {
            'source_id': user.id,
            'type': 'user',
            'is_completed': False,
            'date_completed_tsp': None,
        }
    ]
    template_data = response.data['template']
    assert template_data['id'] == workflow.template_id
    assert template_data['is_active'] == workflow.template.is_active
    assert template_data['name'] == workflow.template.name
    assert template_data['wf_name_template'] == (
        workflow.template.wf_name_template
    )
    assert response.data['owners'] == [user.id]


def test_snooze__template_owner_admin__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=False, is_admin=True)
    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)
    snooze_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': date.timestamp()}
    )

    # assert
    assert response.status_code == 200
    snooze_mock.assert_called_once_with(date=date)


def test_snooze__account_owner_admin__ok(
    mocker,
    api_client
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account)
    workflow = create_test_workflow(user, tasks_count=1)
    snooze_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    date = timezone.now() + timedelta(days=1)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': date.timestamp()}
    )

    # assert
    assert response.status_code == 200
    snooze_mock.assert_called_once_with(date=date)


def test_snooze__legacy_workflow_workflow_starter__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=False, is_admin=True)
    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)
    response_delete = api_client.delete(f'/templates/{workflow.template.id}')
    workflow.refresh_from_db()
    snooze_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': date.timestamp()}
    )

    # assert
    assert response_delete.status_code == 204
    assert response.status_code == 200
    snooze_mock.assert_called_once_with(date=date)
    assert response.data['id'] == workflow.id
    assert response.data['is_legacy_template'] is True


def test_snooze__template_owner__not_admin__permission_denied(
    mocker,
    api_client
):
    # arrange
    account_owner = create_test_user()
    user_not_admin = create_test_user(
        account=account_owner.account,
        is_admin=False,
        is_account_owner=False,
        email='t@t.t'
    )
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    TemplateOwner.objects.create(
        template=template,
        account=account_owner.account,
        type=OwnerType.USER,
        user_id=user_not_admin.id,
    )
    workflow = create_test_workflow(
        template=template,
        user=account_owner,
    )
    snooze_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    api_client.token_authenticate(user_not_admin)
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': date.timestamp()}
    )

    # assert
    assert response.status_code == 403
    snooze_mock.assert_not_called()


def test_snooze__invalid_date__validation_error(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)
    snooze_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    invalid_timestamp = 'invalid_timestamp_string'

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': invalid_timestamp}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_GE_0007
    assert response.data['details']['reason'] == MSG_GE_0007
    assert response.data['details']['name'] == 'date'
    snooze_mock.assert_not_called()


def test_snooze__service_exception__validation_error(
    mocker,
    api_client
):
    # arrange
    account_owner = create_test_user()
    user_admin = create_test_user(
        account=account_owner.account,
        is_admin=True,
        is_account_owner=False,
        email='t@t.t'
    )
    message = 'message'
    workflow = create_test_workflow(user_admin, tasks_count=1)
    api_client.token_authenticate(user_admin)
    snooze_mock = mocker.patch(
        'src.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow',
        side_effect=WorkflowActionServiceException(message)
    )
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': date.timestamp()}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    snooze_mock.assert_called_once_with(date=date)
