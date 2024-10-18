import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
    create_test_account
)
from pneumatic_backend.processes.services.exceptions import (
    WorkflowActionServiceException
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test_delete__account_owner__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)
    terminate_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow'
    )

    # act
    response = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 204
    terminate_mock.assert_called_once_with(workflow=workflow)


def test_delete__template_owner_admin__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=False, is_admin=True)
    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)
    terminate_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow'
    )

    # act
    response = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 204
    terminate_mock.assert_called_once_with(workflow=workflow)


def test_delete__legacy_workflow_workflow_starter__ok(
    mocker,
    api_client
):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    account_owner = create_test_user(
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        email='t@t.t',
        is_account_owner=False,
        is_admin=True
    )

    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(account_owner)
    response_delete = api_client.delete(f'/templates/{workflow.template.id}')
    workflow.refresh_from_db()
    terminate_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert response_delete.status_code == 204
    assert response.status_code == 204
    terminate_mock.assert_called_once_with(workflow=workflow)
    assert workflow.is_legacy_template is True


def test_delete__template_owner_not_admin__permission_denied(
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
    terminate_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow'
    )
    api_client.token_authenticate(user_not_admin)

    # act
    response = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 403
    terminate_mock.assert_not_called()


def test_delete__service_exception__validation_error(
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
    terminate_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow',
        side_effect=WorkflowActionServiceException(message)
    )

    # act
    response = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    terminate_mock.assert_called_once()


def test_delete__not_authenticated__permission_denied(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(user)
    terminate_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow'
    )

    # act
    response = api_client.delete(f'/workflows/{workflow.id}')

    # assert
    assert response.status_code == 401
    message = 'Authentication credentials were not provided.'
    assert response.data['detail'] == message
    terminate_mock.assert_not_called()


def test_delete__not_workflow__not_found(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = 1
    api_client.token_authenticate(user)
    terminate_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow'
    )

    # act
    response = api_client.delete(f'/workflows/{workflow}')

    # assert
    assert response.status_code == 404
    terminate_mock.assert_not_called()
