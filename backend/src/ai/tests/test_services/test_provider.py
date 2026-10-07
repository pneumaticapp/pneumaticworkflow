import pytest

from src.ai.enums import AIVendor
from src.ai.exceptions import (
    AIHandlerException,
    AIProviderException,
    AIProviderInUseException,
)
from src.ai.messages import (
    MSG_AI_0005,
    MSG_AI_0006,
    MSG_AI_0007,
    MSG_AI_0008,
)
from src.ai.models import AIProvider
from src.ai.services.config import AI_VENDORS_CONFIG
from src.ai.services.handlers import AnthropicHandler, OpenAIHandler
from src.ai.services.provider import AIProviderService
from src.ai.tests.fixtures import create_test_agent, create_test_provider
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_get_vendor__custom__return_openai():

    """ Custom vendor """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    provider.vendor = AIVendor.CUSTOM
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service._get_vendor()

    # assert
    assert result == AIVendor.OPENAI


def test_get_vendor__known_vendor__return_instance_vendor():

    """ Known vendor """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    provider.vendor = AIVendor.ANTHROPIC
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service._get_vendor()

    # assert
    assert result == AIVendor.ANTHROPIC


def test_get_handler__default_params__ok(mocker):

    """ Default params """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    get_vendor_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_vendor',
        return_value=AIVendor.OPENAI,
    )
    open_ai_handler_init_mock = mocker.patch.object(
        OpenAIHandler,
        '__init__',
        return_value=None,
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service._get_handler()

    # assert
    assert isinstance(result, OpenAIHandler)
    get_vendor_mock.assert_called_once_with()
    open_ai_handler_init_mock.assert_called_once_with(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
        agent=None,
        task=None,
    )


def test_get_handler__with_agent_and_task__ok(mocker):

    """ With agent and task """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    agent = create_test_agent(account=account, provider=provider)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    get_vendor_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_vendor',
        return_value=AIVendor.OPENAI,
    )
    open_ai_handler_init_mock = mocker.patch.object(
        OpenAIHandler,
        '__init__',
        return_value=None,
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service._get_handler(agent=agent, task=task)

    # assert
    assert isinstance(result, OpenAIHandler)
    get_vendor_mock.assert_called_once_with()
    open_ai_handler_init_mock.assert_called_once_with(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.OPENAI],
        agent=agent,
        task=task,
    )


def test_get_handler__anthropic_vendor__return_anthropic_handler(mocker):

    """ Vendor handler selection """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    get_vendor_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_vendor',
        return_value=AIVendor.ANTHROPIC,
    )
    anthropic_handler_init_mock = mocker.patch.object(
        AnthropicHandler,
        '__init__',
        return_value=None,
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service._get_handler()

    # assert
    assert isinstance(result, AnthropicHandler)
    get_vendor_mock.assert_called_once_with()
    anthropic_handler_init_mock.assert_called_once_with(
        provider=provider,
        account=account,
        config=AI_VENDORS_CONFIG[AIVendor.ANTHROPIC],
        agent=None,
        task=None,
    )


def test_get_models__cache_hit__return_cached_models(mocker):

    """ Cache hit """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    models = [{'slug': 'gpt-4o', 'name': 'gpt-4o'}]
    get_cache_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_cache',
        return_value=models,
    )
    get_handler_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_handler',
    )
    set_cache_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._set_cache',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service.get_models()

    # assert
    assert result == models
    get_cache_mock.assert_called_once_with(
        key=f'{owner.id}_{provider.name}',
        default=[],
    )
    get_handler_mock.assert_not_called()
    set_cache_mock.assert_not_called()


def test_get_models__cache_miss__return_handler_models(mocker):

    """ Cache miss """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    models = [{'slug': 'gpt-4o', 'name': 'gpt-4o'}]
    get_cache_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_cache',
        return_value=[],
    )
    get_models_mock = mocker.Mock(return_value=models)
    handler = mocker.Mock(get_models=get_models_mock)
    get_handler_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_handler',
        return_value=handler,
    )
    set_cache_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._set_cache',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service.get_models()

    # assert
    assert result == models
    get_cache_mock.assert_called_once_with(
        key=f'{owner.id}_{provider.name}',
        default=[],
    )
    get_handler_mock.assert_called_once_with()
    get_models_mock.assert_called_once_with()
    set_cache_mock.assert_called_once_with(
        key=f'{owner.id}_{provider.name}',
        value=models,
    )


def test_get_models__cache_miss_handler_empty__return_empty_list(mocker):

    """ Cache miss, handler empty """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    get_cache_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_cache',
        return_value=[],
    )
    get_models_mock = mocker.Mock(return_value=[])
    handler = mocker.Mock(get_models=get_models_mock)
    get_handler_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_handler',
        return_value=handler,
    )
    set_cache_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._set_cache',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service.get_models()

    # assert
    assert result == []
    get_cache_mock.assert_called_once_with(
        key=f'{owner.id}_{provider.name}',
        default=[],
    )
    get_handler_mock.assert_called_once_with()
    get_models_mock.assert_called_once_with()
    set_cache_mock.assert_called_once_with(
        key=f'{owner.id}_{provider.name}',
        value=[],
    )


