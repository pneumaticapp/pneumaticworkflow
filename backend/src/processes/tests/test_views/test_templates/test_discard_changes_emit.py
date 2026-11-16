import pytest

from src.authentication.enums import AuthTokenType
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_discard_changes__template_with_tasks__audit_not_deleted(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    template_discarded_changes_mock = mocker.patch(
        'src.processes.views.template.AuditEventService'
        '.template_discarded_changes',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/templates/{template.id}/discard-changes')

    # assert
    assert response.status_code == 204
    template.refresh_from_db()
    assert template.is_deleted is False
    template_discarded_changes_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        template_deleted=False,
    )


def test_discard_changes__template_without_tasks__audit_deleted(
    mocker,
    api_client,
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        is_active=False,
        tasks_count=0,
    )
    template_discarded_changes_mock = mocker.patch(
        'src.processes.views.template.AuditEventService'
        '.template_discarded_changes',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(f'/templates/{template.id}/discard-changes')

    # assert
    assert response.status_code == 204
    assert not Template.objects.filter(id=template.id).exists()
    template_discarded_changes_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
        template_deleted=True,
    )


def test_discard_changes__not_admin__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    not_admin = create_test_not_admin(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    template_discarded_changes_mock = mocker.patch(
        'src.processes.views.template.AuditEventService'
        '.template_discarded_changes',
    )
    api_client.token_authenticate(not_admin)

    # act
    response = api_client.post(f'/templates/{template.id}/discard-changes')

    # assert
    assert response.status_code == 403
    template_discarded_changes_mock.assert_not_called()
