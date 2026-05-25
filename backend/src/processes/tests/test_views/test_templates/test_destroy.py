import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import TemplateType
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


class TestDestroyTemplate:

    def test_destroy__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user)
        workflow = create_test_workflow(
            user=user,
            template=template,
        )
        api_request_mock = mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.api_request',
        )
        analysis_mock = mocker.patch(
            'src.analysis.services.AnalyticService'
            '.templates_deleted',
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.delete(f'/templates/{template.id}')

        # assert
        assert response.status_code == 204
        assert not Template.objects.filter(id=template.id).exists()
        account.refresh_from_db()
        workflow.refresh_from_db()
        assert workflow.is_legacy_template is True
        assert workflow.legacy_template_name == template.name
        template.refresh_from_db()
        analysis_mock.assert_called_once_with(
            user=user,
            template=template,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        api_request_mock.assert_not_called()

    def test_destroy__type_onboarding_admin__not_found(
        self,
        mocker,
        api_client,
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            type_=TemplateType.ONBOARDING_ADMIN,
        )
        analysis_mock = mocker.patch(
            'src.analysis.services.AnalyticService'
            '.templates_deleted',
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.delete(f'/templates/{template.id}')

        # assert
        assert response.status_code == 404
        analysis_mock.assert_not_called()
