import pytest
from src.logs.service import AccountLogService
from src.logs.enums import (
    AccountEventStatus,
    AccountEventType,
    RequestDirection,
)
from src.processes.tests.fixtures import (
    create_test_user
)

pytestmark = pytest.mark.django_db


def test_create_instance():

    # arrange
    user = create_test_user()
    scheme = 'https'
    method = 'GET'
    title = 'Some title'
    path = 'https://graph.microsoft.com/v1.0/users?'
    http_status = 500
    status = AccountEventStatus.FAILED
    response_data = {
        'created_contacts': ["daria2@pneumatic.app"],
        'updated_contacts': [
            "potter@pneumatic.app",
            "daria.test@pneumatic.com",
        ],
        'users_data': {
            '@odata.context': "https://graph.lName,userType,creationType",
            'value': [
                {'id': 'e8d1dc71-123d-bd527526ee92', }
            ]
        }
    }
    request_data = {
      "body": "Workflow: 04",
      "method": "new_task",
      "performer": (123,),
      "title": "You have a new task"
    }
    contractor = 'Some contractor'
    direction = RequestDirection.SENT

    service = AccountLogService()

    # act
    service._create_instance(
        event_type=AccountEventType.API,
        scheme=scheme,
        method=method,
        title=title,
        path=path,
        http_status=http_status,
        status=status,
        user_id=user.id,
        account_id=user.account_id,
        request_data=request_data,
        response_data=response_data,
        direction=direction,
        contractor=contractor,
    )

    # assert
    event = service.instance
    assert event.title == title
    assert event.scheme == scheme
    assert event.path == path
    assert event.http_status == http_status
    assert event.status == status
    assert event.user_id == user.id
    assert event.account_id == user.account_id
    assert event.request_data == request_data
    assert event.response_data == response_data
    assert event.direction == direction
    assert event.contractor == contractor
