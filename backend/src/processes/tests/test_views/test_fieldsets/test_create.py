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
    FieldType,
    LabelPosition,
)

from src.processes.messages.template import MSG_PT_0079
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
                'rulesets': [],
            },
        ],
        'rulesets': [
            {
                'api_name': 'r1',
                'order': 1,
                'fields': [],
                'groups_or': [
                    {
                        'api_name': 'g-or-1',
                        'groups_and': [
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
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
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
    assert response.data['usage'] == []

    assert len(response.data['fields']) == 1
    assert response.data['fields'][0]['name'] == field.name
    assert response.data['fields'][0]['api_name'] == field.api_name

    assert len(response.data['rulesets']) == 1
    ruleset_data = response.data['rulesets'][0]
    assert ruleset_data['api_name'] == ruleset.api_name

    assert len(ruleset_data['groups_or']) == 1
    group_or_data = ruleset_data['groups_or'][0]
    assert group_or_data['api_name'] == group_or.api_name

    assert len(group_or_data['groups_and']) == 1
    group_and_data = group_or_data['groups_and'][0]
    assert group_and_data['api_name'] == group_and.api_name
    assert group_and_data['operator'] == FieldSetRuleOperator.SUM_EQUAL
    assert group_and_data['value'] == '10'

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
        order=0,
        rulesets=data['rulesets'],
        fields=data['fields'],
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
        order=0,
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
        order=0,
    )


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
        'rulesets': [
            {
                'groups_or': [
                    {
                        'groups_and': [
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
        'rulesets': [
            {
                'groups_or': [
                    {
                        'groups_and': [
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


def test_create__rule_missing_group_or__validation_error(api_client, mocker):

    """
    Create fieldset with a rule that is missing the required 'groups_or' field
    and verify the request is rejected with a 400 status code.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Missing GroupOr Fieldset',
        'rulesets': [
            {
                'api_name': 'ruleset-1',
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
    message = 'Groups_or: this field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


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
                'rulesets': [
                    {
                        'name': 'Ruleset',
                        'groups_or': [],
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
    Create fieldset with a field rule using type 'sum_equal'
    and verify 400 is returned.
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
                'rulesets': [
                    {
                        'name': 'Ruleset',
                        'type': 'sum_equal',
                        'groups_or': [],
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


def test_create__field_rule__field_missing__validation_error(
    api_client,
    mocker,
):

    """
    Create fieldset with a SHOW field rule group_and that is missing the
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
                'rulesets': [
                    {
                        'name': 'Ruleset',
                        'type': FieldRuleType.SHOW,
                        'groups_or': [
                            {
                                'groups_and': [
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
    assert response.data['message'] == MSG_PT_0079
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule__field_null__validation_error(
    api_client,
    mocker,
):

    """
    Create fieldset with a SHOW field rule group_and that is missing the
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
                'rulesets': [
                    {
                        'name': 'Ruleset',
                        'type': FieldRuleType.SHOW,
                        'groups_or': [
                            {
                                'groups_and': [
                                    {
                                        'field': None,
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
    assert response.data['message'] == MSG_PT_0079
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule_missing_groups_or__validation_error(
    api_client,
    mocker,
):

    """
    Create fieldset with a field rule that is missing 'groups_or'
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
                'rulesets': [
                    {
                        'name': 'Ruleset',
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
    message = 'Groups_or: this field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


def test_create__field_rule_missing_name__validation_error(api_client, mocker):

    """
    Create fieldset with a field rule that is missing the required 'name' field
    and verify the request is rejected with a 400 status code.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Field Rule Missing Name Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f-1',
                'rulesets': [
                    {
                        'type': FieldRuleType.SHOW,
                        'groups_or': [],
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
    message = 'Name: this field is required.'
    assert response.data['message'] == message
    create_shared_fieldset_mock.assert_not_called()


@pytest.mark.parametrize(
    ('field_type', 'operator', 'value'),
    (
        (FieldType.STRING, FieldRuleOperator.EQUAL, 'yes'),
        (FieldType.TEXT, FieldRuleOperator.CONTAIN, 'text'),
        (FieldType.URL, FieldRuleOperator.NOT_EQUAL, 'http://example.com'),
        (FieldType.DATE, FieldRuleOperator.GREATER_THAN, '1577836800'),
        (FieldType.NUMBER, FieldRuleOperator.LESS_THAN, '10'),
        (FieldType.FILE, FieldRuleOperator.EXIST, None),
    ),
)
def test_create__field_rule_validator_by_field_type__ok(
    api_client,
    mocker,
    field_type,
    operator,
    value,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Validator Fieldset',
        'fields': [
            {
                'name': 'Field',
                'type': field_type,
                'order': 1,
                'api_name': 'field-1',
                'rulesets': [
                    {
                        'name': 'Some name',
                        'type': FieldRuleType.VALIDATOR,
                        'message': 'Value is invalid',
                        'order': 1,
                        'groups_or': [
                            {
                                'groups_and': [
                                    {
                                        'operator': operator,
                                        'value': value,
                                        'field': None,
                                    },
                                ],
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
        field_rule_type=FieldRuleType.VALIDATOR,
        field_rule_operator=operator,
        field_rule_value=value,
        field_rule_message='Value is invalid',
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
    field_response = response.data['fields'][0]
    ruleset_data = field_response['rulesets'][0]
    assert ruleset_data['type'] == FieldRuleType.VALIDATOR
    fieldset_service_create_mock.assert_called_once()
    call_kwargs = fieldset_service_create_mock.call_args[1]
    field_payload = call_kwargs['fields'][0]
    ruleset_payload = field_payload['rulesets'][0]
    assert ruleset_payload['type'] == FieldRuleType.VALIDATOR
    group_and_payload = ruleset_payload['groups_or'][0]['groups_and'][0]
    assert group_and_payload['operator'] == operator
    assert group_and_payload['value'] == value


def test_create__field_rule_validator_user_field__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    operator = FieldRuleOperator.EQUAL
    value = '1'
    data = {
        'name': 'Validator User Fieldset',
        'fields': [
            {
                'name': 'Field',
                'type': FieldType.USER,
                'order': 1,
                'api_name': 'field-1',
                'is_required': True,
                'rulesets': [
                    {
                        'name': 'Some name',
                        'type': FieldRuleType.VALIDATOR,
                        'message': 'Value is invalid',
                        'order': 1,
                        'groups_or': [
                            {
                                'groups_and': [
                                    {
                                        'operator': operator,
                                        'value': value,
                                        'field': None,
                                    },
                                ],
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
        field_rule_type=FieldRuleType.VALIDATOR,
        field_rule_operator=operator,
        field_rule_value=value,
        field_rule_message='Value is invalid',
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
    field_response = response.data['fields'][0]
    ruleset_data = field_response['rulesets'][0]
    assert ruleset_data['type'] == FieldRuleType.VALIDATOR
    fieldset_service_create_mock.assert_called_once()
    call_kwargs = fieldset_service_create_mock.call_args[1]
    field_payload = call_kwargs['fields'][0]
    ruleset_payload = field_payload['rulesets'][0]
    assert ruleset_payload['type'] == FieldRuleType.VALIDATOR
    group_and_payload = ruleset_payload['groups_or'][0]['groups_and'][0]
    assert group_and_payload['operator'] == operator
    assert group_and_payload['value'] == value


@pytest.mark.parametrize(
    ('field_type', 'operator', 'value'),
    (
        (FieldType.CHECKBOX, FieldRuleOperator.CONTAIN, 'Second'),
        (FieldType.RADIO, FieldRuleOperator.EQUAL, 'Second'),
        (FieldType.DROPDOWN, FieldRuleOperator.NOT_EQUAL, 'Second'),
    ),
)
def test_create__field_rule_validator_types_with_selections__ok(
    api_client,
    mocker,
    field_type,
    operator,
    value,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Validator Selections Fieldset',
        'fields': [
            {
                'name': 'Field',
                'type': field_type,
                'order': 1,
                'api_name': 'field-1',
                'selections': [
                    {'value': 'First'},
                    {'value': 'Second'},
                ],
                'rulesets': [
                    {
                        'name': 'Some name',
                        'type': FieldRuleType.VALIDATOR,
                        'message': 'Value is invalid',
                        'order': 1,
                        'groups_or': [
                            {
                                'groups_and': [
                                    {
                                        'operator': operator,
                                        'value': value,
                                        'field': None,
                                    },
                                ],
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
        field_rule_type=FieldRuleType.VALIDATOR,
        field_rule_operator=operator,
        field_rule_value=value,
        field_rule_message='Value is invalid',
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
    field_response = response.data['fields'][0]
    ruleset_data = field_response['rulesets'][0]
    assert ruleset_data['type'] == FieldRuleType.VALIDATOR
    fieldset_service_create_mock.assert_called_once()
    call_kwargs = fieldset_service_create_mock.call_args[1]
    field_payload = call_kwargs['fields'][0]
    ruleset_payload = field_payload['rulesets'][0]
    assert ruleset_payload['type'] == FieldRuleType.VALIDATOR
    group_and_payload = ruleset_payload['groups_or'][0]['groups_and'][0]
    assert group_and_payload['operator'] == operator
    assert group_and_payload['value'] == value


def test_create__field_rule_show_file_field__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    source_api_name = 'src-1'
    data = {
        'name': 'Show File Fieldset',
        'fields': [
            {
                'name': 'Image original',
                'type': FieldType.FILE,
                'order': 1,
                'api_name': source_api_name,
            },
            {
                'name': 'Image resized',
                'type': FieldType.FILE,
                'order': 2,
                'api_name': 'file-1',
                'rulesets': [
                    {
                        'name': 'Some name',
                        'type': FieldRuleType.SHOW,
                        'order': 1,
                        'groups_or': [
                            {
                                'groups_and': [
                                    {
                                        'field': source_api_name,
                                        'operator': FieldRuleOperator.EXIST,
                                        'value': None,
                                    },
                                ],
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
        field_rule_type=FieldRuleType.SHOW,
        field_rule_operator=FieldRuleOperator.EXIST,
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
    field_with_ruleset = response.data['fields'][0]
    assert field_with_ruleset['rulesets'][0]['type'] == FieldRuleType.SHOW
    fieldset_service_create_mock.assert_called_once()
    call_kwargs = fieldset_service_create_mock.call_args[1]
    file_payload = call_kwargs['fields'][1]
    ruleset_payload = file_payload['rulesets'][0]
    assert ruleset_payload['type'] == FieldRuleType.SHOW
    group_and_payload = ruleset_payload['groups_or'][0]['groups_and'][0]
    assert group_and_payload['field'] == source_api_name
    assert group_and_payload['operator'] == FieldRuleOperator.EXIST
    assert group_and_payload['value'] is None
