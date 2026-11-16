from datetime import timedelta

import pytest
from django.utils import timezone

from src.analysis.actions import WorkflowActions
from src.authentication.enums import AuthTokenType
from src.processes.messages import workflow as messages
from src.processes.tests.fixtures import (
    create_test_kickoff_field,
    create_test_owner,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_partial_update__name__audit_workflow_updated(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflow_updated_mock = mocker.patch(
        'src.processes.views.workflow.AuditEventService.workflow_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'name': 'Renamed workflow'},
    )

    # assert
    assert response.status_code == 200
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflow_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        update_kwargs={'name': 'Renamed workflow'},
    )


def test_partial_update__kickoff__audit_workflow_updated(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner)
    create_test_kickoff_field(
        workflow=workflow,
        name='Client',
        api_name='client',
    )
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflow_updated_mock = mocker.patch(
        'src.processes.views.workflow.AuditEventService.workflow_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'kickoff': {'client': 'Acme'}},
    )

    # assert
    assert response.status_code == 200
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflow_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        update_kwargs={'kickoff': {'client': 'Acme'}},
    )


def test_partial_update__due_date__audit_workflow_updated(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner)
    due_date = timezone.now().replace(microsecond=0) + timedelta(days=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflow_updated_mock = mocker.patch(
        'src.processes.views.workflow.AuditEventService.workflow_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'due_date_tsp': due_date.timestamp()},
    )

    # assert
    assert response.status_code == 200
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflow_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        update_kwargs={'due_date_tsp': due_date},
    )


def test_partial_update__is_urgent__audit_workflow_updated(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflows_urgent_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_urgent',
    )
    urgent_service_resolve_mock = mocker.patch(
        'src.processes.services.urgent.UrgentService.resolve',
    )
    workflow_updated_mock = mocker.patch(
        'src.processes.views.workflow.AuditEventService.workflow_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'is_urgent': True},
    )

    # assert
    assert response.status_code == 200
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflows_urgent_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
        action=WorkflowActions.marked,
    )
    urgent_service_resolve_mock.assert_called_once_with(
        workflow=workflow,
        user=owner,
        auth_type=AuthTokenType.USER,
    )
    workflow_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        update_kwargs={'is_urgent': True},
    )


def test_partial_update__empty_body__audit_with_empty_kwargs(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflow_updated_mock = mocker.patch(
        'src.processes.views.workflow.AuditEventService.workflow_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={},
    )

    # assert
    assert response.status_code == 200
    workflows_updated_mock.assert_called_once_with(
        workflow=workflow,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        user=owner,
    )
    workflow_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        workflow=workflow,
        update_kwargs={},
    )


def test_partial_update__due_date_in_past__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner)
    due_date = timezone.now() - timedelta(days=1)
    workflows_updated_mock = mocker.patch(
        'src.analysis.services.AnalyticService.workflows_updated',
    )
    workflow_updated_mock = mocker.patch(
        'src.processes.views.workflow.AuditEventService.workflow_updated',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.patch(
        f'/workflows/{workflow.id}',
        data={'due_date_tsp': due_date.timestamp()},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PW_0051
    assert response.data['details']['name'] == 'due_date_tsp'
    assert response.data['details']['reason'] == messages.MSG_PW_0051
    workflows_updated_mock.assert_not_called()
    workflow_updated_mock.assert_not_called()
