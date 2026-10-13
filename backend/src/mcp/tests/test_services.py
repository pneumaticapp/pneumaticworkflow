from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import PermissionDenied

from src.accounts.enums import UserStatus
from src.authentication.services.delegation import DelegationService
from src.authentication.exceptions import (
    InvalidMcpToken,
)
from src.mcp.models import ClientPolicy, Connection
from src.authentication.services.connections import ConnectionService
from src.authentication.tokens import get_digest
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('revoked', [False, True])
def test_get_user_connections__mixed_owners__stable_scoped_order(
    grant: SimpleNamespace,
    revoked: bool,
):

    # arrange
    now = timezone.now()
    first = Connection.objects.create(
        id='00000000-0000-0000-0000-000000000001',
        user=grant.user,
        account=grant.account,
        application=grant.app,
        resource=grant.connection.resource,
        scopes=['pneumatic:read'],
        revoked_at=now if revoked else None,
    )
    second = Connection.objects.create(
        id='00000000-0000-0000-0000-000000000002',
        user=grant.user,
        account=grant.account,
        application=grant.app,
        resource=grant.connection.resource,
    )
    Connection.objects.filter(pk__in=[first.pk, second.pk]).update(
        created_at=now,
    )
    Connection.objects.filter(pk=grant.connection.pk).update(
        created_at=now - timedelta(minutes=1),
    )
    other_user = create_test_not_admin(account=grant.account)
    Connection.objects.create(
        user=other_user,
        account=grant.account,
        application=grant.app,
        resource=grant.connection.resource,
    )
    other_account = create_test_account()
    Connection.objects.create(
        user=grant.user,
        account=other_account,
        application=grant.app,
        resource=grant.connection.resource,
    )

    # act
    result = list(ConnectionService.get_user_connections(user=grant.user))

    # assert
    assert len(result) == 3
    assert str(result[0].pk) == str(first.pk)
    assert str(result[1].pk) == str(second.pk)
    assert str(result[2].pk) == str(grant.connection.pk)
    assert result[0].revoked_at == (now if revoked else None)
    assert result[0].scopes == ['pneumatic:read']
    assert result[0].created_at == now
    assert result[0].user_id == grant.user.pk
    assert result[0].account_id == grant.account.pk


def test_get_user_connections__other_user__empty(
    grant: SimpleNamespace,
):

    # arrange
    user = create_test_not_admin(account=grant.account)

    # act
    result = list(ConnectionService.get_user_connections(user=user))

    # assert
    assert result == []


def test_get_access_binding__active_grant__bound_identity(
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    token = grant.token

    # act
    binding = DelegationService.get_access_binding(
        token=token,
        resource=mcp_settings.MCP_PUBLIC_URL,
    )

    # assert
    assert binding.connection.user_id == grant.user.pk
    assert binding.connection.account_id == grant.account.pk
    assert binding.access_token.resource == [
        mcp_settings.MCP_PUBLIC_URL,
    ]


@pytest.mark.parametrize(
    'change',
    ['disabled', 'status', 'tenant', 'expiry', 'client'],
)
def test_get_access_binding__changed_identity__invalid_token(
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
    change: str,
):
    # arrange
    if change == 'disabled':
        grant.user.is_active = False
        grant.user.save(update_fields=['is_active'])
    elif change == 'status':
        grant.user.status = UserStatus.INACTIVE
        grant.user.save(update_fields=['status'])
    elif change == 'tenant':
        grant.connection.account_id = None
        grant.connection.account = create_test_account()
        grant.connection.save(update_fields=['account'])
    elif change == 'client':
        ClientPolicy.objects.filter(application=grant.app).update(
            is_active=False,
        )
    else:
        grant.access.expires = timezone.now() - timedelta(seconds=1)
        grant.access.save(update_fields=['expires'])

    # act
    with pytest.raises(InvalidMcpToken) as error:
        DelegationService.get_access_binding(
            token=grant.token,
            resource=mcp_settings.MCP_PUBLIC_URL,
        )

    # assert
    assert error.type is InvalidMcpToken


def test_create__unlisted_route__denied(
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    path = '/accounts/users'

    # act
    with pytest.raises(PermissionDenied) as error:
        DelegationService.create(
            token=grant.token,
            resource=mcp_settings.MCP_PUBLIC_URL,
            tool='list_templates',
            method='GET',
            path=path,
        )

    # assert
    assert str(error.value) == PermissionDenied.default_detail


def test_create__source_shorter_than_60s__bounded_hashed(
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    grant.access.expires = timezone.now() + timedelta(seconds=20)
    grant.access.save(update_fields=['expires'])

    # act
    issued = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='list_templates',
        method='GET',
        path='/templates',
    )

    # assert
    assert issued.delegation.expires_at == grant.access.expires
    assert issued.delegation.digest == get_digest(value=issued.credential)
    assert issued.delegation.digest != issued.credential


def test_revoke__delegated_token__immediate_denial(
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    issued = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='list_templates',
        method='GET',
        path='/templates',
    )

    # act
    ConnectionService.revoke(connection=grant.connection)

    # assert
    with pytest.raises(InvalidMcpToken):
        DelegationService.get_delegation(credential=issued.credential)


def test_create__attach_without_both_writes__denied(
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
):
    # arrange
    session_id = '11111111-1111-1111-1111-111111111111'
    path = f'/integrations/mcp/uploads/{session_id}/attach'

    # act
    with pytest.raises(PermissionDenied) as error:
        DelegationService.create(
            token=grant.token,
            resource=mcp_settings.MCP_PUBLIC_URL,
            tool='attach_uploaded_file',
            method='POST',
            path=path,
            scopes=['pneumatic:write'],
        )

    # assert
    assert str(error.value) == PermissionDenied.default_detail
