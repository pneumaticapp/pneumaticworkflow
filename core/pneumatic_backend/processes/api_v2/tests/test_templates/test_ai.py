import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.services.templates.ai import (
    OpenAiService
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    OpenAiServiceException
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_create__account_owner__ok(mocker, api_client):

    # arrange
    user = create_test_user(is_account_owner=True, is_admin=False)
    description = 'My unbelievable processes name'
    template_data = {'name': description}
    service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService.get_template_data',
        return_value=template_data
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AIPermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/ai',
        data={'description': description}
    )

    # assert
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        ident=user.id,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    get_template_data_mock.assert_called_once_with(
        user_description=description
    )


def test_create__admin__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_account_owner=False, is_admin=True)
    description = 'My unbelievable processes name'
    template_data = {'name': description}
    service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService.get_template_data',
        return_value=template_data
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AIPermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/ai',
        data={'description': description}
    )

    # assert
    assert response.status_code == 200
    service_init_mock.assert_called_once_with(
        ident=user.id,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    get_template_data_mock.assert_called_once_with(
        user_description=description
    )


def test_create__request_user_is_not_authenticated__permission_denied(
    mocker,
    api_client
):
    # arrange
    description = 'My unbelievable processes name'
    template_data = {'name': description}
    service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService.get_template_data',
        return_value=template_data
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AIPermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.post(
        path=f'/templates/ai',
        data={'description': description}
    )

    # assert
    assert response.status_code == 401
    service_init_mock.asert_not_called()
    get_template_data_mock.asert_not_called()


def test_create__user_not_admin__permission_denied(
    mocker,
    api_client
):
    # arrange
    user = create_test_user(is_admin=False, is_account_owner=False)
    description = 'My unbelievable processes name'
    template_data = {'name': description}
    service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService.get_template_data',
        return_value=template_data
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AIPermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/ai',
        data={'description': description}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.asert_not_called()
    get_template_data_mock.asert_not_called()


def test_create__description_over_limit__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    description = 'o'*501
    service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService.get_template_data'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AIPermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/ai',
        data={'description': description}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'Ensure this field has no more than 500 characters.'
    assert str(response.data['message']) == message
    service_init_mock.assert_not_called()
    get_template_data_mock.assert_not_called()


def test_create__description_null__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService.get_template_data'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AIPermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/ai',
        data={'description': None}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'This field may not be null.'
    assert str(response.data['message']) == message
    service_init_mock.assert_not_called()
    get_template_data_mock.assert_not_called()


@pytest.mark.parametrize('description', ('', [], {}))
def test_create__description__invalid_value__validation_error(
    description,
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService.get_template_data'
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AIPermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/ai',
        data={'description': description}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    service_init_mock.assert_not_called()
    get_template_data_mock.assert_not_called()


def test_create__service_exception__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    description = 'My unbelievable processes name'
    service_init_mock = mocker.patch.object(
        OpenAiService,
        attribute='__init__',
        return_value=None
    )
    error_message = 'error message'
    get_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.OpenAiService.get_template_data',
        side_effect=OpenAiServiceException(message=error_message)
    )
    mocker.patch(
        'pneumatic_backend.processes.api_v2.views.template.'
        'AIPermission.has_permission',
        return_value=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path=f'/templates/ai',
        data={'description': description}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    service_init_mock.assert_called_once_with(
        ident=user.id,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    get_template_data_mock.assert_called_once_with(
        user_description=description
    )
