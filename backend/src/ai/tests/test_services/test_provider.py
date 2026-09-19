import pytest

from src.ai.enums import AIVendor
from src.ai.services.provider import AIProviderService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_create__cursor__get_models__ok():

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
