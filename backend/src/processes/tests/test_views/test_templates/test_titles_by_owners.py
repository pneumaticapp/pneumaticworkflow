import pytest

from src.accounts.enums import BillingPlanType
from src.processes.enums import OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.starter import TemplateStarter
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
)

pytestmark = pytest.mark.django_db


class TestTitlesByOwners:

    def test_titles_by_owners__owner_user__ok(self, api_client):
        """
        User who is a direct owner (type=user) should see the template.
        """

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/templates/titles-by-owners')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template.id

    def test_titles_by_owners__owner_group__ok(self, api_client):
        """
        User who is an owner via group membership should see the template.
        """

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        group_member = create_test_user(
            account=account,
            email='member@test.test',
            is_account_owner=False,
        )
        group = create_test_group(
            account=account,
            users=[group_member],
        )
        template = create_test_template(
            user=owner,
            is_active=True,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group=group,
        )
        api_client.token_authenticate(group_member)

        # act
        response = api_client.get('/templates/titles-by-owners')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template.id

    def test_titles_by_owners__starter_user__not_in_list(self, api_client):
        """
        User who is only a starter (not owner) should NOT see the template.
        """

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        starter_user = create_test_user(
            account=account,
            email='starter@test.test',
            is_account_owner=False,
        )
        template = create_test_template(
            user=owner,
            is_active=True,
        )
        TemplateStarter.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=starter_user.id,
        )
        api_client.token_authenticate(starter_user)

        # act
        response = api_client.get('/templates/titles-by-owners')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_titles_by_owners__viewer_user__not_in_list(self, api_client):
        """
        User who is only a viewer (not owner) should NOT see the template.
        """

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.test',
            is_account_owner=False,
        )
        template = create_test_template(
            user=owner,
            is_active=True,
        )
        TemplateViewer.objects.create(
            template=template,
            account=account,
            type=OwnerType.USER,
            user_id=viewer_user.id,
        )
        api_client.token_authenticate(viewer_user)

        # act
        response = api_client.get('/templates/titles-by-owners')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_titles_by_owners__starter_group__not_in_list(self, api_client):
        """
        User who is a starter via group (not owner) should NOT see the
        template.
        """

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        starter_user = create_test_user(
            account=account,
            email='starter@test.test',
            is_account_owner=False,
        )
        group = create_test_group(
            account=account,
            users=[starter_user],
        )
        template = create_test_template(
            user=owner,
            is_active=True,
        )
        TemplateStarter.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group=group,
        )
        api_client.token_authenticate(starter_user)

        # act
        response = api_client.get('/templates/titles-by-owners')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_titles_by_owners__pagination__ok(self, api_client):
        """
        Pagination should work correctly.
        """

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        create_test_template(user, is_active=True)
        create_test_template(user, is_active=True)
        template = create_test_template(user, is_active=True)
        create_test_template(user, is_active=True)

        # act
        response = api_client.get(
            path='/templates/titles-by-owners',
            data={
                'limit': 1,
                'offset': 2,
                'ordering': 'date',
            },
        )

        # assert
        assert response.status_code == 200
        assert response.data['count'] == 4
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == template.id

    def test_titles_by_owners__ordering__ok(self, api_client):
        """
        Ordering by name should work correctly.
        """

        # arrange
        user = create_test_user()
        template_a = create_test_template(user, name='Aa1')
        template_b = create_test_template(user, name='Bb2')
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/templates/titles-by-owners?ordering=name')

        # assert
        assert response.status_code == 200
        assert response.data[0]['id'] == template_a.id
        assert response.data[1]['id'] == template_b.id

    def test_titles_by_owners__search__ok(self, api_client):
        """
        Search should work correctly.
        """

        # arrange
        user = create_test_user()
        template = create_test_template(user, name='SearchableTemplate')
        create_test_template(user, name='OtherTemplate')
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/templates/titles-by-owners?search=Searchable',
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template.id

    def test_titles_by_owners__filter_is_active__ok(self, api_client):
        """
        Filter by is_active should work correctly.
        """

        # arrange
        user = create_test_user()
        active_template = create_test_template(user, is_active=True)
        create_test_template(user, is_active=False)
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/templates/titles-by-owners?is_active=true',
        )

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == active_template.id

    def test_titles_by_owners__multiple_owners__no_duplicates(
        self,
        api_client,
    ):
        """
        When user is owner both directly and via group,
        template should appear only once.
        """

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(
            account=account,
            is_account_owner=True,
        )
        group = create_test_group(
            account=account,
            users=[user],
        )
        template = create_test_template(
            user=user,
            is_active=True,
        )
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group=group,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/templates/titles-by-owners')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == template.id

    def test_titles_by_owners__other_account__not_visible(self, api_client):
        """
        Templates from other accounts should not be visible.
        """

        # arrange
        other_user = create_test_user(email='other@test.test')
        create_test_template(
            user=other_user,
            is_active=True,
        )
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/templates/titles-by-owners')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_titles_by_owners__deleted_owner__not_in_list(self, api_client):
        """
        If owner record is deleted (is_deleted=True),
        user should not see the template.
        """

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        TemplateOwner.objects.filter(
            template=template,
            user_id=user.id,
        ).update(is_deleted=True)
        api_client.token_authenticate(user)

        # act
        response = api_client.get('/templates/titles-by-owners')

        # assert
        assert response.status_code == 200
        assert len(response.data) == 0
