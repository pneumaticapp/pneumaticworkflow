import pytest
from django.utils import timezone
from pneumatic_backend.processes.api_v2.services.templates\
    .integrations import TemplateIntegrationsService
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template
)
from pneumatic_backend.processes.entities import (
    TemplateIntegrationsData,
    PrivateTemplateIntegrationsData
)
from pneumatic_backend.processes.enums import TemplateIntegrationType
from pneumatic_backend.processes.models import TemplateIntegrations
from pneumatic_backend.processes.api_v2.serializers.template.\
    integrations import TemplateIntegrationsSerializer
from pneumatic_backend.webhooks.tests.fixtures import create_test_webhook
from pneumatic_backend.processes.enums import TemplateType

pytestmark = pytest.mark.django_db


def test_webhooks_unsubscribed__webhooks_attr_is_false__skip(
    mocker
):

    # arrange
    user = create_test_user()
    integration_data = TemplateIntegrationsData(
        id=1,
        webhooks=False
    )
    get_integrations_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.get_integrations',
        return_value=[integration_data]
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    service.webhooks_unsubscribed()

    # assert
    get_integrations_mock.assert_called_once()
    set_attr_value_mock.assert_not_called()


def test_webhooks_unsubscribed__webhooks_attr_is_true__disable_webhooks_attr(
    mocker
):

    # arrange
    user = create_test_user()
    integration_data = TemplateIntegrationsData(
        id=1,
        webhooks=True
    )
    get_integrations_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.get_integrations',
        return_value=[integration_data]
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    service.webhooks_unsubscribed()

    # assert
    get_integrations_mock.assert_called_once_with()
    set_attr_value_mock.assert_called_once_with(
        attr_name=TemplateIntegrationType.WEBHOOKS,
        value=False,
        template_id=integration_data['id']
    )


def test_webhooks_subscribed__webhooks_attr_is_true__skip(
    mocker
):

    # arrange
    user = create_test_user()
    integration_data = TemplateIntegrationsData(
        id=1,
        webhooks=True
    )
    get_integrations_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.get_integrations',
        return_value=[integration_data]
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    service.webhooks_subscribed()

    # assert
    get_integrations_mock.assert_called_once_with()
    set_attr_value_mock.assert_not_called()


def test_webhooks_subscribed__webhooks_attr_is_false__enable_webhooks_attr(
    mocker
):

    # arrange
    user = create_test_user()
    integration_data = TemplateIntegrationsData(
        id=1,
        webhooks=False
    )
    get_integrations_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.get_integrations',
        return_value=[integration_data]
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    service.webhooks_subscribed()

    # assert
    get_integrations_mock.assert_called_once_with()
    set_attr_value_mock.assert_called_once_with(
        attr_name=TemplateIntegrationType.WEBHOOKS,
        value=True,
        template_id=integration_data['id']
    )


