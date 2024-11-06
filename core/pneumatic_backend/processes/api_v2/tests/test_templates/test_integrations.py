import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
)
from pneumatic_backend.processes.entities import TemplateIntegrationsData
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.api_v2.views.template import (
    TemplateIntegrationsService
)
from pneumatic_backend.generics.messages import (
    MSG_GE_0003
)


pytestmark = pytest.mark.django_db


class TestTemplateIntegrations:

    def test_template_integrations__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user=user, is_active=True)
        api_client.token_authenticate(user)
        integration_data = TemplateIntegrationsData(
            id=template.id,
            webhooks=True,
            shared=True,
            zapier=True,
            api=False
        )
        service_init_mock = mocker.patch.object(
            TemplateIntegrationsService,
            attribute='__init__',
            return_value=None
        )
        service_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService'
            '.get_template_integrations_data',
            return_value=integration_data
        )

        # act
        response = api_client.get(f'/templates/{template.id}/integrations')

        # assert
        assert response.status_code == 200
        assert response.data == integration_data
        service_init_mock.assert_called_once_with(
            account=user.account,
            is_superuser=False,
            user=user
        )
        service_mock.assert_called_once_with(
            template_id=template.id
        )

    def test_template_integrations__non_existent_template__not_found(
        self,
        api_client,
        mocker
    ):

        # arrange
        user_2 = create_test_user(email='test@test.test')
        template = create_test_template(user=user_2, is_active=True)
        user = create_test_user()
        api_client.token_authenticate(user)
        service_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService'
            '.get_template_integrations_data'
        )

        # act
        response = api_client.get(f'/templates/{template.id}/integrations')

        # assert
        assert response.status_code == 404
        service_mock.assert_not_called()

    def test_template_integrations__not_admin__permission_denied(
        self,
        api_client,
        mocker
    ):

        # arrange
        user = create_test_user(is_admin=False, is_account_owner=False)
        template = create_test_template(user=user, is_active=True)
        api_client.token_authenticate(user)
        service_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService'
            '.get_template_integrations_data'
        )

        # act
        response = api_client.get(f'/templates/{template.id}/integrations')

        # assert
        assert response.status_code == 403
        service_mock.assert_not_called()


class TestIntegrations:

    def test_list_integrations__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        integrations_data = [
            TemplateIntegrationsData(
                id=1,
                webhooks=True,
                shared=True,
                zapier=True,
                api=False
            ),
            TemplateIntegrationsData(
                id=2,
                webhooks=True,
                shared=True,
                zapier=True,
                api=False
            )
        ]
        service_init_mock = mocker.patch.object(
            TemplateIntegrationsService,
            attribute='__init__',
            return_value=None
        )
        service_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.get_integrations',
            return_value=integrations_data
        )

        # act
        response = api_client.get(f'/templates/integrations')

        # assert
        assert response.status_code == 200
        assert response.data == integrations_data
        service_init_mock.assert_called_once_with(
            account=user.account,
            is_superuser=False,
            user=user
        )
        service_mock.assert_called_once_with()

    def test_list_template_integrations__not_admin__permission_denied(
        self,
        api_client,
        mocker
    ):

        # arrange
        user = create_test_user(is_admin=False, is_account_owner=False)
        api_client.token_authenticate(user)
        service_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.get_integrations'
        )

        # act
        response = api_client.get(f'/templates/integrations')

        # assert
        assert response.status_code == 403
        service_mock.assert_not_called()

    def test_list_template_integrations__filter_by_template__ok(
        self,
        api_client,
        mocker
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(user=user, is_active=True)
        integrations_data = [
            TemplateIntegrationsData(
                id=template.id,
                webhooks=True,
                shared=True,
                zapier=True,
                api=False
            ),
        ]
        service_init_mock = mocker.patch.object(
            TemplateIntegrationsService,
            attribute='__init__',
            return_value=None
        )
        service_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.get_integrations',
            return_value=integrations_data
        )

        # act
        response = api_client.get(
            f'/templates/integrations?template_id={template.id}'
        )

        # assert
        assert response.status_code == 200
        assert response.data == integrations_data
        service_init_mock.assert_called_once_with(
            account=user.account,
            is_superuser=False,
            user=user
        )
        service_mock.assert_called_once_with(
            template_id=[template.id]
        )

    def test_list_template_integrations__filter_by_many_template__ok(
        self,
        api_client,
        mocker
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        template = create_test_template(user=user, is_active=True)
        template_2 = create_test_template(user=user, is_active=True)
        integrations_data = [
            TemplateIntegrationsData(
                id=template.id,
                webhooks=True,
                shared=True,
                zapier=True,
                api=False
            ),
            TemplateIntegrationsData(
                id=template_2.id,
                webhooks=True,
                shared=True,
                zapier=True,
                api=False
            )
        ]
        service_init_mock = mocker.patch.object(
            TemplateIntegrationsService,
            attribute='__init__',
            return_value=None
        )
        service_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.get_integrations',
            return_value=integrations_data
        )

        # act
        response = api_client.get(
            path='/templates/integrations',
            data={'template_id': f'{template.id}, {template_2.id}'}
        )

        # assert
        assert response.status_code == 200
        service_init_mock.assert_called_once_with(
            account=user.account,
            is_superuser=False,
            user=user
        )
        service_mock.assert_called_once_with(
            template_id=[template.id, template_2.id]
        )

    def test_list__filter_by_invalid_template__validation_error(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/workflows?template_id=1,undefined')

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_GE_0003
        assert response.data['details']['reason'] == MSG_GE_0003
        assert response.data['details']['name'] == 'template_id'
