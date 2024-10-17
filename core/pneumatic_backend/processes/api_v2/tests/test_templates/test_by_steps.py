import pytest
from pneumatic_backend.processes.consts import TEMPLATE_NAME_LENGTH
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_template,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.models import (
    TaskTemplate,
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    TemplateServiceException
)
from pneumatic_backend.processes.api_v2.services.templates.template import (
    TemplateService
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_create__account_owner__ok(mocker, api_client):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'My unbelievable processes name'
    tasks = [
        {
          "number": 1,
          "name": 'Step 1',
          "description": 'some desc'
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    template = create_test_template(user, tasks_count=1)
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps',
        return_value=template
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 200
    data = response.data
    assert data.get('id')
    assert data['name'] == template.name
    assert data['description'] == template.description
    assert data['template_owners'] == [user.id]
    assert data['is_active'] == template.is_active
    assert len(data['tasks']) == 1

    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    create_template_by_steps_mock.assert_called_once_with(
        name=name,
        tasks=tasks
    )


def test_create__admin__ok(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    create_test_user(
        is_account_owner=True,
        account=account,
        email='owner@test.test'
    )
    user = create_test_user(
        is_admin=True,
        is_account_owner=False,
        account=account
    )
    name = 'My unbelievable processes name'
    tasks = [
        {
          "number": 1,
          "name": 'Step 1',
          "description": 'some desc'
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    template = create_test_template(user, tasks_count=1)
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps',
        return_value=template
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    create_template_by_steps_mock.assert_called_once_with(
        name=name,
        tasks=tasks
    )


def test_create__request_user_is_not_authenticated__permission_denied(
    mocker,
    api_client
):

    # arrange
    name = 'My unbelievable processes name'
    tasks = [
        {
            "number": 1,
            "name": 'Step 1',
            "description": 'some desc'
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps'
    )

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()


def test_create__task_over_limit__cut_to_max_len(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'c' * (TEMPLATE_NAME_LENGTH + 2)
    tasks = [
        {
          "number": 1,
          "name": 'b' * (TaskTemplate.NAME_MAX_LENGTH + 2),
          "description": 'a' * 502
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    template = create_test_template(user)
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps',
        return_value=template
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    create_template_by_steps_mock.assert_called_once_with(
        name='c' * TEMPLATE_NAME_LENGTH,
        tasks=[
            {
              "number": 1,
              "name": 'b' * TaskTemplate.NAME_MAX_LENGTH,
              "description": 'a' * 500
            }
        ]
    )


def test_create__task_description_null__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'My unbelievable processes name'
    tasks = [
        {
          "number": 1,
          "name": 'Step 1',
          "description": None
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'tasks'
    service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()


def test_create__task_description_blank__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'My unbelievable processes name'
    tasks = [
        {
          "number": 1,
          "name": 'Step 1',
          "description": ''
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'tasks'
    service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()


@pytest.mark.parametrize('description', ([], {}))
def test_create__task_description__invalid_value__validation_error(
    description,
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'My unbelievable processes name'
    tasks = [
        {
          "number": 1,
          "name": 'Step 1',
          "description": description
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 400
    message = 'Not a valid string.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'tasks'
    service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()


def test_create__task_name_null__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'My unbelievable processes name'
    tasks = [
        {
          "number": 1,
          "name": None,
          "description": 'desc'
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'tasks'
    service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()


def test_create__task_name_blank__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'My unbelievable processes name'
    tasks = [
        {
          "number": 1,
          "name": '',
          "description": 'desc'
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()


def test_create__name_null__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = None
    tasks = [
        {
          "number": 1,
          "name": 'Step 1',
          "description": 'desc'
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'name'
    service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()


def test_create__name_blank__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = ''
    tasks = [
        {
          "number": 1,
          "name": 'Step 1',
          "description": 'desc'
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'name'
    service_init_mock.assert_not_called()
    create_template_by_steps_mock.assert_not_called()


def test_create__service_exception__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'My unbelievable processes name'
    tasks = [
        {
            "number": 1,
            "name": 'Step 1',
            "description": 'value'
        }
    ]
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    error_message = 'some message'
    create_template_by_steps_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_by_steps',
        side_effect=TemplateServiceException(message=error_message)
    )
    api_client.token_authenticate(user)

    response = api_client.post(
        path=f'/templates/by-steps',
        data={
            'name': name,
            'tasks': tasks
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    create_template_by_steps_mock.assert_called_once_with(
        name=name,
        tasks=tasks
    )