def test_get_completion__default_params__ok(mocker):

    """ Default params """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    system_message = 'You are helpful.'
    user_message = 'Say hello'
    model = 'gpt-4o'
    response = 'Hello'
    get_completion_mock = mocker.Mock(return_value=response)
    handler = mocker.Mock(get_completion=get_completion_mock)
    get_handler_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_handler',
        return_value=handler,
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service.get_completion(
        system_message=system_message,
        user_message=user_message,
        model=model,
    )

    # assert
    assert result == response
    get_handler_mock.assert_called_once_with(agent=None, task=None)
    get_completion_mock.assert_called_once_with(
        system_message=system_message,
        user_message=user_message,
        model=model,
    )


def test_get_completion__with_agent_and_task__ok(mocker):

    """ With agent and task """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    agent = create_test_agent(account=account, provider=provider)
    workflow = create_test_workflow(user=owner, tasks_count=1)
    task = workflow.tasks.get(number=1)
    system_message = 'You are helpful.'
    user_message = 'Say hello'
    model = 'gpt-4o'
    response = 'Hello'
    get_completion_mock = mocker.Mock(return_value=response)
    handler = mocker.Mock(get_completion=get_completion_mock)
    get_handler_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_handler',
        return_value=handler,
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service.get_completion(
        system_message=system_message,
        user_message=user_message,
        model=model,
        agent=agent,
        task=task,
    )

    # assert
    assert result == response
    get_handler_mock.assert_called_once_with(agent=agent, task=task)
    get_completion_mock.assert_called_once_with(
        system_message=system_message,
        user_message=user_message,
        model=model,
    )


def test_get_first_model__models_found__return_first_slug(mocker):

    """ Models found """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    model_1 = {'slug': 'gpt-4o', 'name': 'gpt-4o'}
    model_2 = {'slug': 'gpt-4o-mini', 'name': 'gpt-4o-mini'}
    get_models_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.get_models',
        return_value=[model_1, model_2],
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service._get_first_model()

    # assert
    assert result == 'gpt-4o'
    get_models_mock.assert_called_once_with()


def test_get_first_model__handler_error__raise_exception(mocker):

    """ Handler error """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    error_message = 'Connection error'
    get_models_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.get_models',
        side_effect=AIHandlerException(message=error_message),
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    with pytest.raises(AIProviderException) as ex:
        service._get_first_model()

    # assert
    assert str(ex.value) == str(MSG_AI_0006(error=error_message))
    get_models_mock.assert_called_once_with()


def test_get_first_model__empty_list__raise_exception(mocker):

    """ Empty models list """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    get_models_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.get_models',
        return_value=[],
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    with pytest.raises(AIProviderException) as ex:
        service._get_first_model()

    # assert
    assert str(ex.value) == str(MSG_AI_0006(error='empty list'))
    get_models_mock.assert_called_once_with()


def test_create_first_completion__completion_received__ok(mocker):

    """ Completion received """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    model = 'gpt-4o'
    get_completion_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.get_completion',
        return_value='Hello world',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    service._create_first_completion(model=model)

    # assert
    get_completion_mock.assert_called_once_with(
        system_message='You are a office employee.',
        user_message='Say "Hello world"',
        model=model,
    )


def test_create_first_completion__handler_error__raise_exception(mocker):

    """ Handler error """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    model = 'gpt-4o'
    error_message = 'Request failed'
    get_completion_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.get_completion',
        side_effect=AIHandlerException(message=error_message),
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    with pytest.raises(AIProviderException) as ex:
        service._create_first_completion(model=model)

    # assert
    assert str(ex.value) == str(MSG_AI_0007(error=error_message))
    get_completion_mock.assert_called_once_with(
        system_message='You are a office employee.',
        user_message='Say "Hello world"',
        model=model,
    )


def test_create_first_completion__empty_completion__raise_exception(mocker):

    """ Empty completion """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    model = 'gpt-4o'
    get_completion_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.get_completion',
        return_value='',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    with pytest.raises(AIProviderException) as ex:
        service._create_first_completion(model=model)

    # assert
    assert str(ex.value) == str(MSG_AI_0008(model=model))
    get_completion_mock.assert_called_once_with(
        system_message='You are a office employee.',
        user_message='Say "Hello world"',
        model=model,
    )


def test_create_actions__provider_check__ok(mocker):

    """ Provider check """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    model = 'gpt-4o'
    get_first_model_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._get_first_model',
        return_value=model,
    )
    create_first_completion_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._create_first_completion',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    service._create_actions(name='OpenAI')

    # assert
    get_first_model_mock.assert_called_once_with()
    create_first_completion_mock.assert_called_once_with(model=model)


