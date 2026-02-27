import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from src.processes.enums import StarterType
from src.processes.models.templates.starter import TemplateStarter
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
)

UserModel = get_user_model()
pytestmark = [pytest.mark.django_db]


class TestTemplateStartersAPI:

    def test_starters_list__template_without_starters__returns_empty_list(
        self, api_client,
    ):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account, is_admin=True)
        template = create_test_template(template_owner)
        api_client.token_authenticate(template_owner)
        url = reverse('templates-starters', args=[template.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_starters_list__template_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account, is_admin=True)
        template = create_test_template(template_owner)
        starter_user = create_test_user(
            account=account,
            email='starter@test.com',
        )
        group = create_test_group(account=account, name='Starters Group')

        # Create starters
        user_starter = TemplateStarter.objects.create(
            template=template,
            type=StarterType.USER,
            user=starter_user,
            account=account,
        )
        group_starter = TemplateStarter.objects.create(
            template=template,
            type=StarterType.GROUP,
            group=group,
            account=account,
        )
        api_client.token_authenticate(template_owner)
        url = reverse('templates-starters', args=[template.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

        # Check user starter
        user_starter_data = next(
            (item for item in data if item['type'] == StarterType.USER),
            None,
        )
        assert user_starter_data is not None
        assert user_starter_data['id'] == user_starter.id
        assert (
            user_starter_data['user_details']['email'] == starter_user.email
        )
        assert user_starter_data['group_details'] is None

        # Check group starter
        group_starter_data = next(
            (item for item in data if item['type'] == StarterType.GROUP),
            None,
        )
        assert group_starter_data is not None
        assert group_starter_data['id'] == group_starter.id
        assert group_starter_data['group_details']['name'] == group.name
        assert group_starter_data['user_details'] is None

    def test_starters_list__not_template_owner__forbidden(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account, is_admin=True)
        template = create_test_template(template_owner)
        random_user = create_test_user(
            account=account,
            email='random@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        api_client.token_authenticate(random_user)
        url = reverse('templates-starters', args=[template.id])

        # act
        response = api_client.get(url)

        # assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_user_starter__admin_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account, is_admin=True)
        template = create_test_template(template_owner)
        starter_user = create_test_user(
            account=account,
            email='starter@test.com',
        )
        api_client.token_authenticate(template_owner)
        url = reverse('templates-add-starter', args=[template.id])

        # act
        response = api_client.post(
            url,
            data={'type': StarterType.USER, 'user_id': starter_user.id},
        )

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['type'] == StarterType.USER
        assert data['user_details']['email'] == starter_user.email

        # Verify starter was created in database
        assert TemplateStarter.objects.filter(
            template=template,
            user=starter_user,
            type=StarterType.USER,
        ).exists()

    def test_add_group_starter__admin_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account, is_admin=True)
        template = create_test_template(template_owner)
        group = create_test_group(account=account, name='Starters Group')
        api_client.token_authenticate(template_owner)
        url = reverse('templates-add-starter', args=[template.id])

        # act
        response = api_client.post(
            url,
            data={'type': StarterType.GROUP, 'group_id': group.id},
        )

        # assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['type'] == StarterType.GROUP
        assert data['group_details']['name'] == group.name

        # Verify starter was created in database
        assert TemplateStarter.objects.filter(
            template=template,
            group=group,
            type=StarterType.GROUP,
        ).exists()

    def test_add_starter__not_admin__forbidden(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account, is_admin=True)
        template = create_test_template(template_owner)
        non_admin_user = create_test_user(
            account=account,
            email='nonadmin@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        starter_user = create_test_user(
            account=account,
            email='starter@test.com',
        )
        api_client.token_authenticate(non_admin_user)
        url = reverse('templates-add-starter', args=[template.id])

        # act
        response = api_client.post(
            url,
            data={'type': StarterType.USER, 'user_id': starter_user.id},
        )

        # assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_remove_starter__admin_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account, is_admin=True)
        template = create_test_template(template_owner)
        starter_user = create_test_user(
            account=account,
            email='starter@test.com',
        )
        starter = TemplateStarter.objects.create(
            template=template,
            type=StarterType.USER,
            user=starter_user,
            account=account,
        )
        api_client.token_authenticate(template_owner)
        url = reverse(
            'templates-remove-starter',
            args=[template.id, starter.id],
        )

        # act
        response = api_client.delete(url)

        # assert
        assert response.status_code == status.HTTP_200_OK
        assert not TemplateStarter.objects.filter(
            id=starter.id,
            is_deleted=False,
        ).exists()

    def test_remove_starter__not_admin__forbidden(self, api_client):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account, is_admin=True)
        template = create_test_template(template_owner)
        starter_user = create_test_user(
            account=account,
            email='starter@test.com',
        )
        starter = TemplateStarter.objects.create(
            template=template,
            type=StarterType.USER,
            user=starter_user,
            account=account,
        )
        non_admin_user = create_test_user(
            account=account,
            email='nonadmin@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        api_client.token_authenticate(non_admin_user)
        url = reverse(
            'templates-remove-starter',
            args=[template.id, starter.id],
        )

        # act
        response = api_client.delete(url)

        # assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert TemplateStarter.objects.filter(
            id=starter.id,
            is_deleted=False,
        ).exists()
