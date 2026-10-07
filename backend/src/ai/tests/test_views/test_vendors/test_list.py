import pytest

from src.ai.enums import AIVendor
from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_list__ok(api_client):

    """ List ok """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    expected = [
        {'slug': code, 'name': name}
        for code, name in AIVendor.CHOICES
    ]
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path='/ai/vendors',
    )

    # assert
    assert response.status_code == 200
    assert response.data == expected


def test_list__non_admin__ok(api_client):

    """ Non-admin user """

    # arrange
    account = create_test_account()
    user = create_test_not_admin(account=account)
    expected = [
        {'slug': code, 'name': name}
        for code, name in AIVendor.CHOICES
    ]
    api_client.token_authenticate(user=user)

    # act
    response = api_client.get(
        path='/ai/vendors',
    )

    # assert
    assert response.status_code == 200
    assert response.data == expected


def test_list__unauthenticated__unauthorized(api_client):

    """ Unauthenticated """

    # arrange
    message = 'Authentication credentials were not provided.'

    # act
    response = api_client.get(
        path='/ai/vendors',
    )

    # assert
    assert response.status_code == 401
    assert response.data['detail'] == message


def test_list__guest__permission_denied(api_client):

    """ Guest user """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )
    path = '/ai/vendors'
    message = 'You do not have permission to perform this action.'
    headers = {
        'X-Guest-Authorization': str_token,
    }

    # act
    response = api_client.get(
        path=path,
        **headers,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == message
