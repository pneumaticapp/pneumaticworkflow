import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.authentication.enums import AuthTokenType
from src.generics.exceptions import BaseServiceException
from src.processes.enums import (
    FieldSetLayout,
    LabelPosition,
    FieldType,
    FieldRuleType,
    FieldRuleOperator,
    FieldSetRuleOperator,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.services.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_not_admin,
    create_test_owner,
    create_test_shared_fieldset, create_test_template,
    create_test_fieldset_template,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_partial_update__fieldset_data__ok(api_client, mocker):

    """
    Partial update with all top-level fieldset fields returns 200
    and correct response data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    field_api_name = 'f1'
    fieldset_api_name = 'fs1'
    rule_api_name = 'r1'
    data = {
        'name': 'Full Updated Fieldset',
        'description': 'Updated description',
        'api_name': fieldset_api_name,
        'layout': FieldSetLayout.HORIZONTAL,
        'label_position': LabelPosition.LEFT,
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.NUMBER,
                'order': 1,
                'api_name': field_api_name,
            },
        ],
        'rulesets': [
            {
                'api_name': rule_api_name,
                'fields': [field_api_name],
                'groups_or': [
                    {
                        'groups_and': [
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
        description=data['description'],
        label_position=data['label_position'],
        layout=data['layout'],
        api_name=data['api_name'],
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='10',
    )
    field = fieldset.fields.first()
    rule = fieldset.rulesets.first()
    rule.fields.add(field)
    group_and = rule.groups_or.first().groups_and.first()
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id
    assert response.data['name'] == fieldset.name
    assert response.data['title'] == fieldset.title
    assert response.data['order'] == fieldset.order
    assert response.data['description'] == fieldset.description
    assert response.data['label_position'] == fieldset.label_position
    assert response.data['layout'] == fieldset.layout
    assert response.data['api_name'] == fieldset.api_name
    assert response.data['usage'] == []

    assert len(response.data['fields']) == 1
    assert response.data['fields'][0]['name'] == field.name
    assert response.data['fields'][0]['api_name'] == field.api_name

    assert len(response.data['rulesets']) == 1
    assert response.data['rulesets'][0]['api_name'] == rule.api_name
    assert response.data['rulesets'][0]['fields'] == [field.api_name]
    assert (
        response.data['rulesets'][0]['groups_or'][0]['groups_and'][0]['value']
        == group_and.value
    )
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        name='Full Updated Fieldset',
        api_name=fieldset.api_name,
        description='Updated description',
        layout=FieldSetLayout.HORIZONTAL,
        label_position=LabelPosition.LEFT,
        rulesets=mocker.ANY,
        fields=mocker.ANY,
    )


@pytest.mark.parametrize(
    'operator',
    (
        FieldSetRuleOperator.SUM_EQUAL,
        FieldSetRuleOperator.SUM_LESS_THAN,
        FieldSetRuleOperator.SUM_GREATER_THAN,
    ),
)
def test_partial_update__rules_operator__ok(
    api_client,
    operator,
    mocker,
):

    """ Valid fieldset rules operator is accepted and passed to service """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    data = {
        'rulesets': [
            {
                'api_name': 'r-1',
                'order': 1,
                'fields': ['field-1', 'field-2'],
                'groups_or': [
                    {
                        'api_name': 'g-or-1',
                        'groups_and': [
                            {
                                'api_name': 'g-and-1',
                                'operator': operator,
                                'value': '100',
                            },
                        ],
                    },
                ],
            },
        ],
    }
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
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
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        rulesets=mocker.ANY,
    )


def test_partial_update_fieldset_is_used__return_usage(api_client, mocker):

    """ Partial update with minimal request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    shared_fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'name': 'Updated Name',
    }
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    task = template.tasks.get(number=1)
    create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
        shared_fieldset=shared_fieldset,
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=shared_fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{shared_fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == shared_fieldset.id
    assert len(response.data['usage']) == 1
    assert response.data['usage'][0]['id'] == template.id
    assert response.data['usage'][0]['name'] == template.name
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=shared_fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        name=data['name'],
    )


