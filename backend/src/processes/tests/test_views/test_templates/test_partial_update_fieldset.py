import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.generics.exceptions import BaseServiceException
from src.processes.enums import (
    FieldSetLayout,
    LabelPosition,
)
from src.processes.services.templates.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_partial_update__unauthenticated__unauthorized(api_client):

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
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': 'Updated Fieldset',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 401


def test_partial_update__expired_sub__permission_denied(api_client):

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
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Updated Fieldset',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_partial_update__billing_plan__permission_denied(api_client):

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
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Updated Fieldset',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_partial_update__users_overlimit__permission_denied(api_client):

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
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Updated Fieldset',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_partial_update__non_admin__permission_denied(api_client):

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
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    user = create_test_not_admin(account=account)
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Updated Fieldset',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403


def test_partial_update__min_data__ok(api_client, mocker):

    """

    Partial update with minimal request data

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Updated Name',
    }

    # mock FieldSetTemplateService
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id
    assert response.data['name'] == 'Test Fieldset'
    assert response.data['description'] == ''
    assert response.data['order'] == 0
    assert response.data['layout'] == FieldSetLayout.VERTICAL
    assert response.data['label_position'] == LabelPosition.TOP
    assert response.data['api_name'] == fieldset.api_name
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=mocker.ANY,
    )
    field_set_template_service_partial_update_mock.assert_called_once_with(
        name='Updated Name',
    )


def test_partial_update__full_data__ok(api_client, mocker):

    """

    Partial update with full request data

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Full Updated Fieldset',
        'description': 'Updated description',
        'order': 10,
        'layout': FieldSetLayout.HORIZONTAL,
        'label_position': LabelPosition.LEFT,
    }

    # mock FieldSetTemplateService
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id
    assert response.data['api_name'] == fieldset.api_name
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=mocker.ANY,
    )
    field_set_template_service_partial_update_mock.assert_called_once_with(
        name='Full Updated Fieldset',
        description='Updated description',
        order=10,
        layout=FieldSetLayout.HORIZONTAL,
        label_position=LabelPosition.LEFT,
    )


def test_partial_update__invalid_name__validation_error(api_client):

    """

    Invalid name field returns validation error

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': '',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['details']['name'] == 'name'


def test_partial_update__invalid_layout__validation_error(api_client):

    """

    Invalid layout field returns validation error

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'layout': 'invalid_layout',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['details']['name'] == 'layout'


def test_partial_update__invalid_label_pos__validation_error(api_client):

    """

    Invalid label_position field returns validation error

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'label_position': 'invalid_position',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['details']['name'] == 'label_position'


def test_partial_update__service_exception__validation_error(
    api_client,
    mocker,
):

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
    fieldset = create_test_fieldset(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Updated Fieldset',
    }
    error_message = 'Service error occurred'

    # mock FieldSetTemplateService
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        side_effect=BaseServiceException(message=error_message),
    )

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
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
    field_set_template_service_partial_update_mock.assert_called_once_with(
        name='Updated Fieldset',
    )


def test_partial_update__not_existing__not_found(api_client):

    """

    Non-existent fieldset returns 404

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    nonexistent_id = 999999
    data = {
        'name': 'Updated Fieldset',
    }

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{nonexistent_id}',
        data=data,
    )

    # assert
    assert response.status_code == 404
