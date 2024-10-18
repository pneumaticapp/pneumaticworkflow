import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_template,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.enums import (
    SysTemplateType,
)
from pneumatic_backend.processes.models import (
    SystemTemplate,
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    TemplateServiceException
)
from pneumatic_backend.processes.api_v2.services.templates.template import (
    TemplateService
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_by_name__account_owner__ok(mocker, api_client):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'Library template'
    system_template = SystemTemplate.objects.create(
        name=name,
        type=SysTemplateType.LIBRARY,
        template={},
        is_active=True
    )
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    template = create_test_template(user, tasks_count=1)
    create_template_from_library_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_from_library_template',
        return_value=template
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates/by-name',
        data={'name': name}
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
    create_template_from_library_template_mock.assert_called_once_with(
        system_template=system_template
    )


def test_by_name__admin__ok(
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
    name = 'Library template'
    system_template = SystemTemplate.objects.create(
        name=name,
        type=SysTemplateType.LIBRARY,
        template={},
        is_active=True
    )
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    template = create_test_template(user)
    create_template_from_library_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_from_library_template',
        return_value=template
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-name',
        data={'name': name}
    )

    # assert
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    create_template_from_library_template_mock.assert_called_once_with(
        system_template=system_template
    )


def test_by_name__request_user_is_not_authenticated__permission_denied(
    mocker,
    api_client
):

    # arrange
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    create_template_from_library_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_from_library_template'
    )

    # act
    response = api_client.post(
        path=f'/templates/by-name',
        data={
            'name': 'some name',
        }
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    create_template_from_library_template_mock.assert_not_called()


def test_by_name__not_found__return_404(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(user)
    sentry_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'capture_sentry_message'
    )

    # act
    response = api_client.post(
        path=f'/templates/by-name',
        data={
            'name': 'Not existent',
        }
    )

    # assert
    assert response.status_code == 404
    service_init_mock.assert_not_called()
    sentry_mock.assert_called_once()


def test_by_name__name_null__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = None
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-name',
        data={
            'name': name,
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


def test_by_name__name_blank__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = ''
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/by-name',
        data={
            'name': name,
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


def test_by_name__service_exception__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(is_account_owner=True)
    name = 'Library template'
    system_template = SystemTemplate.objects.create(
        name=name,
        type=SysTemplateType.LIBRARY,
        template={},
        is_active=True
    )
    service_init_mock = mocker.patch.object(
        TemplateService,
        attribute='__init__',
        return_value=None
    )
    error_message = 'some message'
    create_template_from_library_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'template.TemplateService.create_template_from_library_template',
        side_effect=TemplateServiceException(message=error_message)
    )
    api_client.token_authenticate(user)

    response = api_client.post(
        path='/templates/by-name',
        data={
            'name': name,
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
    create_template_from_library_template_mock.assert_called_once_with(
        system_template=system_template,
    )