def test_create_instance__with_vendor__ok(mocker):

    """ With vendor """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    name = 'OpenAI'
    base_url = 'https://api.openai.com/v1'
    api_key = 'sk-example'
    encrypt_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.encrypt',
        return_value='encrypted-key',
    )
    service = AIProviderService(user=owner)

    # act
    result = service._create_instance(
        name=name,
        base_url=base_url,
        api_key=api_key,
        vendor=AIVendor.OPENAI,
    )

    # assert
    provider = AIProvider.objects.get(id=result.id)
    assert provider.account_id == account.id
    assert provider.name == name
    assert provider.base_url == base_url
    assert provider.api_key_encrypted == 'encrypted-key'
    assert provider.vendor == AIVendor.OPENAI
    assert service.instance == provider
    encrypt_mock.assert_called_once_with(api_key)


def test_create_instance__default_vendor__create_custom(mocker):

    """ Default vendor """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    api_key = 'sk-example'
    encrypt_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.encrypt',
        return_value='encrypted-key',
    )
    service = AIProviderService(user=owner)

    # act
    result = service._create_instance(
        name='Custom',
        base_url='https://custom.ai/v1',
        api_key=api_key,
    )

    # assert
    provider = AIProvider.objects.get(id=result.id)
    assert provider.vendor == AIVendor.CUSTOM
    encrypt_mock.assert_called_once_with(api_key)


def test_create_instance__extra_kwargs__ignore_kwargs(mocker):

    """ Extra kwargs """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    name = 'OpenAI'
    api_key = 'sk-example'
    encrypt_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.encrypt',
        return_value='encrypted-key',
    )
    service = AIProviderService(user=owner)

    # act
    result = service._create_instance(
        name=name,
        base_url='https://api.openai.com/v1',
        api_key=api_key,
        vendor=AIVendor.OPENAI,
        unknown_field='value',
    )

    # assert
    provider = AIProvider.objects.get(id=result.id)
    assert provider.name == name
    encrypt_mock.assert_called_once_with(api_key)


def test_create_by_vendor__known_vendor__ok(mocker):

    """ Known vendor """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    api_key = 'sk-ant-example'
    create_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.create',
        return_value=provider,
    )
    service = AIProviderService(user=owner)

    # act
    result = service.create_by_vendor(
        api_key=api_key,
        vendor=AIVendor.ANTHROPIC,
    )

    # assert
    assert result == provider
    create_mock.assert_called_once_with(
        name='Anthropic',
        base_url='https://api.anthropic.com/v1',
        api_key=api_key,
        vendor=AIVendor.ANTHROPIC,
    )


def test_create_by_vendor__unknown_vendor__raise_exception(mocker):

    """ Unknown vendor """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    create_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.create',
    )
    service = AIProviderService(user=owner)

    # act
    with pytest.raises(KeyError) as ex:
        service.create_by_vendor(
            api_key='sk-example',
            vendor=AIVendor.CUSTOM,
        )

    # assert
    assert str(ex.value) == "'custom'"
    create_mock.assert_not_called()


def test_partial_update__api_key__encrypt_and_save(mocker):

    """ Update api key """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    api_key = 'sk-new-key'
    encrypt_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.encrypt',
        return_value='encrypted-new-key',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service.partial_update(api_key=api_key)

    # assert
    assert result == provider
    provider.refresh_from_db()
    assert provider.api_key_encrypted == 'encrypted-new-key'
    assert service.update_fields == set()
    encrypt_mock.assert_called_once_with(api_key)


def test_partial_update__without_api_key__ok(mocker):

    """ Update without api key """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    encrypt_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.encrypt',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service.partial_update(name='New name')

    # assert
    assert result == provider
    provider.refresh_from_db()
    assert provider.name == 'New name'
    encrypt_mock.assert_not_called()


def test_partial_update__not_force_save__not_saved(mocker):

    """ Without force save """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account, name='OpenRouter')
    encrypt_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService.encrypt',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    result = service.partial_update(force_save=False, name='New name')

    # assert
    assert result.name == 'New name'
    assert service.update_fields == {'name'}
    assert AIProvider.objects.get(id=provider.id).name == 'OpenRouter'
    encrypt_mock.assert_not_called()


def test_delete__not_in_use__ok(mocker):

    """ Provider not in use """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    delete_cache_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._delete_cache',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    service.delete()

    # assert
    provider.refresh_from_db()
    assert provider.is_deleted is True
    delete_cache_mock.assert_called_once_with(
        key=f'{owner.id}_{provider.name}',
    )


def test_delete__in_use__raise_exception(mocker):

    """ Provider in use """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    provider = create_test_provider(account=account)
    create_test_agent(account=account, provider=provider)
    delete_cache_mock = mocker.patch(
        'src.ai.services.provider.AIProviderService._delete_cache',
    )
    service = AIProviderService(user=owner, instance=provider)

    # act
    with pytest.raises(AIProviderInUseException) as ex:
        service.delete()

    # assert
    assert str(ex.value) == str(MSG_AI_0005)
    provider.refresh_from_db()
    assert provider.is_deleted is False
    delete_cache_mock.assert_not_called()
