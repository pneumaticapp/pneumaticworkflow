import pytest

from src.ai.enums import AIVendor
from src.ai.exceptions import AIHandlerException, AIProviderException
from src.ai.messages import MSG_AI_0006, MSG_AI_0007, MSG_AI_0008
from src.ai.models import AIProvider
from src.ai.services.provider import AIProviderService
from src.ai.tests.fixtures import create_test_provider
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__cursor__get_models__ok(mocker):

    """ Create Cursor provider and list models """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = AIProviderService(user=user, account=account)
    base_url = 'https://api.cursor.com/v1'
    api_key = (
        'crsr_431e9b85d84612e001fe357ad9cb8204a0054d38a3274b8efce4d7ea91797cb4'
    )
    name = 'Custom model'
    vendor = AIVendor.CURSOR
    mocker.patch.object(AIProviderService, '_create_actions')

    # act
    provider = service.create(
        base_url=base_url,
        vendor=vendor,
        api_key=api_key,
        name=name,
    )
    models = service.get_models()

    # assert
    assert provider.name == name
    assert provider.vendor == provider.vendor
    assert provider.base_url == base_url
    assert provider.api_key == api_key
    assert models


def test_create_actions__ok(mocker):

    """ Check provider connection on create """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    service = AIProviderService(user=user, instance=provider)
    models = [{'slug': 'gpt-4o', 'name': 'GPT-4o'}]
    get_models_mock = mocker.patch.object(
        service,
        'get_models',
        return_value=models,
    )
    get_completion_mock = mocker.patch.object(
        service,
        'get_completion',
        return_value='1',
    )

    # act
    service._create_actions()

    # assert
    get_models_mock.assert_called_once_with()
    get_completion_mock.assert_called_once_with(
        system_message='You are a office employee.',
        user_message='Say "Hello world"',
        model='gpt-4o',
    )


def test_create_actions__get_models_error(mocker):

    """ Raise if models request fails """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    service = AIProviderService(user=user, instance=provider)
    error_message = '"Incorrect API key provided." (401)'
    get_models_mock = mocker.patch.object(
        service,
        'get_models',
        side_effect=AIHandlerException(message=error_message),
    )
    get_completion_mock = mocker.patch.object(
        service,
        'get_completion',
    )

    # act
    with pytest.raises(AIProviderException) as ex:
        service._create_actions()

    # assert
    assert str(ex.value.message) == str(MSG_AI_0006(error=error_message))
    get_models_mock.assert_called_once_with()
    get_completion_mock.assert_not_called()


def test_create_actions__get_completion_error(mocker):

    """ Raise if chat request fails """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    service = AIProviderService(user=user, instance=provider)
    models = [{'slug': 'gpt-4o', 'name': 'GPT-4o'}]
    error_message = '"This model does not exist." (404)'
    get_models_mock = mocker.patch.object(
        service,
        'get_models',
        return_value=models,
    )
    get_completion_mock = mocker.patch.object(
        service,
        'get_completion',
        side_effect=AIHandlerException(message=error_message),
    )

    # act
    with pytest.raises(AIProviderException) as ex:
        service._create_actions()

    # assert
    assert str(ex.value.message) == str(MSG_AI_0007(error=error_message))
    get_models_mock.assert_called_once_with()
    get_completion_mock.assert_called_once_with(
        system_message='You are a office employee.',
        user_message='Say "Hello world"',
        model='gpt-4o',
    )


def test_create_first_completion__empty_response(mocker):

    """ Raise if chat request returns an empty response """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    service = AIProviderService(user=user, instance=provider)
    model = 'gpt-4o'
    get_completion_mock = mocker.patch.object(
        service,
        'get_completion',
        return_value='',
    )

    # act
    with pytest.raises(AIProviderException) as ex:
        service._create_first_completion(model=model)

    # assert
    assert str(ex.value.message) == str(MSG_AI_0008(model=model))
    get_completion_mock.assert_called_once_with(
        system_message='You are a office employee.',
        user_message='Say "Hello world"',
        model=model,
    )


def test_create__get_models_error__not_created(mocker):

    """ Do not save provider if models check fails """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = AIProviderService(user=user, account=account)
    name = 'OpenRouter'
    error_message = '"Incorrect API key provided." (401)'
    mocker.patch.object(
        AIProviderService,
        'get_models',
        side_effect=AIHandlerException(message=error_message),
    )
    get_completion_mock = mocker.patch.object(
        AIProviderService,
        'get_completion',
    )

    # act
    with pytest.raises(AIProviderException) as ex:
        service.create(
            name=name,
            base_url='https://openrouter.ai/api/v1',
            api_key='sk-or-v1-example',
            vendor=AIVendor.OPENROUTER,
        )

    # assert
    assert str(ex.value.message) == str(MSG_AI_0006(error=error_message))
    assert not AIProvider.objects.filter(name=name).exists()
    get_completion_mock.assert_not_called()
