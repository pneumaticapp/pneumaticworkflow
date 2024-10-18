import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
)
from pneumatic_backend.processes.models import (
    FieldTemplate,
)
from pneumatic_backend.processes.enums import (
    FieldType
)
from pneumatic_backend.authentication.tokens import (
    PublicToken,
    EmbedToken,
)
pytestmark = pytest.mark.django_db


class TestRetrievePublicTemplate:

    def test_retrieve__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            template=template,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200

        assert not response.data.get('id')
        assert response.data['name'] == template.name
        assert response.data['description'] == template.description
        assert response.data['show_captcha'] is False
        assert not response.data['kickoff'].get('id')
        assert response.data['kickoff']['description'] == (
            template.kickoff_instance.description
        )
        assert len(response.data['kickoff']['fields']) == 1
        response_field = response.data['kickoff']['fields'][0]
        assert not response_field.get('id')
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_retrieve__not_authenticated__permission_denied(
        self,
        api_client,
        mocker
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.public_id}'
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=None
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_not_called()

    def test_retrieve__show_captcha__ok(
        self,
        api_client,
        mocker,
        session_mock,
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        response_1 = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )
        response_2 = api_client.post(
            path=f'/templates/public/run',
            data={'fields': {}},
            **{'X-Public-Authorization': auth_header_value}
        )
        anonymous_user_workflow_exists_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True
        )

        # act
        response_3 = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response_1.status_code == 200
        assert response_2.status_code == 200
        assert response_3.status_code == 200
        assert response_3.data['show_captcha'] is True
        anonymous_user_workflow_exists_mock.assert_called_once()

    def test_retrieve__disable_captcha__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': False}
        anonymous_user_workflow_exists_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True
        )

        # act
        response = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        assert response.data['show_captcha'] is False
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)
        anonymous_user_workflow_exists_mock.assert_not_called()


class TestRetrieveEmbedTemplate:

    def test_retrieve__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1
        )
        FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            template=template,
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200

        assert not response.data.get('id')
        assert response.data['name'] == template.name
        assert response.data['description'] == template.description
        assert response.data['show_captcha'] is False
        assert not response.data['kickoff'].get('id')
        assert response.data['kickoff']['description'] == (
            template.kickoff_instance.description
        )
        assert len(response.data['kickoff']['fields']) == 1
        response_field = response.data['kickoff']['fields'][0]
        assert not response_field.get('id')
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_retrieve__not_authenticated__permission_denied(
        self,
        api_client,
        mocker
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.embed_id}'
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=None
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_not_called()

    def test_retrieve__show_captcha__ok(
        self,
        api_client,
        mocker,
        session_mock,
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        response_1 = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        response_2 = api_client.post(
            path=f'/templates/public/run',
            data={'fields': {}},
            **{'X-Public-Authorization': auth_header_value}
        )
        anonymous_user_workflow_exists_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True
        )

        # act
        response_3 = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response_1.status_code == 200
        assert response_2.status_code == 204
        assert response_3.status_code == 200
        assert response_3.data['show_captcha'] is True
        anonymous_user_workflow_exists_mock.assert_called_once()

    def test_retrieve__disable_captcha__ok(self, api_client, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1
        )
        FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            template=template,
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': False}
        anonymous_user_workflow_exists_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True
        )

        # act
        response = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        assert response.data['show_captcha'] is False
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)
        anonymous_user_workflow_exists_mock.assert_not_called()
