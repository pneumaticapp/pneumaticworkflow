import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.generics.exceptions import BaseServiceException
from src.processes.services.templates.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_destroy__unauthenticated__unauthorized(api_client):

    """

    Unauthenticated request returns 401

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )

    # act
    response = api_client.delete(
        f'/templates/fieldsets/{fieldset.id}',
    )

    # assert
    assert response.status_code == 401


def test_destroy__expired_sub__permission_denied(api_client):

    """

    Expired subscription returns 403

    """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        f'/templates/fieldsets/{fieldset.id}',
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_destroy__billing_plan__permission_denied(api_client):

    """

    Billing plan permission denied returns 403

    """

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        f'/templates/fieldsets/{fieldset.id}',
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_destroy__users_overlimit__permission_denied(api_client):

    """

    Users overlimited returns 403

    """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1,
    )
    user = create_test_owner(account=account)
    create_test_not_admin(
        account=account,
        email='extra@pneumatic.app',
    )
    account.active_users = 2
    account.save()
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        f'/templates/fieldsets/{fieldset.id}',
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_destroy__non_admin__permission_denied(api_client):

    """

    Non-admin non-owner user returns 403

    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    user = create_test_not_admin(account=account)
    api_client.token_authenticate(user=user)

    # act
    response = api_client.delete(
        f'/templates/fieldsets/{fieldset.id}',
    )

    # assert
    assert response.status_code == 403


def test_destroy__ok(api_client, mocker):

    """

    Delete existing fieldset

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)

    # mock FieldSetTemplateService
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_delete_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.delete',
    )

    # act
    response = api_client.delete(
        f'/templates/fieldsets/{fieldset.id}',
    )

    # assert
    assert response.status_code == 204
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=mocker.ANY,
    )
    field_set_template_service_delete_mock.assert_called_once_with()


def test_destroy__service_exception__validation_error(api_client, mocker):

    """

    Service raises BaseServiceException returns validation error

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    error_message = 'Service error occurred'

    # mock FieldSetTemplateService
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_delete_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.delete',
        side_effect=BaseServiceException(message=error_message),
    )

    # act
    response = api_client.delete(
        f'/templates/fieldsets/{fieldset.id}',
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=mocker.ANY,
    )
    field_set_template_service_delete_mock.assert_called_once_with()


def test_destroy__not_existing__not_found(api_client):

    """

    Non-existent fieldset returns 404

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    nonexistent_id = 999999

    # act
    response = api_client.delete(
        f'/templates/fieldsets/{nonexistent_id}',
    )

    # assert
    assert response.status_code == 404
