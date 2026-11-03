import pytest

from src.authentication.enums import AuthTokenType
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_clone__template__audit_template_cloned(
    mocker,
    api_client,
):

    """ The record is about the copy, not the original: the template
        is the new draft and the name is the one the draft got. """

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        user=owner,
        name='Onboarding',
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(owner)
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.integrations.'
        'TemplateIntegrationsService.create_integrations_for_template',
    )
    template_cloned_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_cloned',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    clone = Template.objects.get(id=response.data['id'])
    assert clone.id != template.id
    create_integrations_mock.assert_called_once_with(template=clone)
    template_cloned_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=clone,
        name='Onboarding - clone',
    )


def test_clone__template_of_another_account__audit_not_called(
    mocker,
    api_client,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    another_account = create_test_account(name='Another Company')
    another_owner = create_test_owner(
        account=another_account,
        email='another_owner@pneumatic.app',
    )
    api_client.token_authenticate(another_owner)
    create_integrations_mock = mocker.patch(
        'src.processes.services.templates.integrations.'
        'TemplateIntegrationsService.create_integrations_for_template',
    )
    template_cloned_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_cloned',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 404
    assert Template.objects.count() == 1
    create_integrations_mock.assert_not_called()
    template_cloned_mock.assert_not_called()
