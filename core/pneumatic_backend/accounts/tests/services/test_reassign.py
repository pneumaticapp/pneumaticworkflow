import pytest
from pneumatic_backend.accounts.enums import (
    BillingPlanType,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template,
    create_test_workflow,
)
from pneumatic_backend.accounts.tests.fixtures import (
    create_invited_user,
    create_test_user,
    create_test_account
)
from pneumatic_backend.accounts.services.reassign import (
    ReassignService
)
from pneumatic_backend.accounts.validators import user_is_performer
from pneumatic_backend.accounts.services import exceptions

pytestmark = pytest.mark.django_db


class TestReassignService:

    def test_init__different_account_users__raise_exception(self):

        # arrange
        old_user = create_test_user(
            is_admin=True,
            is_account_owner=False,
            email='admin1@test.test',
        )
        new_user = create_test_user(
            email='deleted@test.test',
            is_account_owner=False
        )

        # act
        with pytest.raises(exceptions.UserNotFoundException):
            ReassignService(
                new_user=new_user,
                old_user=old_user
            )

    def test_get_user_to_reassign__account_owner__ok(self):

        # arrange
        account_1 = create_test_account(
            name='transfer from',
            plan=BillingPlanType.FREEMIUM
        )
        create_test_user(
            account=account_1,
            is_admin=True,
            is_account_owner=False,
            email='admin1@test.test',
        )
        account_1_owner = create_test_user(
            account=account_1,
            is_account_owner=True,
            email='owner@test.test',
        )
        deleted_user = create_test_user(
            account=account_1,
            email='deleted@test.test',
            is_account_owner=False
        )

        # act
        service = ReassignService(old_user=deleted_user)

        # assert
        assert service.new_user.id == account_1_owner.id

    def test_get_user_to_reassign__admin__ok(self):

        # arrange
        account_1 = create_test_account(
            name='transfer from',
            plan=BillingPlanType.FREEMIUM
        )
        account_1_admin = create_test_user(
            account=account_1,
            is_admin=True,
            is_account_owner=False,
            email='admin1@test.test',
        )
        deleted_user = create_test_user(
            account=account_1,
            email='deleted@test.test',
            is_account_owner=True
        )

        # act
        service = ReassignService(old_user=deleted_user)

        # assert
        account_1_admin.refresh_from_db()
        assert service.new_user.id == account_1_admin.id
        assert account_1_admin.is_account_owner is True

    def test_get_user_to_reassign__invited__ok(self):

        # arrange
        account_1 = create_test_account(
            name='transfer from',
            plan=BillingPlanType.FREEMIUM
        )
        deleted_user = create_test_user(
            account=account_1,
            email='deleted@test.test',
            is_account_owner=True
        )
        invited_user = create_invited_user(deleted_user)

        # act
        service = ReassignService(old_user=deleted_user)

        # assert
        invited_user.refresh_from_db()
        assert service.new_user.id == invited_user.id
        assert invited_user.is_account_owner is True

    def test_get_user_to_reassign__last_user__raise_exception(self):

        # arrange
        account_1 = create_test_account(
            name='transfer from',
            plan=BillingPlanType.FREEMIUM
        )
        deleted_user = create_test_user(
            account=account_1,
            email='deleted@test.test',
            is_account_owner=True
        )

        # act
        with pytest.raises(exceptions.ReassignUserDoesNotExist):
            ReassignService(old_user=deleted_user)

    def test_reassign_everywhere__ok(self, mocker):

        # arrange
        account_1 = create_test_account(
            name='transfer from',
            plan=BillingPlanType.FREEMIUM
        )
        create_test_user(
            account=account_1,
            email='test@test.test',
            is_account_owner=False
        )
        deleted_user = create_test_user(
            account=account_1,
            email='deleted@test.test',
            is_account_owner=True
        )
        reassign_in_raw_performer_templates_mock = mocker.patch(
            'pneumatic_backend.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performer_templates'
        )
        reassign_in_template_owners_mock = mocker.patch(
            'pneumatic_backend.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_owners'
        )
        reassign_in_raw_performers_mock = mocker.patch(
            'pneumatic_backend.accounts.services.reassign.ReassignService.'
            '_reassign_in_raw_performers'
        )
        reassign_in_performers_mock = mocker.patch(
            'pneumatic_backend.accounts.services.reassign.ReassignService.'
            '_reassign_in_performers'
        )
        reassign_in_workflow_members_mock = mocker.patch(
            'pneumatic_backend.accounts.services.reassign.ReassignService.'
            '_reassign_in_workflow_members'
        )
        reassign_in_template_conditions_mock = mocker.patch(
            'pneumatic_backend.accounts.services.reassign.ReassignService.'
            '_reassign_in_template_conditions'
        )
        reassign_in_conditions_mock = mocker.patch(
            'pneumatic_backend.accounts.services.reassign.ReassignService.'
            '_reassign_in_conditions'
        )
        complete_tasks_mock = mocker.patch(
            'pneumatic_backend.processes.tasks.tasks.'
            'complete_tasks.delay'
        )
        service = ReassignService(old_user=deleted_user)

        # act
        service.reassign_everywhere()

        # assert
        reassign_in_raw_performer_templates_mock.assert_called_once()
        reassign_in_template_owners_mock.assert_called_once()
        reassign_in_raw_performers_mock.assert_called_once()
        reassign_in_performers_mock.assert_called_once()
        reassign_in_workflow_members_mock.assert_called_once()
        reassign_in_template_conditions_mock.assert_called_once()
        reassign_in_conditions_mock.assert_called_once()
        complete_tasks_mock.assert_called_once()

    @pytest.mark.parametrize(
        'plan', {
            BillingPlanType.FREEMIUM,
            BillingPlanType.PREMIUM
        }
    )
    def test_reassign_everywhere__user_is_not_performer__ok(
        self,
        plan
    ):

        # arrange
        account = create_test_account(plan=plan)
        create_test_user(
            account=account,
            is_account_owner=True
        )
        deleted_user = create_test_user(
            account=account,
            email='deleted@test.test',
            is_account_owner=False
        )
        template_1 = create_test_template(user=deleted_user, is_active=True)
        template_2 = create_test_template(user=deleted_user, is_active=False)
        create_test_workflow(
            user=deleted_user,
            template=template_1
        )
        create_test_workflow(
            user=deleted_user,
            template=template_2
        )
        service = ReassignService(old_user=deleted_user)

        # act
        service.reassign_everywhere()

        # assert
        assert user_is_performer(deleted_user) is False
