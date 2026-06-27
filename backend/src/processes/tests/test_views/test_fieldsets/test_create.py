import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.authentication.enums import AuthTokenType
from src.generics.exceptions import BaseServiceException
from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldSetLayout,
    FieldSetRuleOperator,
    FieldSetRuleType,
    FieldType,
    LabelPosition,
)

from src.processes.models.templates.fieldset import (
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleGroupAnd,
    FieldSetTemplateRuleSet,
)
from src.processes.models.templates.fields import FieldTemplate

from src.processes.services.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_shared_fieldset,
)

pytestmark = pytest.mark.django_db


def test_create__all_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)

    data = {
        'name': 'All Fields Fieldset',
        'title': 'All Fields Title',
        'description': 'Description',
        'label_position': LabelPosition.LEFT,
        'layout': FieldSetLayout.HORIZONTAL,
        'api_name': 'fieldset_api_name',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f1',
            },
        ],
        'rules': [
            {
                'api_name': 'r1',
                'type': FieldSetRuleType.VALIDATOR,
                'order': 1,
                'fields': [],
                'group_or': [
                    {
                        'api_name': 'g-or-1',
                        'group_and': [
                            {
                                'api_name': 'g-and-1',
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '10',
                            },
                        ],
                    },
                ],
            },
        ],
    }

    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        title=data['title'],
        description=data['description'],
        label_position=data['label_position'],
        layout=data['layout'],
        api_name=data['api_name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='10',
    )
    field = fieldset.fields.first()
    ruleset = fieldset.rulesets.first()
    group_or = ruleset.groups_or.first()
    group_and = group_or.groups_and.first()

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['id'] == fieldset.id
    assert response.data['name'] == data['name']
    assert response.data['title'] == data['title']
    assert response.data['description'] == data['description']
    assert response.data['label_position'] == data['label_position']
    assert response.data['layout'] == data['layout']
    assert response.data['api_name'] == data['api_name']

    assert len(response.data['fields']) == 1
    assert response.data['fields'][0]['name'] == field.name
    assert response.data['fields'][0]['api_name'] == field.api_name

    assert len(response.data['rules']) == 1
    rule_resp = response.data['rules'][0]
    assert rule_resp['type'] == FieldSetRuleType.VALIDATOR
    assert rule_resp['api_name'] == ruleset.api_name
    assert len(rule_resp['group_or']) == 1
    assert rule_resp['group_or'][0]['api_name'] == group_or.api_name
    assert len(rule_resp['group_or'][0]['group_and']) == 1
    group_and_resp = rule_resp['group_or'][0]['group_and'][0]
    assert group_and_resp['api_name'] == group_and.api_name
    assert group_and_resp['operator'] == FieldSetRuleOperator.SUM_EQUAL
    assert group_and_resp['value'] == '10'

    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        title=data['title'],
        description=data['description'],
        layout=data['layout'],
        label_position=data['label_position'],
        api_name=data['api_name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__min_data__ok(api_client, mocker):

    """ Create fieldset with minimal request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Minimal Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Minimal Fieldset',
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name='Minimal Fieldset',
        rulesets=[],
        fields=[],
    )


def test_create__set_api_name__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Minimal Fieldset',
        'api_name': 'fs1',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset = create_test_shared_fieldset(
        account=account,
        name='Minimal Fieldset',
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['title'] == ''
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        api_name=data['api_name'],
        rulesets=[],
        fields=[],
    )


def test_create__rule_with_one_field__ok(api_client, mocker):

    """
    Create fieldset with fields in rule request and check fields in response
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    field_api_name = 'f1'
    data = {
        'name': 'All Fields Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.STRING,
                'order': 2,
                'api_name': field_api_name,
            },
            {
                'name': 'Field 2',
                'type': FieldType.URL,
                'order': 1,
                'api_name': 'f2',
            },
        ],
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': [field_api_name],
                'order': 1,
                'group_or': [
                    {
                        'api_name': 'g-or-1',
                        'group_and': [
                            {
                                'api_name': 'g-and-1',
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '10',
                            },
                        ],
                    },
                ],
            },
        ],
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
    )
    ruleset = fieldset.rulesets.first()
    field = fieldset.fields.first()
    ruleset.fields.add(field)

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201

    assert len(response.data['rules']) == 1
    assert response.data['rules'][0]['fields'] == [field.api_name]

    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__rule_with_two_fields__ok(api_client, mocker):

    """
    Create fieldset with fields in rule request and check fields in response
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    field_1_api_name = 'f1'
    field_2_api_name = 'f2'
    data = {
        'name': 'All Fields Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.STRING,
                'order': 2,
                'api_name': field_1_api_name,
            },
            {
                'name': 'Field 2',
                'type': FieldType.URL,
                'order': 1,
                'api_name': field_2_api_name,
            },
        ],
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': [field_2_api_name, field_1_api_name],
                'order': 1,
                'group_or': [
                    {
                        'api_name': 'g-or-1',
                        'group_and': [
                            {
                                'api_name': 'g-and-1',
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '10',
                            },
                        ],
                    },
                ],
            },
        ],
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
    )
    ruleset = fieldset.rulesets.first()
    field_1 = fieldset.fields.first()
    field_2 = FieldTemplate.objects.create(
        account=account,
        api_name=field_2_api_name,
        fieldset=fieldset,
    )
    ruleset.fields.set([field_1, field_2])

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201

    assert len(response.data['rules']) == 1
    assert set(response.data['rules'][0]['fields']) == {
        field_1.api_name,
        field_2.api_name,
    }

    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__unauthenticated__unauthorized(api_client, mocker):

    """ Unauthenticated request returns 401 """

    # arrange
    data = {
        'name': 'New Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 401
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create__expired_sub__permission_denied(api_client, mocker):

    """ Expired subscription returns 403 """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    data = {
        'name': 'New Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create__billing_plan__permission_denied(api_client, mocker):

    """ Billing plan permission denied returns 403 """

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    data = {
        'name': 'New Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create__users_limit__permission_denied(api_client, mocker):

    """ Users overlimited returns 403 """

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
    data = {
        'name': 'New Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create__non_admin__permission_denied(api_client, mocker):

    """ Non-admin non-owner user returns 403 """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    data = {
        'name': 'New Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 403
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create__admin__ok(api_client, mocker):

    """ Admin (non-owner) user can create fieldset """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    data = {
        'name': 'New Fieldset',
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        rulesets=[],
        fields=[],
    )


def test_create__blank_name__validation_error(api_client, mocker):

    """ Invalid name field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create__invalid_layout__validation_error(api_client, mocker):

    """ Invalid layout field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Test Fieldset',
        'layout': 'invalid_layout',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = '"invalid_layout" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'layout'
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create__invalid_label_position__validation_error(
    api_client,
    mocker,
):

    """ Invalid label_position field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Test Fieldset',
        'label_position': 'invalid_position',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = '"invalid_position" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'label_position'
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create__service_exception__validation_error(
    api_client,
    mocker,
):
    """ Service raises BaseServiceException returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Test Fieldset',
    }
    error_message = 'Service error occurred'

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        side_effect=BaseServiceException(message=error_message),
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name='Test Fieldset',
        rulesets=[],
        fields=[],
    )


def test_create__rule_multiple_group_or__ok(api_client, mocker):

    """
    Create fieldset with a ruleset containing multiple group_or entries
    (sum equals 100 OR 0) and check response structure.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    field_1_api_name = 'f1'
    field_2_api_name = 'f2'
    data = {
        'name': 'Multi GroupOr Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.NUMBER,
                'order': 1,
                'api_name': field_1_api_name,
            },
            {
                'name': 'Field 2',
                'type': FieldType.NUMBER,
                'order': 2,
                'api_name': field_2_api_name,
            },
        ],
        'rules': [
            {
                'api_name': 'r1',
                'type': FieldSetRuleType.VALIDATOR,
                'order': 1,
                'fields': [field_1_api_name, field_2_api_name],
                'group_or': [
                    {
                        'api_name': 'g-or-1',
                        'group_and': [
                            {
                                'api_name': 'g-and-1',
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                    {
                        'api_name': 'g-or-2',
                        'group_and': [
                            {
                                'api_name': 'g-and-2',
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '0',
                            },
                        ],
                    },
                ],
            },
        ],
    }

    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    ruleset = fieldset.rulesets.first()
    field_1 = fieldset.fields.first()
    field_2 = FieldTemplate.objects.create(
        account=account,
        api_name=field_2_api_name,
        fieldset=fieldset,
    )
    ruleset.fields.set([field_1, field_2])
    group_or_1 = ruleset.groups_or.first()
    group_or_2 = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        api_name='g-or-2',
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or_2,
        account=account,
        api_name='g-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='0',
    )

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201

    assert len(response.data['rules']) == 1
    rule_resp = response.data['rules'][0]
    assert rule_resp['api_name'] == ruleset.api_name
    assert rule_resp['type'] == FieldSetRuleType.VALIDATOR
    assert len(rule_resp['group_or']) == 2

    group_or_1_resp = rule_resp['group_or'][0]
    group_or_2_resp = rule_resp['group_or'][1]
    assert group_or_1_resp['api_name'] == group_or_1.api_name
    assert group_or_1_resp['group_and'][0]['value'] == '100'
    assert (
        group_or_1_resp['group_and'][0]['operator']
        == FieldSetRuleOperator.SUM_EQUAL
    )
    assert group_or_2_resp['api_name'] == 'g-or-2'
    assert group_or_2_resp['group_and'][0]['value'] == '0'
    assert (
        group_or_2_resp['group_and'][0]['operator']
        == FieldSetRuleOperator.SUM_EQUAL
    )
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_with_message__ok(api_client, mocker):

    """
    Create fieldset with a ruleset containing a custom error message
    and verify message is returned in the response.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    field_api_name = 'f1'
    custom_message = 'Sum must equal 100'
    data = {
        'name': 'Message Rule Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.NUMBER,
                'order': 1,
                'api_name': field_api_name,
            },
        ],
        'rules': [
            {
                'api_name': 'r1',
                'type': FieldSetRuleType.VALIDATOR,
                'message': custom_message,
                'order': 1,
                'fields': [field_api_name],
                'group_or': [
                    {
                        'api_name': 'g-or-1',
                        'group_and': [
                            {
                                'api_name': 'g-and-1',
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }

    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
        rule_message=custom_message,
    )
    ruleset = fieldset.rulesets.first()
    field = fieldset.fields.first()
    ruleset.fields.add(field)

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201

    assert len(response.data['rules']) == 1
    rule_resp = response.data['rules'][0]
    assert rule_resp['api_name'] == ruleset.api_name
    assert rule_resp['type'] == FieldSetRuleType.VALIDATOR
    assert rule_resp['message'] == custom_message
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_type_sum_equal__ok(api_client, mocker):

    """
    Create fieldset with rule type SUM_EQUAL and verify the response
    contains the correct type value.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Sum Equal Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.SUM_EQUAL,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    ruleset = fieldset.rulesets.first()
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert len(response.data['rules']) == 1
    assert response.data['rules'][0]['type'] == FieldSetRuleType.SUM_EQUAL
    assert response.data['rules'][0]['api_name'] == ruleset.api_name
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_missing_type__validation_error(api_client, mocker):

    """
    Create fieldset with a rule that is missing the required 'type' field
    and verify the request is rejected with a 400 status code.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Missing Type Fieldset',
        'rules': [
            {
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__rule_invalid_type__validation_error(api_client, mocker):

    """
    Create fieldset with an unrecognised rule type value and verify
    the request is rejected with a 400 status code.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Invalid Type Fieldset',
        'rules': [
            {
                'type': 'unknown_type',
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = '"unknown_type" is not a valid choice.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__rule_operator_sum_more_than__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Sum More Than Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': (
                                    FieldSetRuleOperator.SUM_GREATER_THAN
                                ),
                                'value': '0',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='0',
    )
    ruleset = fieldset.rulesets.first()
    group_or = ruleset.groups_or.first()
    group_and = group_or.groups_and.first()
    group_and.operator = FieldSetRuleOperator.SUM_GREATER_THAN
    group_and.save()
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    group_and_resp = response.data['rules'][0]['group_or'][0]['group_and'][0]
    assert group_and_resp['operator'] == FieldSetRuleOperator.SUM_GREATER_THAN
    assert group_and_resp['value'] == '0'
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_operator_sum_less_than__ok(api_client, mocker):

    """
    Create fieldset with a group_and using SUM_LESS_THAN operator and verify
    the response returns the correct operator value.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Sum Less Than Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_LESS_THAN,
                                'value': '1000',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='1000',
    )
    ruleset = fieldset.rulesets.first()
    group_or = ruleset.groups_or.first()
    group_and = group_or.groups_and.first()
    group_and.operator = FieldSetRuleOperator.SUM_LESS_THAN
    group_and.save()
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    group_and_resp = response.data['rules'][0]['group_or'][0]['group_and'][0]
    assert group_and_resp['operator'] == FieldSetRuleOperator.SUM_LESS_THAN
    assert group_and_resp['value'] == '1000'
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_invalid_operator__validation_error(api_client, mocker):

    """
    Create fieldset with operator 'equal' (FieldRuleOperator) which is
    not valid for FieldSetRuleOperator and verify 400 is returned.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Invalid Operator Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': 'equal',
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = '"equal" is not a valid choice.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__rule_group_and_null_value__ok(api_client, mocker):

    """
    Create fieldset with a group_and where value is null (None) and verify
    the response returns null for value field.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Null Value Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': None,
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value=None,
    )
    ruleset = fieldset.rulesets.first()
    group_or = ruleset.groups_or.first()
    group_and = group_or.groups_and.first()
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    group_and_resp = response.data['rules'][0]['group_or'][0]['group_and'][0]
    assert group_and_resp['value'] is None
    assert group_and_resp['api_name'] == group_and.api_name
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_missing_operator__validation_error(api_client, mocker):

    """
    Create fieldset with a group_and that is missing the required 'operator'
    field and verify the request is rejected with a 400 status code.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Missing Operator Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__rule_multiple_group_and__ok(api_client, mocker):

    """
    Create fieldset with a single group_or containing two group_and entries
    (SUM_GREATER_THAN 0 AND SUM_LESS_THAN 100) and verify both are returned
    in the response.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Multiple GroupAnd Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': (
                                    FieldSetRuleOperator.SUM_GREATER_THAN
                                ),
                                'value': '0',
                            },
                            {
                                'operator': FieldSetRuleOperator.SUM_LESS_THAN,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='0',
    )
    ruleset = fieldset.rulesets.first()
    group_or = ruleset.groups_or.first()
    group_and_1 = group_or.groups_and.first()
    group_and_1.operator = FieldSetRuleOperator.SUM_GREATER_THAN
    group_and_1.save()
    FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        api_name=f'{fieldset.api_name}-group-and-2',
        operator=FieldSetRuleOperator.SUM_LESS_THAN,
        value='100',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    group_or_resp = response.data['rules'][0]['group_or'][0]
    assert len(group_or_resp['group_and']) == 2
    assert (
        group_or_resp['group_and'][0]['operator']
        == FieldSetRuleOperator.SUM_GREATER_THAN
    )
    assert group_or_resp['group_and'][0]['value'] == '0'
    assert (
        group_or_resp['group_and'][1]['operator']
        == FieldSetRuleOperator.SUM_LESS_THAN
    )
    assert group_or_resp['group_and'][1]['value'] == '100'
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_missing_group_or__validation_error(api_client, mocker):

    """
    Create fieldset with a rule that is missing the required 'group_or' field
    and verify the request is rejected with a 400 status code.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Missing GroupOr Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__rule_empty_group_or__ok(api_client, mocker):

    """
    Create fieldset with a rule where group_or is an empty list and verify
    the serializer accepts it (no min_length constraint) and returns 201.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Empty GroupOr Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['rules'] == []
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__rule_empty_group_and__ok(api_client, mocker):

    """
    Create fieldset with a group_or entry where group_and is an empty list
    and verify the serializer accepts it and returns 201.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Empty GroupAnd Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
    )
    ruleset = fieldset.rulesets.first()
    group_or = ruleset.groups_or.first()
    group_or.groups_and.all().delete()
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert len(response.data['rules'][0]['group_or']) == 1
    assert response.data['rules'][0]['group_or'][0]['group_and'] == []
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__multiple_rulesets__ok(api_client, mocker):

    """
    Create fieldset whose mock return value contains two RuleSet objects
    and verify the response contains both rules.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Two Rulesets Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '10',
                            },
                        ],
                    },
                ],
            },
            {
                'type': FieldSetRuleType.SUM_EQUAL,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '20',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='10',
    )
    ruleset_2 = FieldSetTemplateRuleSet.objects.create(
        account=account,
        fieldset=fieldset,
        api_name=f'{fieldset.api_name}-ruleset-2',
        type=FieldSetRuleType.SUM_EQUAL,
        order=1,
    )
    group_or_2 = FieldSetTemplateRuleGroupOr.objects.create(
        account=account,
        fieldset_rule=ruleset_2,
        api_name=f'{fieldset.api_name}-group-or-2',
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        account=account,
        group_or=group_or_2,
        api_name=f'{fieldset.api_name}-group-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='20',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert len(response.data['rules']) == 2
    assert response.data['rules'][0]['type'] == FieldSetRuleType.VALIDATOR
    assert response.data['rules'][1]['type'] == FieldSetRuleType.SUM_EQUAL
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_order_preserved__ok(api_client, mocker):

    """
    Create fieldset with two rulesets with explicit order values and verify
    the response returns them in ascending order (order ASC).
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Order Preserved Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'order': 2,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '5',
                            },
                        ],
                    },
                ],
            },
            {
                'type': FieldSetRuleType.SUM_EQUAL,
                'order': 1,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '10',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='10',
    )
    ruleset_1 = fieldset.rulesets.first()
    ruleset_1.order = 1
    ruleset_1.save()
    ruleset_2 = FieldSetTemplateRuleSet.objects.create(
        account=account,
        fieldset=fieldset,
        api_name=f'{fieldset.api_name}-ruleset-2',
        type=FieldSetRuleType.VALIDATOR,
        order=2,
    )
    group_or_2 = FieldSetTemplateRuleGroupOr.objects.create(
        account=account,
        fieldset_rule=ruleset_2,
        api_name=f'{fieldset.api_name}-group-or-2',
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        account=account,
        group_or=group_or_2,
        api_name=f'{fieldset.api_name}-group-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='5',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert len(response.data['rules']) == 2
    assert response.data['rules'][0]['order'] == 1
    assert response.data['rules'][1]['order'] == 2
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_no_fields__ok(api_client, mocker):

    """
    Create fieldset with a rule that has an empty fields list and verify
    the response returns an empty list for rule fields.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'No Rule Fields Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': [],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['rules'][0]['fields'] == []
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_empty_message__ok(api_client, mocker):

    """
    Create fieldset with a rule where message is an empty string and verify
    the response returns the empty string for the message field.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Empty Message Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'message': '',
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
        rule_message='',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['rules'][0]['message'] == ''
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_null_message__ok(api_client, mocker):

    """
    Create fieldset with a rule where message is null and verify
    the response returns None for the message field.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Null Message Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'message': None,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['rules'][0]['message'] is None
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_without_api_name__ok(api_client, mocker):

    """
    Create fieldset with a rule that has no explicit api_name and verify
    the service is called (api_name generation is the service's
    responsibility).
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'No API Name Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__rule_explicit_api_name__ok(api_client, mocker):

    """
    Create fieldset with a rule that has an explicit api_name and verify
    the service receives the provided api_name in validated data.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    explicit_api_name = 'my-custom-rule-1'
    data = {
        'name': 'Explicit API Name Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'api_name': explicit_api_name,
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    ruleset = fieldset.rulesets.first()
    ruleset.api_name = explicit_api_name
    ruleset.save()
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['rules'][0]['api_name'] == explicit_api_name
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__rule_nonexistent_field_api_name__ok(api_client, mocker):

    """
    Create fieldset with rule.fields containing a non-existent
    api_name string.
    RelatedApiNameListField performs no DB lookup — the string is
    passed through to the service as-is, so the request returns 201.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Nonexistent Field Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': ['nonexistent-api-name'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__rule_fields_in_response__ok(api_client, mocker):

    """
    Create fieldset where one FieldTemplate is linked to the ruleset via M2M.
    Verify the response contains the field api_name in rules[0].fields.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Rule Fields Response Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': ['field-api-1'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    ruleset = fieldset.rulesets.first()
    field_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='field-api-1',
        name='Field 1',
        type=FieldType.TEXT,
    )
    ruleset.fields.add(field_1)
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert len(response.data['rules'][0]['fields']) == 1
    assert response.data['rules'][0]['fields'][0] == 'field-api-1'
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_fields_sent_to_service__ok(api_client, mocker):

    """
    Create fieldset with two field api_names in rule.fields and verify
    the service is called once (fields are passed as strings, not DB objects).
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Fields Sent To Service Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': ['field-api-1', 'field-api-2'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    ruleset = fieldset.rulesets.first()
    field_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='field-api-1',
        name='Field 1',
        type=FieldType.TEXT,
    )
    field_2 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='field-api-2',
        name='Field 2',
        type=FieldType.TEXT,
    )
    ruleset.fields.set([field_1, field_2])
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert len(response.data['rules'][0]['fields']) == 2
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__rule_field_in_multiple_rules__ok(api_client, mocker):

    """
    Create fieldset where the same FieldTemplate is linked to two different
    RuleSets and verify both rules return the field api_name in
    their fields list.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field In Multiple Rules Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': ['shared-field'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '10',
                            },
                        ],
                    },
                ],
            },
            {
                'type': FieldSetRuleType.SUM_EQUAL,
                'fields': ['shared-field'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '20',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='10',
    )
    ruleset_1 = fieldset.rulesets.first()
    ruleset_2 = FieldSetTemplateRuleSet.objects.create(
        account=account,
        fieldset=fieldset,
        api_name=f'{fieldset.api_name}-ruleset-2',
        type=FieldSetRuleType.SUM_EQUAL,
        order=1,
    )
    group_or_2 = FieldSetTemplateRuleGroupOr.objects.create(
        account=account,
        fieldset_rule=ruleset_2,
        api_name=f'{fieldset.api_name}-group-or-2',
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        account=account,
        group_or=group_or_2,
        api_name=f'{fieldset.api_name}-group-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='20',
    )
    shared_field = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='shared-field',
        name='Shared Field',
        type=FieldType.TEXT,
    )
    ruleset_1.fields.add(shared_field)
    ruleset_2.fields.add(shared_field)
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert len(response.data['rules']) == 2
    assert response.data['rules'][0]['fields'][0] == 'shared-field'
    assert response.data['rules'][1]['fields'][0] == 'shared-field'
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_all_fieldset_fields_in_rule__ok(api_client, mocker):

    """
    Create fieldset with three FieldTemplates all linked to a single RuleSet
    and verify all three api_names appear in the response rules[0].fields.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'All Fields In Rule Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': ['f-1', 'f-2', 'f-3'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    ruleset = fieldset.rulesets.first()
    field_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='f-1',
        name='Field 1',
        type=FieldType.TEXT,
    )
    field_2 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='f-2',
        name='Field 2',
        type=FieldType.TEXT,
    )
    field_3 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='f-3',
        name='Field 3',
        type=FieldType.TEXT,
    )
    ruleset.fields.set([field_1, field_2, field_3])
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    rule_fields = set(response.data['rules'][0]['fields'])
    assert rule_fields == {'f-1', 'f-2', 'f-3'}
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_fields_empty_list_in_response__ok(api_client, mocker):

    """
    Create fieldset where the ruleset has no linked fields (empty
    M2M) and verify
    the response returns an empty list for rules[0].fields.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Empty Fields In Response Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': [],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['rules'][0]['fields'] == []
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_fields_no_duplicates_in_response__ok(api_client, mocker):

    """
    Create fieldset with three distinct fields in the ruleset M2M and verify
    the response list contains no duplicate api_names.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'No Duplicates Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': ['fa-1', 'fa-2', 'fa-3'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    ruleset = fieldset.rulesets.first()
    field_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='fa-1',
        name='Field A1',
        type=FieldType.TEXT,
    )
    field_2 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='fa-2',
        name='Field A2',
        type=FieldType.TEXT,
    )
    field_3 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='fa-3',
        name='Field A3',
        type=FieldType.TEXT,
    )
    ruleset.fields.set([field_1, field_2, field_3])
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fields_in_response = response.data['rules'][0]['fields']
    assert len(fields_in_response) == len(set(fields_in_response))
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_field_not_in_another_rule__ok(api_client, mocker):

    """
    Create fieldset with two rulesets where each has a different field linked
    in M2M and verify the response shows no field crossing between rules.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Fields Not Shared Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': ['rule-field-1'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '10',
                            },
                        ],
                    },
                ],
            },
            {
                'type': FieldSetRuleType.SUM_EQUAL,
                'fields': ['rule-field-2'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '20',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='10',
    )
    ruleset_1 = fieldset.rulesets.first()
    ruleset_2 = FieldSetTemplateRuleSet.objects.create(
        account=account,
        fieldset=fieldset,
        api_name=f'{fieldset.api_name}-ruleset-2',
        type=FieldSetRuleType.SUM_EQUAL,
        order=1,
    )
    group_or_2 = FieldSetTemplateRuleGroupOr.objects.create(
        account=account,
        fieldset_rule=ruleset_2,
        api_name=f'{fieldset.api_name}-group-or-2',
    )
    FieldSetTemplateRuleGroupAnd.objects.create(
        account=account,
        group_or=group_or_2,
        api_name=f'{fieldset.api_name}-group-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='20',
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='rule-field-1',
        name='Rule Field 1',
        type=FieldType.TEXT,
    )
    field_2 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        api_name='rule-field-2',
        name='Rule Field 2',
        type=FieldType.TEXT,
    )
    ruleset_1.fields.add(field_1)
    ruleset_2.fields.add(field_2)
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert len(response.data['rules']) == 2
    assert response.data['rules'][0]['fields'] == ['rule-field-1']
    assert response.data['rules'][1]['fields'] == ['rule-field-2']
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once()


def test_create__rule_fields_passthrough_to_service__ok(api_client, mocker):

    """
    Create fieldset with one field api_name in rule.fields and verify
    the serializer passes it through to the service as a string without
    performing any DB lookup (RelatedApiNameListField is ListField[CharField]).
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Fields Passthrough Fieldset',
        'rules': [
            {
                'type': FieldSetRuleType.VALIDATOR,
                'fields': ['passthrough-field'],
                'group_or': [
                    {
                        'group_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
        rule_type=FieldSetRuleType.VALIDATOR,
        rule_value='100',
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__field_rule_type_show__ok(api_client, mocker):

    """
    Create fieldset with a field that has a rule of type SHOW and
    verify the service is called successfully (201).
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Show Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__field_rule_type_validator__ok(api_client, mocker):

    """
    Create fieldset with a field that has a rule of type VALIDATOR
    and verify the service is called successfully (201).
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Validator Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.VALIDATOR,
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__field_rule_missing_type__validation_error(api_client, mocker):

    """
    Create fieldset with a field rule that is missing the required 'type' field
    and verify the request is rejected with a 400 status code.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Missing Type Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'Type: this field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule_invalid_type__validation_error(api_client, mocker):

    """
    Create fieldset with a field rule using type 'sum_equal' which belongs to
    FieldSetRuleType (not FieldRuleType) and verify 400 is returned.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Invalid Type Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldSetRuleType.SUM_EQUAL,
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'Type: "sum_equal" is not a valid choice.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule_invalid_op__validation_error(api_client, mocker):

    """
    Create fieldset with a field rule using operator 'sum_equal' which
    belongs to FieldSetRuleOperator (not FieldRuleOperator) and verify
    400 is returned.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Invalid Operator Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                        'group_or': [
                            {
                                'group_and': [
                                    {
                                        'operator': (
                                            FieldSetRuleOperator.SUM_EQUAL
                                        ),
                                        'value': '10',
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'Field: this field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule_missing_op__validation_error(api_client, mocker):

    """
    Create fieldset with a field rule group_and that is missing the required
    'operator' field and verify the request is rejected with a 400 status code.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Missing Operator Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                        'group_or': [
                            {
                                'group_and': [
                                    {
                                        'value': 'yes',
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'Field: this field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule_grp_and_field_missing__err(api_client, mocker):

    """
    Create fieldset with a field rule group_and that is missing the
    required 'field' key and verify 400 is returned.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Missing Field Key Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                        'group_or': [
                            {
                                'group_and': [
                                    {
                                        'operator': FieldRuleOperator.EQUAL,
                                        'value': 'yes',
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'Field: this field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule_missing_grp_or__err(api_client, mocker):

    """
    Create fieldset with a field rule that is missing 'group_or'
    and verify the request is rejected with 400.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Missing GroupOr Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                    },
                ],
            },
        ],
    }
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'Group_or: this field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule_empty_group_or__ok(api_client, mocker):

    """
    Create fieldset with a field rule where group_or is an empty list
    and verify the serializer accepts it (no min_length constraint)
    and returns 201.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Empty GroupOr Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__field_rule_empty_group_and__ok(api_client, mocker):

    """
    Create fieldset with a field rule where group_and is an empty
    list and verify the serializer accepts it (no min_length
    constraint) and returns 201.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Empty GroupAnd Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                        'group_or': [
                            {
                                'group_and': [],
                            },
                        ],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__field_multiple_rules__ok(api_client, mocker):

    """
    Create fieldset with a field that has two rule entries and verify
    the service is called with both rulesets in the fields validated data.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Two Rules Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                        'group_or': [],
                    },
                    {
                        'type': FieldRuleType.VALIDATOR,
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__field_rule_null_message__ok(api_client, mocker):

    """
    Create fieldset with a field rule where message is null and verify
    the serializer accepts it and calls the service successfully.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Null Message Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.VALIDATOR,
                        'message': None,
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__field_rule_empty_message__ok(api_client, mocker):

    """
    Create fieldset with a field rule where message is an empty
    string and verify
    the serializer accepts it and calls the service successfully.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Empty Message Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.VALIDATOR,
                        'message': '',
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


def test_create__field_rule_explicit_api_name__ok(api_client, mocker):

    """
    Create fieldset with a field rule that has an explicit api_name and verify
    the serializer accepts it and calls the service successfully.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    explicit_api_name = 'my-field-rule-1'
    data = {
        'name': 'Field Rule Explicit API Name Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rules': [
                    {
                        'type': FieldRuleType.SHOW,
                        'api_name': explicit_api_name,
                        'group_or': [],
                    },
                ],
            },
        ],
    }
    fieldset = create_test_shared_fieldset(
        account=account,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    create_shared_fieldset_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    create_shared_fieldset_mock.assert_called_once_with(
        name=data['name'],
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )
