import pytest
from pneumatic_backend.processes.api_v2.services.templates.ai import (
    AnonOpenAiService
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    OpenAiServiceException
)
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_create__not_auth__ok(mocker, api_client):

    # arrange
    user_ip = '1.2.3.4'
    get_ip_mock = mocker.patch(
        'pneumatic_backend.services.views.ServicesViewSet.get_user_ip',
        return_value=user_ip
    )
    user_agent = 'Some agent'
    get_user_agent_mock = mocker.patch(
        'pneumatic_backend.services.views.ServicesViewSet.get_user_agent',
        return_value=user_agent
    )
    service_init_mock = mocker.patch.object(
        AnonOpenAiService,
        attribute='__init__',
        return_value=None
    )
    description = 'My unbelievable processes name'
    template_data = {'name': description}
    get_short_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService.get_short_template_data',
        return_value=template_data
    )
    mocker.patch(
        'pneumatic_backend.services.views.AIPermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.get(
        path=f'/services/steps-by-description?description={description}'
    )

    # assert
    assert response.status_code == 200
    get_ip_mock.assert_called_once()
    get_user_agent_mock.assert_called_once()
    service_init_mock.assert_called_once_with(
        ident=user_ip,
        user_agent=user_agent,
    )
    get_short_template_data_mock.assert_called_once_with(
        user_description=description
    )


def test_create__description_over_limit__validation_error(
    mocker,
    api_client
):

    # arrange
    description = 'o'*501
    service_init_mock = mocker.patch.object(
        AnonOpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_short_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService.get_short_template_data'
    )
    mocker.patch(
        'pneumatic_backend.services.views.AIPermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.get(
        path=f'/services/steps-by-description?description={description}'
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    message = 'Ensure this field has no more than 500 characters.'
    assert str(response.data['message']) == message
    service_init_mock.assert_not_called()
    get_short_template_data_mock.assert_not_called()


@pytest.mark.parametrize('description', ('', [], {}))
def test_create__description__invalid_value__validation_error(
    description,
    mocker,
    api_client
):

    # arrange
    service_init_mock = mocker.patch.object(
        AnonOpenAiService,
        attribute='__init__',
        return_value=None
    )
    get_short_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService.get_short_template_data'
    )
    mocker.patch(
        'pneumatic_backend.services.views.AIPermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.get(
        path=f'/services/steps-by-description',
        data={'description': description}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    service_init_mock.assert_not_called()
    get_short_template_data_mock.assert_not_called()


def test_create__service_exception__validation_error(
    mocker,
    api_client
):

    # arrange
    user_ip = '1.2.3.4'
    get_ip_mock = mocker.patch(
        'pneumatic_backend.services.views.ServicesViewSet.get_user_ip',
        return_value=user_ip
    )
    user_agent = 'Some agent'
    get_user_agent_mock = mocker.patch(
        'pneumatic_backend.services.views.ServicesViewSet.get_user_agent',
        return_value=user_agent
    )
    description = 'My unbelievable processes name'
    service_init_mock = mocker.patch.object(
        AnonOpenAiService,
        attribute='__init__',
        return_value=None
    )
    error_message = 'error message'
    get_short_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService.get_short_template_data',
        side_effect=OpenAiServiceException(message=error_message)
    )
    mocker.patch(
        'pneumatic_backend.services.views.AIPermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.get(
        path=f'/services/steps-by-description?description={description}'
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    get_ip_mock.assert_called_once()
    get_user_agent_mock.assert_called_once()
    service_init_mock.assert_called_once_with(
        ident=user_ip,
        user_agent=user_agent,
    )
    get_short_template_data_mock.assert_called_once_with(
        user_description=description
    )


def test_create__disabled_ai__permission_error(mocker, api_client):

    # arrange
    user_ip = '1.2.3.4'
    get_ip_mock = mocker.patch(
        'pneumatic_backend.services.views.ServicesViewSet.get_user_ip',
        return_value=user_ip
    )
    user_agent = 'Some agent'
    get_user_agent_mock = mocker.patch(
        'pneumatic_backend.services.views.ServicesViewSet.get_user_agent',
        return_value=user_agent
    )
    service_init_mock = mocker.patch.object(
        AnonOpenAiService,
        attribute='__init__',
        return_value=None
    )
    description = 'My unbelievable processes name'
    template_data = {'name': description}
    get_short_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'ai.AnonOpenAiService.get_short_template_data',
        return_value=template_data
    )
    mocker.patch(
        'pneumatic_backend.services.views.AIPermission.has_permission',
        return_value=False
    )

    # act
    response = api_client.get(
        path=f'/services/steps-by-description?description={description}'
    )

    # assert
    assert response.status_code == 401
    get_ip_mock.assert_not_called()
    get_user_agent_mock.assert_not_called()
    service_init_mock.assert_not_called()
    get_short_template_data_mock.assert_not_called()
