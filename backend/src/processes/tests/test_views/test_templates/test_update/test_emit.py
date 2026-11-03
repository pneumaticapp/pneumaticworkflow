import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_update__active_template__audit_template_updated(
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
    task = template.tasks.get(number=1)
    api_client.token_authenticate(owner)
    update_workflows_mock = mocker.patch(
        'src.processes.views.template.update_workflows.delay',
    )
    template_integrations_updated_mock = mocker.patch(
        'src.processes.services.templates.integrations'
        '.TemplateIntegrationsService.template_updated',
    )
    templates_updated_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    kickoff_updated_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    template_updated_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_updated',
    )

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': 'Onboarding changed',
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': owner.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'id': template.kickoff_instance.id,
                'fields': [],
            },
            'tasks': [
                {
                    'id': task.id,
                    'api_name': task.api_name,
                    'number': task.number,
                    'name': task.name,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': owner.id,
                        },
                    ],
                },
            ],
        },
    )

    # assert
    assert response.status_code == 200
    template.refresh_from_db()
    update_workflows_mock.assert_called_once_with(
        template_id=template.id,
        version=template.version,
        updated_by=owner.id,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
    )
    template_integrations_updated_mock.assert_called_once_with(
        template=template,
    )
    templates_updated_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        kickoff_fields_count=0,
        tasks_count=1,
        tasks_fields_count=0,
        delays_count=0,
        due_in_count=0,
        conditions_count=0,
    )
    kickoff_updated_mock.assert_called_once_with(
        user=owner,
        template=template,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    template_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )


def test_update__draft__audit_template_updated(
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
    update_workflows_mock = mocker.patch(
        'src.processes.views.template.update_workflows.delay',
    )
    template_integrations_updated_mock = mocker.patch(
        'src.processes.services.templates.integrations'
        '.TemplateIntegrationsService.template_updated',
    )
    templates_updated_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_updated',
    )
    kickoff_updated_mock = mocker.patch(
        'src.processes.views.template.'
        'AnalyticService.templates_kickoff_updated',
    )
    template_updated_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_updated',
    )

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': 'Draft again',
            'is_active': False,
            'kickoff': {
                'id': template.kickoff_instance.id,
                'fields': [],
            },
            'tasks': [],
        },
    )

    # assert
    assert response.status_code == 200
    template.refresh_from_db()
    update_workflows_mock.assert_not_called()
    template_integrations_updated_mock.assert_called_once_with(
        template=template,
    )
    templates_updated_mock.assert_not_called()
    kickoff_updated_mock.assert_not_called()
    template_updated_mock.assert_called_once_with(
        user=owner,
        auth_type=AuthTokenType.USER,
        template=template,
    )


def test_update__not_admin__audit_not_called(
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
    update_workflows_mock = mocker.patch(
        'src.processes.views.template.update_workflows.delay',
    )
    template_integrations_updated_mock = mocker.patch(
        'src.processes.services.templates.integrations'
        '.TemplateIntegrationsService.template_updated',
    )
    template_updated_mock = mocker.patch(
        'src.processes.views.template.AuditEventService.template_updated',
    )

    # act
    response = api_client.put(
        path=f'/templates/{template.id}',
        data={
            'id': template.id,
            'name': 'Draft again',
            'is_active': False,
            'kickoff': {
                'id': template.kickoff_instance.id,
                'fields': [],
            },
            'tasks': [],
        },
    )

    # assert
    assert response.status_code == 403
    update_workflows_mock.assert_not_called()
    template_integrations_updated_mock.assert_not_called()
    template_updated_mock.assert_not_called()
