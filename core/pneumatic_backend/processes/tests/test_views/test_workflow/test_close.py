import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
    create_test_account
)
from pneumatic_backend.processes.models import (
    TemplateOwner,
)
from pneumatic_backend.processes.enums import (
    OwnerType
)
from pneumatic_backend.processes.services.exceptions import (
    WorkflowActionServiceException
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test_close__account_owner__ok(
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
    response = api_client.post(
        f'/workflows/{workflow.id}/close',
    )

    # assert
    assert response.status_code == 204
    terminate_mock.assert_called_once_with()


def test_close__template_owner_admin__ok(
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
    response = api_client.post(
        f'/workflows/{workflow.id}/close',
    )

    # assert
    assert response.status_code == 204
    terminate_mock.assert_called_once_with()


def test_close__legacy_workflow_workflow_starter__ok(
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
    response = api_client.post(
        f'/workflows/{workflow.id}/close',
    )

    # assert
    assert response_delete.status_code == 204
    assert response.status_code == 204
    terminate_mock.assert_called_once_with()
    assert workflow.is_legacy_template is True


def test_close__template_owner__not_admin__permission_denied(
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
    terminate_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.terminate_workflow'
    )
    api_client.token_authenticate(user_not_admin)

    # act
    response = api_client.post(
        f'/workflows/{workflow.id}/close',
    )

    # assert
    assert response.status_code == 403
    terminate_mock.assert_not_called()


def test_close__service_exception__validation_error(
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
    response = api_client.post(
        f'/workflows/{workflow.id}/close',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    terminate_mock.assert_called_once()
