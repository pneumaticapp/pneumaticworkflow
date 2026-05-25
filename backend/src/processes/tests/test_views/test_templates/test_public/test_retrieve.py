import pytest

from src.authentication.tokens import (
    EmbedToken,
    PublicToken,
)
from src.processes.enums import (
    FieldType,
)
from src.processes.models.templates.fields import FieldTemplate, \
    FieldTemplateSelection
from src.processes.tests.fixtures import (
    create_test_template,
    create_test_owner,
    create_test_dataset,
    create_test_account,
)

pytestmark = pytest.mark.django_db


class TestRetrievePublicTemplate:

    def test_retrieve__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200

        assert not response.data.get('id')
        assert response.data['name'] == template.name
        assert response.data['description'] == template.description
        assert response.data['show_captcha'] is False
        assert not response.data['kickoff'].get('id')
        assert len(response.data['kickoff']['fields']) == 1
        response_field = response.data['kickoff']['fields'][0]
        assert not response_field.get('id')
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_retrieve__field_with_selections__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        field_template = FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.DROPDOWN,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        selection = FieldTemplateSelection.objects.create(
            field_template=field_template,
            template=template,
            value='some value',
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200

        assert not response.data.get('id')
        assert len(response.data['kickoff']['fields']) == 1
        field_data = response.data['kickoff']['fields'][0]
        assert field_data['type'] == field_template.type
        assert field_data['name'] == field_template.name
        assert field_data['description'] == field_template.description
        assert field_data['is_required'] == field_template.is_required
        assert field_data['is_hidden'] == field_template.is_hidden
        assert field_data['order'] == field_template.order
        assert field_data['api_name'] == field_template.api_name
        assert field_data['default'] == ''
        assert field_data['selections'] == [selection.value]
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_retrieve__field_with_dataset__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        dataset = create_test_dataset(account=account, items_count=1)
        dataset_item = dataset.items.get(order=1)
        field_template = FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.DROPDOWN,
            kickoff=template.kickoff_instance,
            template=template,
            account=account,
            dataset=dataset,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200

        assert not response.data.get('id')
        assert len(response.data['kickoff']['fields']) == 1
        field_data = response.data['kickoff']['fields'][0]
        assert field_data['type'] == field_template.type
        assert field_data['name'] == field_template.name
        assert field_data['description'] == field_template.description
        assert field_data['is_required'] == field_template.is_required
        assert field_data['is_hidden'] == field_template.is_hidden
        assert field_data['order'] == field_template.order
        assert field_data['api_name'] == field_template.api_name
        assert field_data['default'] == ''
        assert field_data['selections'] == [dataset_item.value]
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_retrieve__field_with_dataset_and_selections__ok(
        self,
        api_client,
        mocker,
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        dataset = create_test_dataset(account=account, items_count=1)
        dataset_item = dataset.items.get(order=1)
        field_template = FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.DROPDOWN,
            kickoff=template.kickoff_instance,
            template=template,
            account=account,
            dataset=dataset,
        )
        selection = FieldTemplateSelection.objects.create(
            field_template=field_template,
            template=template,
            value='some value',
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        field_data = response.data['kickoff']['fields'][0]
        assert field_data['selections'] == [
            selection.value,
            dataset_item.value,
        ]
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_retrieve__not_authenticated__permission_denied(
        self,
        api_client,
        mocker,
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        auth_header_value = f'Token {template.public_id}'
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=None,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_not_called()

    def test_retrieve__show_captcha__ok(
        self,
        api_client,
        mocker,
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        response_1 = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )
        response_2 = api_client.post(
            path='/templates/public/run',
            data={'fields': {}},
            **{'X-Public-Authorization': auth_header_value},
        )
        anonymous_user_workflow_exists_mock = mocker.patch(
            'src.processes.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True,
        )

        # act
        response_3 = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response_1.status_code == 200
        assert response_2.status_code == 200
        assert response_3.status_code == 200
        assert response_3.data['show_captcha'] is True
        anonymous_user_workflow_exists_mock.assert_called_once()

    def test_retrieve__disable_captcha__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': False}
        anonymous_user_workflow_exists_mock = mocker.patch(
            'src.processes.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True,
        )

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
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
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1,
        )
        FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200

        assert not response.data.get('id')
        assert response.data['name'] == template.name
        assert response.data['description'] == template.description
        assert response.data['show_captcha'] is False
        assert not response.data['kickoff'].get('id')
        assert len(response.data['kickoff']['fields']) == 1
        response_field = response.data['kickoff']['fields'][0]
        assert not response_field.get('id')
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_retrieve__not_authenticated__permission_denied(
        self,
        api_client,
        mocker,
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1,
        )
        auth_header_value = f'Token {template.embed_id}'
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=None,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_not_called()

    def test_retrieve__show_captcha__ok(
        self,
        api_client,
        mocker,
    ):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1,
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        response_1 = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        response_2 = api_client.post(
            path='/templates/public/run',
            data={'fields': {}},
            **{'X-Public-Authorization': auth_header_value},
        )
        anonymous_user_workflow_exists_mock = mocker.patch(
            'src.processes.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True,
        )

        # act
        response_3 = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response_1.status_code == 200
        assert response_2.status_code == 204
        assert response_3.status_code == 200
        assert response_3.data['show_captcha'] is True
        anonymous_user_workflow_exists_mock.assert_called_once()

    def test_retrieve__disable_captcha__ok(self, api_client, mocker):

        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1,
        )
        FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            template=template,
            account=user.account,
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        get_token_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token,
        )
        get_template_mock = mocker.patch(
            'src.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template,
        )
        settings_mock = mocker.patch(
            'src.processes.views.public.template.settings',
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': False}
        anonymous_user_workflow_exists_mock = mocker.patch(
            'src.processes.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True,
        )

        # act
        response = api_client.get(
            path='/templates/public',
            **{'X-Public-Authorization': auth_header_value},
        )

        # assert
        assert response.status_code == 200
        assert response.data['show_captcha'] is False
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)
        anonymous_user_workflow_exists_mock.assert_not_called()
