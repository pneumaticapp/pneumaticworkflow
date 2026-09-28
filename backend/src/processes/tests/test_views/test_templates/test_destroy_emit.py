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


def test_destroy__template__audit_template_deleted(
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
    api_client.token_authenticate(owner)
    templates_deleted_mock = mocker.patch(
        'src.analysis.services.AnalyticService.templates_deleted',
    )
    template_deleted_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_deleted',
    )

    # act
    response = api_client.delete(f'/templates/{template.id}')

    # assert
    assert response.status_code == 204
    templates_deleted_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    template_deleted_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )


def test_destroy__not_admin__audit_not_called(
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
    api_client.token_authenticate(not_admin)
    templates_deleted_mock = mocker.patch(
        'src.analysis.services.AnalyticService.templates_deleted',
    )
    template_deleted_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_deleted',
    )

    # act
    response = api_client.delete(f'/templates/{template.id}')

    # assert
    assert response.status_code == 403
    assert Template.objects.filter(id=template.id).exists()
    templates_deleted_mock.assert_not_called()
    template_deleted_mock.assert_not_called()
