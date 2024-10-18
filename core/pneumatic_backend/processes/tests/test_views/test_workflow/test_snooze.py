import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.enums import WorkflowStatus
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template
)
from pneumatic_backend.processes.services.exceptions import (
    WorkflowActionServiceException
)
from pneumatic_backend.processes.models import Delay
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test_snooze__account_owner__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(user, tasks_count=1)
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])
    task = workflow.current_task_instance
    Delay.objects.create(
        task=task,
        start_date=timezone.now(),
        duration=timedelta(days=7)
    )
    task = workflow.current_task_instance
    api_client.token_authenticate(user)
    snooze_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': str(date)}
    )

    # assert
    assert response.status_code == 200
    snooze_mock.assert_called_once_with(
        workflow=workflow,
        date=date
    )
    assert response.data['id'] == workflow.id
    assert response.data['name'] == workflow.name
    assert response.data['status'] == workflow.status
    assert response.data['tasks_count'] == 1
    assert response.data['description'] == workflow.description
    assert response.data['passed_tasks'] == []
    assert response.data['finalizable'] is False
    assert response.data['date_completed'] is None
    assert response.data['is_external'] is False
    assert response.data['is_urgent'] is False
    assert response.data['is_legacy_template'] is False
    assert response.data['legacy_template_name'] is None
    kickoff = workflow.kickoff_instance
    assert response.data['kickoff']['id'] == kickoff.id
    assert response.data['kickoff']['description'] == kickoff.description

    assert response.data['workflow_starter'] == user.id

    assert response.data['current_task']['id'] == task.id
    assert response.data['current_task']['name'] == task.name
    assert response.data['current_task']['number'] == task.number
    assert response.data['current_task']['due_date'] is None
    assert response.data['current_task']['date_started'] is not None
    assert response.data['current_task']['performers'] == [user.id]
    assert response.data['current_task']['checklists_total'] == 0
    assert response.data['current_task']['checklists_marked'] == 0
    assert response.data['current_task']['delay']['duration'] == (
        '7 00:00:00'
    )
    assert response.data['current_task']['delay']['start_date'] is not None
    assert response.data['current_task']['delay']['end_date'] is None
    assert response.data['current_task']['delay']['estimated_end_date']
    template_data = response.data['template']
    assert template_data['id'] == workflow.template.id
    assert template_data['is_active'] == workflow.template.is_active
    assert template_data['name'] == workflow.get_template_name()
    assert template_data['template_owners'] == [user.id]


def test_snooze__template_owner_admin__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=False, is_admin=True)
    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)
    snooze_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': str(date)}
    )

    # assert
    assert response.status_code == 200
    snooze_mock.assert_called_once_with(
        workflow=workflow,
        date=date
    )


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
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': str(date)}
    )

    # assert
    assert response_delete.status_code == 204
    assert response.status_code == 200
    snooze_mock.assert_called_once_with(
        workflow=workflow,
        date=date
    )
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
    template.template_owners.add(user_not_admin)
    workflow = create_test_workflow(
        template=template,
        user=account_owner,
    )
    snooze_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    api_client.token_authenticate(user_not_admin)
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': str(date)}
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
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow'
    )
    date = '2000/20/01'

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': str(date)}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == (
        'Datetime has wrong format. Use one of these formats instead:'
        ' YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'
    )
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
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_delay_workflow',
        side_effect=WorkflowActionServiceException(message)
    )
    date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/snooze',
        data={'date': str(date)}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    snooze_mock.assert_called_once()
