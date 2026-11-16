import pytest

from src.authentication.enums import AuthTokenType
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
)

pytestmark = pytest.mark.django_db


def test_export__no_filters__audit_templates_export(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    templates_export_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.templates_export',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get('/templates/export')

    # assert
    assert response.status_code == 200
    templates_export_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        filters={'is_active': None, 'is_public': None},
    )


def test_export__filters__audit_with_request_filters(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    templates_export_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.templates_export',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(
        '/templates/export?is_active=true&ordering=name',
    )

    # assert
    assert response.status_code == 200
    templates_export_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        filters={
            'is_active': True,
            'is_public': None,
            'ordering': 'name',
        },
    )


def test_export__first_page__audit_templates_export(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    templates_export_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.templates_export',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get('/templates/export?limit=10&offset=0')

    # assert
    assert response.status_code == 200
    templates_export_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        filters={
            'is_active': None,
            'is_public': None,
            'limit': 10,
            'offset': 0,
        },
    )


def test_export__next_page__audit_not_called(
    mocker,
    api_client,
):

    """ One record per export: a page after the first one is the same
        export read further, not a new one. """

    # arrange
    owner = create_test_owner()
    templates_export_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.templates_export',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get('/templates/export?limit=10&offset=10')

    # assert
    assert response.status_code == 200
    templates_export_mock.assert_not_called()


def test_export__not_admin__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    not_admin = create_test_not_admin(account=account)
    templates_export_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.templates_export',
    )
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.get('/templates/export')

    # assert
    assert response.status_code == 403
    templates_export_mock.assert_not_called()