def test_api_request__api_attr_is_true__skip(
    mocker
):

    # arrange
    template_id = 1
    user_agent = 'Mozilla'
    integration_data = TemplateIntegrationsData(
        id=template_id,
        api=True,
        zapier=True
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(id=template_id)
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.api_request(
        template=template,
        user_agent=user_agent
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    set_attr_value_mock.assert_not_called()


def test_api_request__api_attr_is_false__enable_api_attr(
    mocker
):

    # arrange
    template_id = 1
    user_agent = 'Mozilla'
    integration_data = TemplateIntegrationsData(
        id=template_id,
        api=False,
        zapier=True
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(id=template_id)
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.api_request(
        template=template,
        user_agent=user_agent
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    set_attr_value_mock.assert_called_once_with(
        attr_name=TemplateIntegrationType.API,
        value=True,
        template_id=template.id
    )


def test_api_request__zapier_attr_is_true__skip(
    mocker
):

    # arrange
    template_id = 1
    user_agent = 'Zapier'
    integration_data = TemplateIntegrationsData(
        id=template_id,
        api=True,
        zapier=True
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(id=template_id)
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.api_request(
        template=template,
        user_agent=user_agent
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    set_attr_value_mock.assert_not_called()


def test_api_request__zapier_attr_is_false__enable_zapier_attr(
    mocker
):

    # arrange
    template_id = 1
    user_agent = 'Zapier'
    integration_data = TemplateIntegrationsData(
        id=template_id,
        api=True,
        zapier=False
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(id=template_id)
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.api_request(
        template=template,
        user_agent=user_agent
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    set_attr_value_mock.assert_called_once_with(
        attr_name=TemplateIntegrationType.ZAPIER,
        value=True,
        template_id=template.id
    )


def test_template_updated__template_is_active_and_public__skip(
    mocker
):

    # arrange
    template_id = 1
    integrations_data = PrivateTemplateIntegrationsData(shared=True)
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integrations_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(
        id=template_id,
        is_active=True,
        is_public=True,
        is_embedded=True,
    )
    service = TemplateIntegrationsService(account=mocker.Mock)

    # act
    service.template_updated(
        template=template,
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(
        template_id
    )
    set_attr_value_mock.assert_not_called()


def test_template_updated__template_is_draft__disable_shared_attr(
    mocker
):

    # arrange
    template_id = 1
    integration_data = TemplateIntegrationsData(
        id=template_id,
        shared=True,
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(
        id=template_id,
        is_active=False,
        is_public=True,
        is_embedded=True,
    )
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.template_updated(
        template=template,
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    set_attr_value_mock.assert_called_once_with(
        attr_name=TemplateIntegrationType.SHARED,
        value=False,
        template_id=template.id
    )


def test_template_updated__template_not_public__disable_shared_attr(
    mocker
):

    # arrange
    template_id = 1
    integration_data = TemplateIntegrationsData(
        id=template_id,
        shared=True,
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(
        id=template_id,
        is_active=True,
        is_public=False,
        is_embedded=False,
    )
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.template_updated(
        template=template,
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    set_attr_value_mock.assert_called_once_with(
        attr_name=TemplateIntegrationType.SHARED,
        value=False,
        template_id=template.id
    )


def test_template_updated__share_date_not_expired__enable_shared_attr(
    mocker
):

    # arrange
    template_id = 1
    integration_data = PrivateTemplateIntegrationsData(
        id=template_id,
        shared_date_tsp='some date',
        shared=False,
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    shared_date_expired_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_shared_date_expired',
        return_value=False
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(
        id=template_id,
        is_active=True,
        is_public=False,
        is_embedded=True,
    )
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.template_updated(
        template=template,
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    shared_date_expired_mock.assert_called_once_with(
        integration_data['shared_date_tsp']
    )
    set_attr_value_mock.assert_called_once_with(
        attr_name=TemplateIntegrationType.SHARED,
        value=True,
        template_id=template.id
    )


def test_public_api_request__shared_attr_is_false__ok(
    mocker
):

    # arrange
    template_id = 1
    integration_data = TemplateIntegrationsData(
        id=template_id,
        shared=False
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(id=template_id)
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.public_api_request(
        template=template,
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    set_attr_value_mock.assert_called_once_with(
        attr_name=TemplateIntegrationType.SHARED,
        value=True,
        template_id=template.id
    )


def test_public_api_request__shared_attr_is_true__skip(
    mocker
):

    # arrange
    template_id = 1
    integration_data = TemplateIntegrationsData(
        id=template_id,
        shared=True
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    template = mocker.Mock(id=template_id)
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service.public_api_request(
        template=template,
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    set_attr_value_mock.assert_not_called()


def test_get_integrations__all_templates__ok(
    mocker
):

    # arrange
    user = create_test_user()
    another_account_user = create_test_user(email='test@test.test')
    template = create_test_template(user)
    create_test_template(
        user=user,
        type_=TemplateType.ONBOARDING_ADMIN
    )
    create_test_template(another_account_user)
    integration_data = PrivateTemplateIntegrationsData(
        id=template.id,
        shared=True,
        shared_date_tsp='some str 1',
        api=True,
        api_date_tsp='some str 2',
        zapier=False,
        zapier_date_tsp='some str 3',
        webhooks=False,
        webhooks_date_tsp='some str 4',
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service.get_integrations()

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template.id)
    assert len(result) == 1
    assert result[0]['id'] == template.id


def test_get_integrations__filter_by_template_ids__ok(
    mocker
):

    # arrange
    user = create_test_user()
    template_1 = create_test_template(user)
    create_test_template(user)
    integration_data = PrivateTemplateIntegrationsData(
        id=template_1.id,
        shared=True,
        shared_date_tsp='some str 1',
        api=True,
        api_date_tsp='some str 2',
        zapier=False,
        zapier_date_tsp='some str 3',
        webhooks=False,
        webhooks_date_tsp='some str 4',
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service.get_integrations(
        template_id=[template_1.id]
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template_1.id)
    assert len(result) == 1
    assert result[0]['id'] == template_1.id


def test_shared_date_expired__expired__ok():

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    expired_period = timezone.timedelta(
        seconds=TemplateIntegrationsService.cache_timeout + 60
    )
    template_integrations = TemplateIntegrations.objects.create(
        account_id=user.account_id,
        template_id=template.id,
        shared=True,
        shared_date=(timezone.now() - expired_period)
    )
    template_integrations_data = TemplateIntegrationsSerializer(
        instance=template_integrations
    ) .data
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service._shared_date_expired(
        template_integrations_data['shared_date_tsp']
    )

    # assert
    assert result is True


def test_shared_date_expired__not_expired__ok():

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    expired_period = timezone.timedelta(
        seconds=TemplateIntegrationsService.cache_timeout - 60
    )
    template_integrations = TemplateIntegrations.objects.create(
        account_id=user.account_id,
        template_id=template.id,
        shared=True,
        shared_date=(timezone.now() - expired_period)
    )
    template_integrations_data = TemplateIntegrationsSerializer(
        instance=template_integrations
    ).data
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service._shared_date_expired(
        template_integrations_data['shared_date_tsp']
    )

    # assert
    assert result is False


def test_private_get_template_integrations_data__from_cache__ok(
    mocker
):

    # arrange
    template_id = 1
    template = mocker.Mock(id=template_id)
    integration_data = TemplateIntegrationsData(id=template.id)
    get_cache_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_cache',
        return_value=integration_data
    )
    set_cache_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_set_cache'
    )
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    result = service._get_template_integrations_data(
        template_id=template_id
    )

    # assert
    get_cache_mock.assert_called_once_with(key=template.id)
    set_cache_mock.assert_not_called()
    assert result['id'] == template_id


def test_private_get_template_integrations_data__empty_cache__ok(
    mocker
):

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    template_integrations = TemplateIntegrations.objects.create(
        account_id=template.account_id,
        template_id=template.id
    )
    get_cache_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_cache',
        return_value=None
    )
    data_mock = mocker.Mock()
    set_cache_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_set_cache',
        return_value=data_mock
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service._get_template_integrations_data(
        template_id=template.id
    )

    # assert
    get_cache_mock.assert_called_once_with(key=template.id)
    set_cache_mock.assert_called_once_with(
        key=template.id,
        value=template_integrations
    )
    assert result == data_mock


def test_get_template_integrations_data__ok(
    mocker
):

    # arrange
    template_id = 1
    integration_data = PrivateTemplateIntegrationsData(
        id=template_id,
        shared=True,
        shared_date_tsp='some str 1',
        api=True,
        api_date_tsp='some str 2',
        zapier=False,
        zapier_date_tsp='some str 3',
        webhooks=False,
        webhooks_date_tsp='some str 4',
    )
    get_template_integrations_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_get_template_integrations_data',
        return_value=integration_data
    )
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    result = service.get_template_integrations_data(
        template_id=template_id
    )

    # assert
    get_template_integrations_data_mock.assert_called_once_with(template_id)
    assert 'shared_date_tsp' not in result.keys()
    assert 'api_date_tsp' not in result.keys()
    assert 'zapier_date_tsp' not in result.keys()
    assert 'webhooks_date_tsp' not in result.keys()


def test_create_integrations_for_template__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service.create_integrations_for_template(
        template=template,
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )

    # assert
    assert result.account_id == user.account_id
    assert result.template_id == template.id
    assert result.webhooks is False
    assert result.webhooks_date is None
    assert result.api is False
    assert result.api_date is None
    assert result.zapier is False
    assert result.zapier_date is None
    assert result.shared is False
    assert result.shared_date is None
    set_attr_value_mock.assert_not_called()


def test_create_integrations_for_template__webhooks_is_true__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service.create_integrations_for_template(
        template=template,
        webhooks=True
    )

    # assert
    assert result.account_id == user.account_id
    assert result.template_id == template.id
    assert result.webhooks is False
    assert result.webhooks_date is None
    assert result.api is False
    assert result.api_date is None
    assert result.zapier is False
    assert result.zapier_date is None
    assert result.shared is False
    assert result.shared_date is None
    set_attr_value_mock.assert_called_once_with(
        template_id=template.id,
        attr_name=TemplateIntegrationType.WEBHOOKS,
        value=True
    )


def test_create_integrations_for_template__webhooks_exists__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    create_test_webhook(
        user=user,
        event='some event',
    )
    set_attr_value_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService._set_attr_value'
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service.create_integrations_for_template(
        template=template,
    )

    # assert
    set_attr_value_mock.assert_called_once_with(
        template_id=template.id,
        attr_name=TemplateIntegrationType.WEBHOOKS,
        value=True
    )
    assert result.template_id == template.id


def test_set_attr_value__ok(mocker):

    # arrange
    template_id = 1
    value = True
    attr_name = 'attr_name'
    template = mocker.Mock(id=template_id)
    template_integrations = mocker.Mock(template_id=template_id)
    update_instance_attr_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_update_instance_attr',
        return_value=template_integrations
    )

    set_cache_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.TemplateIntegrationsService.'
        '_set_cache'
    )
    service = TemplateIntegrationsService(account=mocker.Mock())

    # act
    service._set_attr_value(
        attr_name=attr_name,
        template_id=template_id,
        value=value
    )

    # assert
    update_instance_attr_mock.assert_called_once_with(
        template_id=template_id,
        attr_name=attr_name,
        value=value
    )
    set_cache_mock.assert_called_once_with(
        key=template.id,
        value=template_integrations
    )


def test_update_instance_attr__first_activation__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    TemplateIntegrations.objects.create(
        account_id=template.account_id,
        template_id=template.id
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.AnalyticService.templates_integrated'
    )
    service = TemplateIntegrationsService(
        account=user.account,
        user=user
    )

    # act
    result = service._update_instance_attr(
        attr_name=TemplateIntegrationType.API,
        value=True,
        template_id=template.id,
    )

    # assert
    assert result.api is True
    assert result.api_date is not None
    analytics_mock.assert_called_once_with(
        template_id=template.id,
        account_id=user.account_id,
        integration_type=TemplateIntegrationType.API,
        is_superuser=False,
        user_id=user.id,
        anonymous_id=None
    )


def test_update_instance_attr__second_activation__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    TemplateIntegrations.objects.create(
        account_id=template.account_id,
        template_id=template.id,
        webhooks=True,
        webhooks_date=timezone.now()
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.AnalyticService.templates_integrated'
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service._update_instance_attr(
        attr_name=TemplateIntegrationType.WEBHOOKS,
        value=True,
        template_id=template.id,
    )

    # assert
    assert result.webhooks is True
    assert result.webhooks_date is not None
    analytics_mock.assert_not_called()


def test_update_instance_attr__deactivation__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    TemplateIntegrations.objects.create(
        account_id=template.account_id,
        template_id=template.id,
        webhooks=True,
        webhooks_date=timezone.now()
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.AnalyticService.templates_integrated'
    )
    service = TemplateIntegrationsService(account=user.account)

    # act
    result = service._update_instance_attr(
        attr_name=TemplateIntegrationType.WEBHOOKS,
        value=False,
        template_id=template.id,
    )

    # assert
    assert result.webhooks is False
    assert result.webhooks_date is not None
    analytics_mock.assert_not_called()


def test_update_instance_attr__webhooks__analytics_not_called(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user)
    TemplateIntegrations.objects.create(
        account_id=template.account_id,
        template_id=template.id
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.'
        'integrations.AnalyticService.templates_integrated'
    )
    service = TemplateIntegrationsService(
        account=user.account,
        user=user
    )

    # act
    result = service._update_instance_attr(
        attr_name=TemplateIntegrationType.WEBHOOKS,
        value=True,
        template_id=template.id,
    )

    # assert
    assert result.webhooks is True
    assert result.webhooks_date is not None
    analytics_mock.assert_not_called()