@pytest.mark.parametrize(
    'operator',
    (
        FieldRuleOperator.EQUAL,
        FieldRuleOperator.GREATER_THAN,
        FieldRuleOperator.LESS_THAN,
    ),
)
def test_partial_update__fields_operator__ok(
    api_client,
    operator,
    mocker,
):

    """ Valid field rules operator is accepted and passed to service """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    field = fieldset.fields.first()
    data = {
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.NUMBER,
                'order': 2,
                'api_name': 'field-1',
                'is_hidden': True,
                'rulesets': [
                    {
                        'api_name': 'r-1',
                        'type': FieldRuleType.VALIDATOR,
                        'order': 1,
                        'groups_or': [
                            {
                                'api_name': 'g-or-1',
                                'groups_and': [
                                    {
                                        'api_name': 'g-and-1',
                                        'field': field.api_name,
                                        'operator': operator,
                                        'value': 'apple',
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
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
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once()


def test_partial_update__response_rules_data__ok(api_client, mocker):

    """ Verify full rules response: ruleset → group_or → group_and """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_value='100',
        rule_message='Error message',
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
    )
    field = fieldset.fields.first()
    ruleset = fieldset.rulesets.first()
    ruleset.fields.add(field)
    group_or = ruleset.groups_or.first()
    group_and = group_or.groups_and.first()
    data = {
        'name': fieldset.name,
    }
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['rulesets']) == 1

    rule_resp = response.data['rulesets'][0]
    assert rule_resp['api_name'] == ruleset.api_name
    assert rule_resp['message'] == ruleset.message
    assert rule_resp['order'] == ruleset.order
    assert rule_resp['fields'] == [field.api_name]

    assert len(rule_resp['groups_or']) == 1
    group_or_resp = rule_resp['groups_or'][0]
    assert group_or_resp['api_name'] == group_or.api_name

    assert len(group_or_resp['groups_and']) == 1
    group_and_resp = group_or_resp['groups_and'][0]
    assert group_and_resp['api_name'] == group_and.api_name
    assert group_and_resp['operator'] == group_and.operator
    assert group_and_resp['value'] == group_and.value
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        name=data['name'],
    )


def test_partial_update__response_fields_data__ok(api_client, mocker):

    """ Verify full fields response: field → rules → group_or → group_and """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        field_rule_type=FieldRuleType.SHOW,
        field_rule_operator=FieldRuleOperator.EQUAL,
        field_rule_value='apple',
        field_rule_message='Error message',
    )
    field = fieldset.fields.first()
    field_ruleset = field.rulesets.first()
    field_group_or = field_ruleset.groups_or.first()
    field_group_and = field_group_or.groups_and.first()
    data = {
        'name': fieldset.name,
    }
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['fields']) == 1

    field_resp = response.data['fields'][0]
    assert field_resp['api_name'] == field.api_name
    assert field_resp['name'] == field.name
    assert field_resp['type'] == field.type

    assert len(field_resp['rulesets']) == 1
    rule_resp = field_resp['rulesets'][0]
    assert rule_resp['api_name'] == field_ruleset.api_name
    assert rule_resp['message'] == field_ruleset.message
    assert rule_resp['order'] == field_ruleset.order

    assert len(rule_resp['groups_or']) == 1
    group_or_resp = rule_resp['groups_or'][0]
    assert group_or_resp['api_name'] == field_group_or.api_name

    assert len(group_or_resp['groups_and']) == 1
    group_and_resp = group_or_resp['groups_and'][0]
    assert group_and_resp['api_name'] == field_group_and.api_name
    assert group_and_resp['field'] == field.api_name
    assert group_and_resp['operator'] == field_group_and.operator
    assert group_and_resp['value'] == field_group_and.value
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once_with(
        name=data['name'],
    )


@pytest.mark.parametrize(
    'rule_type',
    (
        FieldRuleType.SHOW,
        FieldRuleType.VALIDATOR,
    ),
)
def test_partial_update__fields_rules_type__ok(
    api_client,
    rule_type,
    mocker,
):

    """ Valid fieldset fields->rules->type values are accepted """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    field = fieldset.fields.first()
    data = {
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.NUMBER,
                'order': 1,
                'api_name': 'field-1',
                'rulesets': [
                    {
                        'api_name': 'r-1',
                        'type': rule_type,
                        'order': 1,
                        'groups_or': [
                            {
                                'api_name': 'g-or-1',
                                'groups_and': [
                                    {
                                        'api_name': 'g-and-1',
                                        'field': field.api_name,
                                        'operator': FieldRuleOperator.EQUAL,
                                        'value': 'apple',
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }
    field_set_template_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    field_set_template_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    partial_update_mock.assert_called_once()


def test_partial_update__unauthenticated__unauthorized(api_client, mocker):

    """ Unauthenticated request returns 401 """

    # arrange
    account = create_test_account()
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 401
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__expired_sub__permission_denied(api_client, mocker):

    """ Expired subscription returns 403 """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__billing_plan__permission_denied(api_client, mocker):

    """ Billing plan permission denied returns 403 """

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__users_limit__permission_denied(api_client, mocker):

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
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__non_admin__permission_denied(api_client, mocker):

    """ Non-admin non-owner user returns 403 """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    user = create_test_not_admin(account=account)
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__invalid_name__validation_error(api_client, mocker):

    """ Invalid name field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'name': '',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == 'This field may not be blank.'
    assert response.data['details']['name'] == 'name'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__invalid_layout__validation_error(api_client, mocker):

    """ Invalid layout field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'layout': 'invalid_layout',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = '"invalid_layout" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'layout'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__invalid_label_position__validation_error(
    api_client,
    mocker,
):

    """ Invalid label_position field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'label_position': 'invalid_position',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = '"invalid_position" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'label_position'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__service_exception__validation_error(
    api_client,
    mocker,
):

    """
    Service raises BaseServiceException returns 400 validation error
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    error_message = 'Service error occurred'
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        side_effect=BaseServiceException(message=error_message),
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        name=data['name'],
    )


def test_partial_update__not_existing_fieldset__not_found(api_client, mocker):

    """ Non-existent fieldset returns 404 """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    nonexistent_id = 999999
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{nonexistent_id}',
        data=data,
    )

    # assert
    assert response.status_code == 404
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__not_shared__not_found(api_client, mocker):

    """ Partial update with minimal request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
    )
    fieldset.is_shared = False
    fieldset.save()
    data = {
        'name': 'Updated Name',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 404
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__invalid_rules_operator__validation_error(
    api_client,
    mocker,
):

    """ Invalid operator in fieldset rules->group_or->group_and returns 400 """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    data = {
        'rulesets': [
            {
                'api_name': 'r-1',
                'order': 1,
                'fields': [],
                'groups_or': [
                    {
                        'api_name': 'g-or-1',
                        'groups_and': [
                            {
                                'api_name': 'g-and-1',
                                'operator': 'invalid_operator',
                                'value': '100',
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
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = 'Operator: "invalid_operator" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == 'g-and-1'
    assert response.data['details']['reason'] == message
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__invalid_fields_rules_operator__validation_error(
    api_client,
    mocker,
):

    """ Invalid operator in fields->rules->group_or->group_and returns 400 """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(account=account)
    field = fieldset.fields.first()
    data = {
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.NUMBER,
                'order': 1,
                'api_name': 'field-1',
                'rulesets': [
                    {
                        'api_name': 'r-1',
                        'type': FieldRuleType.SHOW,
                        'order': 1,
                        'groups_or': [
                            {
                                'api_name': 'g-or-1',
                                'groups_and': [
                                    {
                                        'api_name': 'g-and-1',
                                        'field': field.api_name,
                                        'operator': 'invalid_operator',
                                        'value': 'apple',
                                    },
                                ],
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
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = 'Operator: "invalid_operator" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == 'g-and-1'
    assert response.data['details']['reason'] == message
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__two_rules_same_type__ok(api_client, mocker):

    """
    Partial update with two rules of the same operator:
    one existing (with api_name) and one new (without api_name).
    Both rules reference the same fields.
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    fieldset = create_test_shared_fieldset(
        account=account,
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
    )
    field_1 = fieldset.fields.first()
    field_2 = FieldTemplate.objects.create(
        account=account,
        name='Field 2',
        type=FieldType.NUMBER,
        api_name='f2',
        fieldset=fieldset,
    )
    existing_ruleset = fieldset.rulesets.first()
    existing_ruleset.fields.add(field_1)
    existing_ruleset.fields.add(field_2)

    data = {
        'rulesets': [
            {
                'api_name': existing_ruleset.api_name,
                'fields': [field_1.api_name, field_2.api_name],
                'groups_or': [
                    {
                        'groups_and': [
                            {
                                'operator': FieldSetRuleOperator.SUM_EQUAL,
                                'value': '1',
                            },
                        ],
                    },
                ],
            },
            {
                'fields': [field_1.api_name, field_2.api_name],
                'groups_or': [
                    {
                        'groups_and': [
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

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        rulesets=mocker.ANY,
    )
