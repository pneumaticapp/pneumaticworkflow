import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.authentication.enums import AuthTokenType
from src.generics.exceptions import BaseServiceException
from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleType,
    LabelPosition,
)
from src.processes.services.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
    create_test_shared_fieldset,
)

pytestmark = pytest.mark.django_db


def test_clone__ok(api_client, mocker):
    """Clone existing shared fieldset"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Original Fieldset',
        title='Original Title',
        description='Original description',
        label_position=LabelPosition.LEFT,
        layout=FieldSetLayout.HORIZONTAL,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='10',
    )
    field = fieldset.fields.get()
    rule = fieldset.rules.get()
    rule.fields.add(field)
    clone = create_test_shared_fieldset(
        account=account,
        name=fieldset.name,
        title=fieldset.title,
        description=fieldset.description,
        label_position=fieldset.label_position,
        layout=fieldset.layout,
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='10',
        api_name='cloned-fs',
    )
    clone_field = clone.fields.get()
    clone_rule = clone.rules.get()
    clone_rule.fields.add(clone_field)

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
        return_value=clone,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 201
    assert response.data['id'] == clone.id
    assert response.data['name'] == clone.name
    assert response.data['title'] == clone.title
    assert response.data['description'] == clone.description
    assert response.data['label_position'] == clone.label_position
    assert response.data['layout'] == clone.layout
    assert response.data['api_name'] == clone.api_name

    assert len(response.data['fields']) == 1
    assert response.data['fields'][0]['name'] == clone_field.name
    assert response.data['fields'][0]['api_name'] == clone_field.api_name

    assert len(response.data['rules']) == 1
    assert response.data['rules'][0]['type'] == clone_rule.type
    assert response.data['rules'][0]['api_name'] == clone_rule.api_name

    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    field_set_template_service_get_clone_mock.assert_called_once_with()


def test_clone__unauthenticated__unauthorized(api_client, mocker):
    """Unauthenticated request returns 401"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
    )

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 401
    field_set_template_service_init_mock.assert_not_called()
    field_set_template_service_get_clone_mock.assert_not_called()


def test_clone__expired_subscription__permission_denied(api_client, mocker):
    """Expired subscription returns 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035
    field_set_template_service_init_mock.assert_not_called()
    field_set_template_service_get_clone_mock.assert_not_called()


def test_clone__billing_plan__permission_denied(api_client, mocker):
    """Billing plan permission denied returns 403"""

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041
    field_set_template_service_init_mock.assert_not_called()
    field_set_template_service_get_clone_mock.assert_not_called()


def test_clone__users_overlimit__permission_denied(api_client, mocker):
    """Users overlimited returns 403"""

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
    fieldset = create_test_shared_fieldset(account=account)

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037
    field_set_template_service_init_mock.assert_not_called()
    field_set_template_service_get_clone_mock.assert_not_called()


def test_clone__non_admin__permission_denied(api_client, mocker):
    """Non-admin non-owner user returns 403"""

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    user = create_test_not_admin(account=account)

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 403
    field_set_template_service_init_mock.assert_not_called()
    field_set_template_service_get_clone_mock.assert_not_called()


def test_clone__service_exception__validation_error(api_client, mocker):
    """Service raises BaseServiceException returns validation error"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    error_message = 'Service error occurred'

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
        side_effect=BaseServiceException(message=error_message),
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    field_set_template_service_get_clone_mock.assert_called_once_with()


def test_clone__not_existing__not_found(api_client, mocker):
    """Non-existent fieldset returns 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    nonexistent_id = 999999

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(f'/fieldsets/{nonexistent_id}/clone')

    # assert
    assert response.status_code == 404
    field_set_template_service_init_mock.assert_not_called()
    field_set_template_service_get_clone_mock.assert_not_called()


def test_clone__not_shared__not_found(api_client, mocker):
    """Non-shared fieldset returns 404"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    fieldset.is_shared = False
    fieldset.save()

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 404
    field_set_template_service_init_mock.assert_not_called()
    field_set_template_service_get_clone_mock.assert_not_called()


def test_clone__another_account__not_found(api_client, mocker):
    """Fieldset from another account returns 404"""

    # arrange
    account_1 = create_test_account(name='Account 1')
    account_2 = create_test_account(name='Account 2')
    user_1 = create_test_owner(account=account_1)
    fieldset = create_test_shared_fieldset(account=account_2)

    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    field_set_template_service_get_clone_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.get_clone',
    )

    api_client.token_authenticate(user=user_1)

    # act
    response = api_client.post(f'/fieldsets/{fieldset.id}/clone')

    # assert
    assert response.status_code == 404
    field_set_template_service_init_mock.assert_not_called()
    field_set_template_service_get_clone_mock.assert_not_called()
