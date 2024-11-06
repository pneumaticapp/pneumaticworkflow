# pylint:disable=redefined-outer-name
import pytest
from pneumatic_backend.processes.models import Template
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
    create_test_account
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.views.template import (
    TemplateIntegrationsService
)
from pneumatic_backend.processes.enums import TemplateType

pytestmark = pytest.mark.django_db


class TestDestroyTemplate:

    def test_destroy__ok(
        self,
        mocker,
        api_client,
        analytics_mock
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user)
        workflow = create_test_workflow(
            user=user,
            template=template
        )
        api_request_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.api_request',
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.delete(f'/templates/{template.id}')

        # assert
        assert response.status_code == 204
        assert not Template.objects.filter(id=template.id).exists()
        account.refresh_from_db()
        assert account.active_templates == 0
        workflow.refresh_from_db()
        assert workflow.is_legacy_template is True
        assert workflow.legacy_template_name == template.name
        template.refresh_from_db()
        analytics_mock.templates_deleted.assert_called_once_with(
            user=user,
            template=template,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        api_request_mock.assert_not_called()

    def test_destroy__type_onboarding_admin__not_found(
        self,
        api_client,
        analytics_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            type_=TemplateType.ONBOARDING_ADMIN
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.delete(f'/templates/{template.id}')

        # assert
        assert response.status_code == 404
        analytics_mock.assert_not_called()

    def test_destroy__api_request__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user)
        user_agent = 'Mozilla'
        get_user_agent_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.template.get_user_agent',
            return_value=user_agent
        )
        service_init_mock = mocker.patch.object(
            TemplateIntegrationsService,
            attribute='__init__',
            return_value=None
        )
        api_request_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.api_request',
        )
        api_client.token_authenticate(
            user=user,
            token_type=AuthTokenType.API
        )

        # act
        response = api_client.delete(f'/templates/{template.id}')

        # assert
        assert response.status_code == 204
        get_user_agent_mock.assert_called_once()
        api_request_mock.assert_called_once_with(
            template=template,
            user_agent=user_agent
        )
        service_init_mock.assert_called_once_with(
            account=user.account,
            is_superuser=False,
            user=user
        )
