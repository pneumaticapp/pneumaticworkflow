"""
Tests for non-admin template owners.

Non-admin users who are template owners should have viewer-level access:
- Cannot edit templates
- Cannot retrieve template details (edit view)
- Can run workflows
- Can view workflows (read-only)
- Cannot edit workflows
- Cannot manage task performers
- Cannot create presets
"""
import pytest

from src.processes.enums import (
    OwnerType,
    PerformerType,
)
from src.processes.messages import template as messages
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
)

pytestmark = pytest.mark.django_db


class TestNonAdminOwnerTemplateRetrieve:
    """Non-admin owners cannot retrieve template details (edit view)."""

    def test_retrieve__non_admin_owner__permission_denied(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 403
        assert response.data['detail'] == messages.MSG_PT_0023

    def test_retrieve__non_admin_owner_via_group__permission_denied(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_user = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        group = create_test_group(account, users=[non_admin_user])
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group=group,
        )
        api_client.token_authenticate(non_admin_user)

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 403
        assert response.data['detail'] == messages.MSG_PT_0023

    def test_retrieve__admin_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        api_client.token_authenticate(admin_owner)

        # act
        response = api_client.get(f'/templates/{template.id}')

        # assert
        assert response.status_code == 200
        assert response.data['id'] == template.id


class TestNonAdminOwnerTemplateUpdate:
    """Non-admin owners cannot update templates."""

    def test_update__non_admin_owner__permission_denied(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'name': 'Updated Name',
                'is_active': True,
                'kickoff': {},
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': str(admin_owner.id),
                    },
                ],
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Task 1',
                        'api_name': template.tasks.first().api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': admin_owner.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 403

    def test_update__admin_owner__ok(self, api_client, mocker):
        # arrange
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        api_client.token_authenticate(admin_owner)
        new_name = 'Updated Template Name'

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'name': new_name,
                'is_active': True,
                'kickoff': {},
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': str(admin_owner.id),
                    },
                ],
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Task 1',
                        'api_name': template.tasks.first().api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': admin_owner.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        assert response.data['name'] == new_name


class TestNonAdminOwnerTemplateClone:
    """Non-admin owners cannot clone templates."""

    def test_clone__non_admin_owner__permission_denied(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.post(f'/templates/{template.id}/clone')

        # assert
        assert response.status_code == 403


class TestNonAdminOwnerTemplateDestroy:
    """Non-admin owners cannot delete templates."""

    def test_destroy__non_admin_owner__permission_denied(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.delete(f'/templates/{template.id}')

        # assert
        assert response.status_code == 403


class TestNonAdminOwnerTemplateRun:
    """Non-admin owners CAN run workflows from templates."""

    def test_run__non_admin_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={'name': 'Test Workflow'},
        )

        # assert
        assert response.status_code == 200
        assert response.data['name'] == 'Test Workflow'

    def test_run__non_admin_owner_via_group__ok(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_user = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        group = create_test_group(account, users=[non_admin_user])
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group=group,
        )
        api_client.token_authenticate(non_admin_user)

        # act
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={'name': 'Test Workflow'},
        )

        # assert
        assert response.status_code == 200
        assert response.data['name'] == 'Test Workflow'


class TestNonAdminOwnerTemplatePresets:
    """Non-admin owners can read presets but cannot create them."""

    def test_presets_list__non_admin_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.get(f'/templates/{template.id}/presets')

        # assert
        assert response.status_code == 200

    def test_preset_create__non_admin_owner__permission_denied(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.post(
            f'/templates/{template.id}/preset',
            data={'name': 'Test Preset'},
        )

        # assert
        assert response.status_code == 403


class TestNonAdminOwnerCanBeAddedAsOwner:
    """Non-admin users CAN be added as template owners."""

    def test_create_template__non_admin_owner__ok(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_user = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        api_client.token_authenticate(admin_owner)

        # act
        response = api_client.post(
            '/templates',
            data={
                'name': 'Template with non-admin owner',
                'is_active': True,
                'kickoff': {},
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': str(admin_owner.id),
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': str(non_admin_user.id),
                    },
                ],
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Task 1',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': admin_owner.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        template = Template.objects.get(id=response.data['id'])
        owner_user_ids = list(
            template.owners.filter(type=OwnerType.USER)
            .values_list('user_id', flat=True),
        )
        assert admin_owner.id in owner_user_ids
        assert non_admin_user.id in owner_user_ids

    def test_update_template__add_non_admin_owner__ok(
        self, api_client, mocker,
    ):
        # arrange
        mocker.patch(
            'src.processes.services.templates.'
            'integrations.TemplateIntegrationsService.template_updated',
        )
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_user = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        api_client.token_authenticate(admin_owner)

        # act
        response = api_client.put(
            f'/templates/{template.id}',
            data={
                'name': template.name,
                'is_active': True,
                'kickoff': {},
                'owners': [
                    {
                        'type': OwnerType.USER,
                        'source_id': str(admin_owner.id),
                    },
                    {
                        'type': OwnerType.USER,
                        'source_id': str(non_admin_user.id),
                    },
                ],
                'tasks': [
                    {
                        'number': 1,
                        'name': 'Task 1',
                        'api_name': template.tasks.first().api_name,
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': admin_owner.id,
                            },
                        ],
                    },
                ],
            },
        )

        # assert
        assert response.status_code == 200
        template.refresh_from_db()
        owner_user_ids = list(
            template.owners.filter(type=OwnerType.USER)
            .values_list('user_id', flat=True),
        )
        assert admin_owner.id in owner_user_ids
        assert non_admin_user.id in owner_user_ids


class TestNonAdminOwnerTemplateList:
    """Non-admin owners can see templates in list."""

    def test_list__non_admin_owner__sees_template(self, api_client):
        # arrange
        account = create_test_account()
        admin_owner = create_test_user(
            email='admin@test.test',
            account=account,
            is_admin=True,
            is_account_owner=True,
        )
        non_admin_owner = create_test_user(
            email='nonadmin@test.test',
            account=account,
            is_admin=False,
            is_account_owner=False,
        )
        template = create_test_template(
            user=admin_owner,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user=non_admin_owner,
        )
        api_client.token_authenticate(non_admin_owner)

        # act
        response = api_client.get('/templates')

        # assert
        assert response.status_code == 200
        template_ids = [t['id'] for t in response.data]
        assert template.id in template_ids
