import pytest

from src.accounts.enums import (
    BillingPlanType,
    LeaseLevel,
)
from src.authentication.enums import AuthTokenType
from src.logs.events import Actor, EventObject
from src.logs.events.enums import (
    ActorType,
    EventName,
    EventObjectType,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_token__master_account__emit_tenant_login_as(
    mocker,
    api_client,
):

    # arrange
    master_account = create_test_account()
    master_account_owner = create_test_owner(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
    )
    tenant_account_owner = create_test_owner(
        account=tenant_account,
        email='tenant_owner@test.test',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService'
        '.get_auth_token',
        return_value='some token',
    )
    tenants_accessed_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'tenants_accessed',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')
    api_client.token_authenticate(master_account_owner)

    # act
    response = api_client.get(f'/tenants/{tenant_account.id}/token')

    # assert
    assert response.status_code == 200
    emit_mock.assert_called_once_with(
        EventName.TENANT_LOGIN_AS,
        account_id=tenant_account.id,
        actor=Actor(
            type=ActorType.USER,
            id=master_account_owner.id,
            email=master_account_owner.email,
        ),
        event_object=EventObject(
            type=EventObjectType.ACCOUNT,
            id=tenant_account.id,
        ),
        payload={'master_account_id': master_account.id},
    )
    get_auth_token_mock.assert_called_once_with(
        user=tenant_account_owner,
        user_agent='Firefox',
        user_ip='192.168.0.1',
        superuser_mode=True,
    )
    tenants_accessed_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_token__master_account__event_keeps_request_context(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    master_account = create_test_account()
    master_account_owner = create_test_owner(account=master_account)
    tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=master_account,
    )
    tenant_account_owner = create_test_owner(
        account=tenant_account,
        email='tenant_owner@test.test',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService'
        '.get_auth_token',
        return_value='some token',
    )
    tenants_accessed_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'tenants_accessed',
    )
    api_client.token_authenticate(
        master_account_owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.20',
    )

    # act
    response = api_client.get(
        f'/tenants/{tenant_account.id}/token',
        HTTP_X_REQUEST_ID='audit-tenant-1',
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TENANT_LOGIN_AS
    assert event.account_id == tenant_account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=master_account_owner.id,
        email=master_account_owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.ACCOUNT,
        id=tenant_account.id,
    )
    assert event.payload == {'master_account_id': master_account.id}
    assert event.ip == '10.10.0.20'
    assert event.user_agent == 'Chrome/141'
    assert event.request_id == 'audit-tenant-1'
    get_auth_token_mock.assert_called_once_with(
        user=tenant_account_owner,
        user_agent='Chrome/141',
        user_ip='10.10.0.20',
        superuser_mode=True,
    )
    tenants_accessed_mock.assert_called_once_with(
        master_user=master_account_owner,
        tenant_account=tenant_account,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_token__not_own_tenant__no_event(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account(lease_level=LeaseLevel.STANDARD)
    account_owner = create_test_owner(account=account)
    another_account = create_test_account(
        name='another account',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.STANDARD,
    )
    another_tenant_account = create_test_account(
        name='tenant',
        plan=BillingPlanType.UNLIMITED,
        lease_level=LeaseLevel.TENANT,
        master_account=another_account,
    )
    create_test_owner(
        account=another_tenant_account,
        email='tenant_owner@test.test',
    )
    get_auth_token_mock = mocker.patch(
        'src.authentication.services.user_auth.AuthService'
        '.get_auth_token',
    )
    emit_mock = mocker.patch('src.logs.events.services.emit')
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(
        f'/tenants/{another_tenant_account.id}/token',
    )

    # assert
    assert response.status_code == 403
    emit_mock.assert_not_called()
    get_auth_token_mock.assert_not_called()
