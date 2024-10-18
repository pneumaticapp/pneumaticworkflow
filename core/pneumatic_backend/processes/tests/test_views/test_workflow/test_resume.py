import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.services.exceptions import (
    WorkflowActionServiceException
)


pytestmark = pytest.mark.django_db
UserModel = get_user_model()


def test_resume__account_owner__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=True)
    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)
    resume_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_resume_workflow'
    )

    # act
    response = api_client.post(f'/workflows/{workflow.id}/resume')

    # assert
    assert response.status_code == 204
    resume_mock.assert_called_once_with(workflow=workflow)


def test_resume__template_owner_admin__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=False, is_admin=True)
    workflow = create_test_workflow(user, tasks_count=1)
    api_client.token_authenticate(user)
    resume_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_resume_workflow'
    )

    # act
    response = api_client.post(f'/workflows/{workflow.id}/resume')

    # assert
    assert response.status_code == 204
    resume_mock.assert_called_once_with(workflow=workflow)


def test_resume__template_owner__not_admin__permission_denied(
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
    resume_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_resume_workflow'
    )
    api_client.token_authenticate(user_not_admin)

    # act
    response = api_client.post(f'/workflows/{workflow.id}/resume')

    # assert
    assert response.status_code == 403
    resume_mock.assert_not_called()


def test_resume__service_exception__validation_error(
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
    resume_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.force_resume_workflow',
        side_effect=WorkflowActionServiceException(message)
    )

    # act
    response = api_client.post(f'/workflows/{workflow.id}/resume')

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    resume_mock.assert_called_once()
