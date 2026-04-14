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
from src.processes.messages import template as messages
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.services.templates.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_create_fieldset__unauthenticated__unauthorized(api_client):

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
    data = {
        'name': 'New Fieldset',
        'order': 1,
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 401


def test_create_fieldset__expired_sub__permission_denied(api_client):

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
    api_client.token_authenticate(user=user)
    data = {
        'name': 'New Fieldset',
        'order': 1,
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_create_fieldset__billing_plan__permission_denied(api_client):

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
    api_client.token_authenticate(user=user)
    data = {
        'name': 'New Fieldset',
        'order': 1,
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041


def test_create_fieldset__users_overlimit__permission_denied(api_client):

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
    api_client.token_authenticate(user=user)
    data = {
        'name': 'New Fieldset',
        'order': 1,
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037


def test_create_fieldset__non_admin__permission_denied(api_client):

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
    user = create_test_not_admin(account=account)
    api_client.token_authenticate(user=user)
    data = {
        'name': 'New Fieldset',
        'order': 1,
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 403


def test_create_fieldset__not_tpl_owner__permission_denied(api_client):

    """

    Template admin owner permission denied returns 403

    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=1,
    )
    user = create_test_admin(account=account)
    api_client.token_authenticate(user=user)
    data = {
        'name': 'New Fieldset',
        'order': 1,
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == messages.MSG_PT_0023


def test_create_fieldset__min_data__ok(api_client, mocker):

    """

    Create fieldset with minimal request data

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Minimal Fieldset',
        'order': 1,
    }

    # mock FieldSetTemplateService
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Minimal Fieldset',
        order=1,
    )
    field_set_template_service_create_mock = mocker.patch(
        'src.processes.views.template.FieldSetTemplateService.create',
        return_value=fieldset,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'Minimal Fieldset'
    assert response.data['order'] == 1
    assert response.data['layout'] == FieldSetLayout.VERTICAL
    assert response.data['label_position'] == LabelPosition.TOP
    assert response.data['description'] == ''
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=mocker.ANY,
    )
    field_set_template_service_create_mock.assert_called_once_with(
        template_id=template.id,
        name='Minimal Fieldset',
        order=1,
        rules=[],
        fields=[],
    )


def test_create_fieldset__full_data__ok(api_client, mocker):

    """

    Create fieldset with full request data

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Full Fieldset',
        'description': 'A detailed description',
        'order': 5,
        'layout': FieldSetLayout.HORIZONTAL,
        'label_position': LabelPosition.LEFT,
    }

    # mock FieldSetTemplateService
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Full Fieldset',
        description='A detailed description',
        order=5,
        layout=FieldSetLayout.HORIZONTAL,
        label_position=LabelPosition.LEFT,
    )
    field_set_template_service_create_mock = mocker.patch(
        'src.processes.views.template.FieldSetTemplateService.create',
        return_value=fieldset,
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'Full Fieldset'
    assert response.data['description'] == 'A detailed description'
    assert response.data['order'] == 5
    assert response.data['layout'] == FieldSetLayout.HORIZONTAL
    assert response.data['label_position'] == LabelPosition.LEFT
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=mocker.ANY,
    )
    field_set_template_service_create_mock.assert_called_once_with(
        template_id=template.id,
        name='Full Fieldset',
        description='A detailed description',
        order=5,
        layout=FieldSetLayout.HORIZONTAL,
        label_position=LabelPosition.LEFT,
        rules=[],
        fields=[],
    )


def test_create_fieldset__invalid_name__validation_error(api_client):

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
    api_client.token_authenticate(user=user)
    data = {
        'order': 1,
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['details']['name'] == 'name'


def test_create_fieldset__invalid_layout__validation_error(api_client):

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
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Test Fieldset',
        'order': 1,
        'layout': 'invalid_layout',
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['details']['name'] == 'layout'


def test_create_fieldset__invalid_label_pos__validation_error(api_client):

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
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Test Fieldset',
        'order': 1,
        'label_position': 'invalid_position',
    }

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['details']['name'] == 'label_position'


def test_create_fieldset__service_exception__validation_error(
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
    api_client.token_authenticate(user=user)
    data = {
        'name': 'Test Fieldset',
        'order': 1,
    }
    error_message = 'Service error occurred'

    # mock FieldSetTemplateService
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_create_mock = mocker.patch(
        'src.processes.views.template.FieldSetTemplateService.create',
        side_effect=BaseServiceException(message=error_message),
    )

    # act
    response = api_client.post(
        f'/templates/{template.id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=mocker.ANY,
    )
    field_set_template_service_create_mock.assert_called_once_with(
        template_id=template.id,
        name='Test Fieldset',
        order=1,
        rules=[],
        fields=[],
    )


def test_create_fieldset__not_existing_tpl__not_found(api_client):

    """

    Non-existent template returns 404

    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user=user)
    nonexistent_id = 999999
    data = {
        'name': 'New Fieldset',
        'order': 1,
    }

    # act
    response = api_client.post(
        f'/templates/{nonexistent_id}/fieldsets',
        data=data,
    )

    # assert
    assert response.status_code == 404
