import pytest
from pneumatic_backend.applications.models import Integration
from pneumatic_backend.processes.models import SystemTemplate
from pneumatic_backend.processes.tests.fixtures import create_test_user


def create_test_system_template():
    return SystemTemplate.objects.create(
        name='test',
        order=5,
        is_active=True,
    )


pytestmark = pytest.mark.django_db


class TestListIntegrations:
    def test_list(self, api_client):
        user = create_test_user()
        first_integration = Integration.objects.create(
            name='First integration',
            short_description='This is short description',
            long_description='This is long description',
            button_text='Button',
            url='https://google.com/logo.svg',
            order=10,
            is_active=True,
        )
        second_integration = Integration.objects.create(
            name='Second integration',
            short_description='This is short description',
            long_description='This is long description',
            button_text='Button',
            url='https://google.com/logo.svg',
            order=9,
            is_active=True
        )
        Integration.objects.create(
            name='Inactive integration',
            short_description='This is short description',
            long_description='This is long description',
            button_text='Button',
            url='https://google.com/logo.svg',
            order=11
        )

        api_client.token_authenticate(user)
        response = api_client.get('/applications/integrations')

        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]['id'] == first_integration.id
        assert response.data[0]['name'] == first_integration.name
        assert response.data[0]['logo'] == first_integration.logo
        assert (response.data[0]['short_description'] ==
                first_integration.short_description)
        assert response.data[1]['id'] == second_integration.id
        assert response.data[1]['name'] == second_integration.name
        assert response.data[1]['logo'] == second_integration.logo
        assert (response.data[1]['short_description'] ==
                second_integration.short_description)


class TestRetrieveIntegration:
    def test_retrieve(self, api_client):
        user = create_test_user()
        integration = Integration.objects.create(
            name='First integration',
            short_description='This is short description',
            long_description='This is long description',
            button_text='Button',
            url='https://google.com/logo.svg',
            order=10,
            is_active=True,
        )

        api_client.token_authenticate(user)
        response = api_client.get(
            f'/applications/integrations/{integration.id}'
        )

        assert response.status_code == 200
        assert response.data['id'] == integration.id
        assert response.data['name'] == integration.name
        assert (response.data['long_description'] ==
                integration.long_description)
        assert response.data['logo'] == integration.logo
        assert response.data['button_text'] == integration.button_text
        assert response.data['url'] == integration.url

    def test_retrieve_inactive_integration(self, api_client):
        user = create_test_user()
        integration = Integration.objects.create(
            name='First integration',
            short_description='This is short description',
            long_description='This is long description',
            button_text='Button',
            url='https://google.com/logo.svg',
            order=10,
        )

        api_client.token_authenticate(user)
        response = api_client.get(
            f'/applications/integrations/{integration.id}'
        )

        assert response.status_code == 404
