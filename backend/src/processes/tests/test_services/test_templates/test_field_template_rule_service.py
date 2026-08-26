from types import SimpleNamespace

import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
)
from src.processes.messages import template as pt_messages
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)
from src.processes.services.exceptions import (
    FieldTemplateRuleSetServiceException,
)
from src.processes.services.templates.field_template_rule import (
    FieldTemplateRuleSetService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test__create_instance__default_params__ok():

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._create_instance(
        field_id=field.id,
        type=FieldRuleType.SHOW,
        name='Ruleset',
    )

    # assert
    assert result == service.instance
    assert result.field_id == field.id
    assert result.name == 'Ruleset'
    assert result.type == FieldRuleType.SHOW
    assert result.message is None
    assert result.order == 0
    assert result.template_id is None
    assert result.account_id == account.id
    assert result.api_name.startswith('field-ruleset')


def test__create_instance__all_params__ok():

    """
    All parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    name = 'Show when value is yes'
    api_name = 'ruleset-custom-1'
    message = 'Must be greater than 0'
    order = 3

    # act
    result = service._create_instance(
        field_id=field.id,
        type=FieldRuleType.VALIDATOR,
        name=name,
        api_name=api_name,
        message=message,
        order=order,
        template_id=template.id,
    )

    # assert
    assert result == service.instance
    assert result.field_id == field.id
    assert result.name == name
    assert result.type == FieldRuleType.VALIDATOR
    assert result.api_name == api_name
    assert result.message == message
    assert result.order == order
    assert result.template_id == template.id
    assert result.account_id == account.id


def test__create_instance__explicit_template_id__ok():

    """
    Explicit template_id
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._create_instance(
        field_id=field.id,
        type=FieldRuleType.VALIDATOR,
        template_id=template.id,
    )

    # assert
    assert result.template_id == template.id
    assert result.field_id == field.id
    assert result.type == FieldRuleType.VALIDATOR


def test__create_instance__api_name_provided__ok():

    """
    api_name provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    api_name = 'ruleset-custom-1'

    # act
    result = service._create_instance(
        field_id=field.id,
        type=FieldRuleType.SHOW,
        api_name=api_name,
    )

    # assert
    assert result.api_name == api_name


def test__create_instance__api_name_omitted__ok():

    """
    api_name omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._create_instance(
        field_id=field.id,
        type=FieldRuleType.SHOW,
        api_name='',
    )

    # assert
    assert result.api_name.startswith('field-ruleset')


def test__create_instance__message_and_order__ok():

    """
    Message and order
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    message = 'Must be greater than 0'
    order = 3

    # act
    result = service._create_instance(
        field_id=field.id,
        type=FieldRuleType.VALIDATOR,
        template_id=template.id,
        message=message,
        order=order,
    )

    # assert
    assert result.message == message
    assert result.order == order


@pytest.mark.parametrize(
    ('field_type', 'operator'),
    (
        (FieldType.STRING, FieldRuleOperator.EQUAL),
        (FieldType.TEXT, FieldRuleOperator.CONTAIN),
        (FieldType.URL, FieldRuleOperator.NOT_EQUAL),
        (FieldType.CHECKBOX, FieldRuleOperator.NOT_CONTAIN),
        (FieldType.RADIO, FieldRuleOperator.EQUAL),
        (FieldType.DROPDOWN, FieldRuleOperator.NOT_EQUAL),
        (FieldType.USER, FieldRuleOperator.EQUAL),
        (FieldType.DATE, FieldRuleOperator.GREATER_THAN),
        (FieldType.NUMBER, FieldRuleOperator.LESS_THAN),
    ),
)
def test__validate__allowed_operator__ok(field_type, operator):

    """
    Allowed operator for field type
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=field_type,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        name='Ruleset',
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        field=field.api_name,
        operator=operator,
        value='1',
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._validate(group_and=group_and)

    # assert
    assert result is None


@pytest.mark.parametrize(
    ('field_type', 'operator'),
    (
        (FieldType.STRING, FieldRuleOperator.GREATER_THAN),
        (FieldType.TEXT, FieldRuleOperator.LESS_THAN),
        (FieldType.URL, FieldRuleOperator.GREATER_THAN),
        (FieldType.CHECKBOX, FieldRuleOperator.LESS_THAN),
        (FieldType.RADIO, FieldRuleOperator.CONTAIN),
        (FieldType.DROPDOWN, FieldRuleOperator.NOT_CONTAIN),
        (FieldType.USER, FieldRuleOperator.GREATER_THAN),
        (FieldType.DATE, FieldRuleOperator.CONTAIN),
        (FieldType.NUMBER, FieldRuleOperator.NOT_CONTAIN),
        (FieldType.FILE, FieldRuleOperator.EQUAL),
    ),
)
def test__validate__operator_not_allowed__raise_exception(
    field_type,
    operator,
):

    """
    Operator is not allowed for field type
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=field_type,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        field=field.api_name,
        operator=operator,
        value='1',
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    with pytest.raises(FieldTemplateRuleSetServiceException) as ex:
        service._validate(group_and=group_and)

    # assert
    assert ex.value.message == pt_messages.MSG_PT_0078(
        field=field,
        operator=operator,
        field_type=field_type,
    )


def test__create_group_and__default_params__ok():

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and_data = {
        'operator': FieldRuleOperator.EQUAL,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._create_group_and(
        group_or=group_or,
        group_and_data=group_and_data,
    )

    # assert
    assert result.group_or_id == group_or.id
    assert result.account_id == account.id
    assert result.template_id == template.id
    assert result.operator == FieldRuleOperator.EQUAL
    assert result.field is None
    assert result.value is None
    assert result.api_name.startswith('field-rule-group-and')


def test__create_group_and__api_name_provided__ok():

    """
    api_name provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    api_name = 'group-and-custom-1'
    group_and_data = {
        'api_name': api_name,
        'operator': FieldRuleOperator.EQUAL,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._create_group_and(
        group_or=group_or,
        group_and_data=group_and_data,
    )

    # assert
    assert result.api_name == api_name


def test__create_group_and__api_name_omitted__ok():

    """
    api_name omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and_data = {
        'api_name': '',
        'operator': FieldRuleOperator.EQUAL,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._create_group_and(
        group_or=group_or,
        group_and_data=group_and_data,
    )

    # assert
    assert result.api_name.startswith('field-rule-group-and')


def test__create_group_and__field_and_value_provided__ok():

    """
    field and value provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
        api_name='field-1',
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    value = 'yes'
    group_and_data = {
        'field': field.api_name,
        'operator': FieldRuleOperator.CONTAIN,
        'value': value,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._create_group_and(
        group_or=group_or,
        group_and_data=group_and_data,
    )

    # assert
    assert result.field == field.api_name
    assert result.operator == FieldRuleOperator.CONTAIN
    assert result.value == value


def test__update_group_and__default_params__ok():

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
        api_name='field-1',
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        field=field.api_name,
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    group_and_data = {}
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._update_group_and(
        group_and=group_and,
        group_and_data=group_and_data,
    )

    # assert
    group_and.refresh_from_db()
    assert result == group_and
    assert group_and.field == field.api_name
    assert group_and.operator == FieldRuleOperator.EQUAL
    assert group_and.value == 'yes'


def test__update_group_and__field_in_payload__ok():

    """
    field in payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
        api_name='field-1',
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        field=field.api_name,
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    new_field = 'field-2'
    group_and_data = {
        'field': new_field,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._update_group_and(
        group_and=group_and,
        group_and_data=group_and_data,
    )

    # assert
    group_and.refresh_from_db()
    assert result == group_and
    assert group_and.field == new_field
    assert group_and.operator == FieldRuleOperator.EQUAL
    assert group_and.value == 'yes'


def test__update_group_and__operator_in_payload__ok():

    """
    operator in payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
        api_name='field-1',
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        field=field.api_name,
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    operator = FieldRuleOperator.NOT_EQUAL
    group_and_data = {
        'operator': operator,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._update_group_and(
        group_and=group_and,
        group_and_data=group_and_data,
    )

    # assert
    group_and.refresh_from_db()
    assert result == group_and
    assert group_and.operator == operator
    assert group_and.field == field.api_name
    assert group_and.value == 'yes'


def test__update_group_and__value_in_payload__ok():

    """
    value in payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
        api_name='field-1',
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        field=field.api_name,
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    value = 'no'
    group_and_data = {
        'value': value,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._update_group_and(
        group_and=group_and,
        group_and_data=group_and_data,
    )

    # assert
    group_and.refresh_from_db()
    assert result == group_and
    assert group_and.value == value
    assert group_and.field == field.api_name
    assert group_and.operator == FieldRuleOperator.EQUAL


def test__update_group_and__all_fields_in_payload__ok():

    """
    field, operator and value in payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
        api_name='field-1',
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        field=field.api_name,
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    new_field = 'field-2'
    operator = FieldRuleOperator.CONTAIN
    value = '10'
    group_and_data = {
        'field': new_field,
        'operator': operator,
        'value': value,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._update_group_and(
        group_and=group_and,
        group_and_data=group_and_data,
    )

    # assert
    group_and.refresh_from_db()
    assert result == group_and
    assert group_and.field == new_field
    assert group_and.operator == operator
    assert group_and.value == value


def test__set_groups_and__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and_1 = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        field='field-1',
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    groups_and_data = []
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._update_group_and',
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
    )

    # act
    service._set_groups_and(
        group_or=group_or,
        groups_and_data=groups_and_data,
    )

    # assert
    assert not group_or.groups_and.filter(id=group_and_1.id).exists()
    update_group_and_mock.assert_not_called()
    create_group_and_mock.assert_not_called()


def test__set_groups_and__matching_api_name__ok(mocker):

    """
    Matching api_name
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and_1 = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        field='field-1',
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    group_and_data_1 = {
        'api_name': group_and_1.api_name,
        'operator': FieldRuleOperator.EQUAL,
    }
    groups_and_data = [group_and_data_1]
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._update_group_and',
        return_value=group_and_1,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
    )

    # act
    service._set_groups_and(
        group_or=group_or,
        groups_and_data=groups_and_data,
    )

    # assert
    assert group_or.groups_and.filter(id=group_and_1.id).exists()
    update_group_and_mock.assert_called_once_with(
        group_and=group_and_1,
        group_and_data=group_and_data_1,
    )
    create_group_and_mock.assert_not_called()


def test__set_groups_and__unknown_or_missing_api_name__ok(mocker):

    """
    Unknown or missing api_name
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and_1 = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        field='field-1',
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    group_and_data_1 = {
        'field': 'field-1',
        'operator': FieldRuleOperator.GREATER_THAN,
        'value': '50',
    }
    groups_and_data = [group_and_data_1]
    created_group_and = SimpleNamespace(api_name='group-and-2')
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._update_group_and',
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
        return_value=created_group_and,
    )

    # act
    service._set_groups_and(
        group_or=group_or,
        groups_and_data=groups_and_data,
    )

    # assert
    assert not group_or.groups_and.filter(id=group_and_1.id).exists()
    create_group_and_mock.assert_called_once_with(
        group_or=group_or,
        group_and_data=group_and_data_1,
    )
    update_group_and_mock.assert_not_called()


def test__set_groups_and__mixed_payload__ok(mocker):

    """
    Mixed payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_and_1 = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        field='field-1',
        operator=FieldRuleOperator.EQUAL,
        value='yes',
    )
    group_and_2 = FieldTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-2',
        field='field-1',
        operator=FieldRuleOperator.EQUAL,
        value='no',
    )
    group_and_data_1 = {
        'api_name': group_and_1.api_name,
        'operator': FieldRuleOperator.EQUAL,
    }
    group_and_data_2 = {
        'field': 'field-1',
        'operator': FieldRuleOperator.GREATER_THAN,
        'value': '50',
    }
    groups_and_data = [group_and_data_1, group_and_data_2]
    created_group_and = SimpleNamespace(api_name='group-and-3')
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._update_group_and',
        return_value=group_and_1,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
        return_value=created_group_and,
    )

    # act
    service._set_groups_and(
        group_or=group_or,
        groups_and_data=groups_and_data,
    )

    # assert
    assert group_or.groups_and.filter(id=group_and_1.id).exists()
    assert not group_or.groups_and.filter(id=group_and_2.id).exists()
    update_group_and_mock.assert_called_once_with(
        group_and=group_and_1,
        group_and_data=group_and_data_1,
    )
    create_group_and_mock.assert_called_once_with(
        group_or=group_or,
        group_and_data=group_and_data_2,
    )


def test__create_group_or__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or_data = {}
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    assert result.field_rule_id == ruleset.id
    assert result.account_id == account.id
    assert result.template_id == template.id
    assert result.api_name.startswith('field-rule-group-or')
    create_group_and_mock.assert_not_called()


def test__create_group_or__api_name_provided__ok(mocker):

    """
    api_name provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    api_name = 'group-or-custom-1'
    group_or_data = {
        'api_name': api_name,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    assert result.api_name == api_name
    create_group_and_mock.assert_not_called()


def test__create_group_or__api_name_omitted__ok(mocker):

    """
    api_name omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or_data = {
        'api_name': '',
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    assert result.api_name.startswith('field-rule-group-or')
    create_group_and_mock.assert_not_called()


def test__create_group_or__groups_and_omitted__ok(mocker):

    """
    groups_and omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or_data = {
        'api_name': 'group-or-1',
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    assert result.api_name == 'group-or-1'
    create_group_and_mock.assert_not_called()


def test__create_group_or__groups_and_is_not_none__ok(mocker):

    """
    groups_and is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_and_data = {
        'field': 'field-1',
        'operator': FieldRuleOperator.EQUAL,
        'value': 'yes',
    }
    group_or_data = {
        'api_name': 'group-or-1',
        'groups_and': [group_and_data],
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    create_group_and_mock.assert_called_once_with(
        group_or=result,
        group_and_data=group_and_data,
    )


def test__update_group_or__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_or_data = {}
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_and',
    )

    # act
    result = service._update_group_or(
        group_or=group_or,
        group_or_data=group_or_data,
    )

    # assert
    assert result == group_or
    set_groups_and_mock.assert_not_called()


def test__update_group_or__groups_and_omitted__ok(mocker):

    """
    groups_and omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    group_or_data = {
        'api_name': 'group-or-1',
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_and',
    )

    # act
    result = service._update_group_or(
        group_or=group_or,
        group_or_data=group_or_data,
    )

    # assert
    assert result == group_or
    set_groups_and_mock.assert_not_called()


def test__update_group_or__groups_and_is_not_none__ok(mocker):

    """
    groups_and is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
    )
    groups_and_data = [
        {
            'field': 'field-1',
            'operator': FieldRuleOperator.EQUAL,
            'value': 'yes',
        },
    ]
    group_or_data = {
        'groups_and': groups_and_data,
    }
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_and_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_and',
    )

    # act
    result = service._update_group_or(
        group_or=group_or,
        group_or_data=group_or_data,
    )

    # assert
    assert result == group_or
    set_groups_and_mock.assert_called_once_with(
        group_or=group_or,
        groups_and_data=groups_and_data,
    )


def test__set_groups_or__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or_1 = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    groups_or_data = []
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._update_group_or',
    )
    create_group_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_or',
    )

    # act
    service._set_groups_or(groups_or_data=groups_or_data)

    # assert
    assert not ruleset.groups_or.filter(id=group_or_1.id).exists()
    update_group_or_mock.assert_not_called()
    create_group_or_mock.assert_not_called()


def test__set_groups_or__matching_api_name__ok(mocker):

    """
    Matching api_name
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or_1 = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    group_or_data_1 = {
        'api_name': group_or_1.api_name,
    }
    groups_or_data = [group_or_data_1]
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._update_group_or',
        return_value=group_or_1,
    )
    create_group_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_or',
    )

    # act
    service._set_groups_or(groups_or_data=groups_or_data)

    # assert
    assert ruleset.groups_or.filter(id=group_or_1.id).exists()
    update_group_or_mock.assert_called_once_with(
        group_or=group_or_1,
        group_or_data=group_or_data_1,
    )
    create_group_or_mock.assert_not_called()


def test__set_groups_or__unknown_or_missing_api_name__ok(mocker):

    """
    Unknown or missing api_name
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or_1 = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    group_or_data_1 = {
        'groups_and': [],
    }
    groups_or_data = [group_or_data_1]
    created_group_or = SimpleNamespace(api_name='group-or-2')
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._update_group_or',
    )
    create_group_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_or',
        return_value=created_group_or,
    )

    # act
    service._set_groups_or(groups_or_data=groups_or_data)

    # assert
    assert not ruleset.groups_or.filter(id=group_or_1.id).exists()
    create_group_or_mock.assert_called_once_with(
        group_or_data=group_or_data_1,
    )
    update_group_or_mock.assert_not_called()


def test__set_groups_or__mixed_payload__ok(mocker):

    """
    Mixed payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    group_or_1 = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    group_or_2 = FieldTemplateRuleGroupOr.objects.create(
        ruleset=ruleset,
        account=account,
        template=template,
        api_name='group-or-2',
    )
    group_or_data_1 = {
        'api_name': group_or_1.api_name,
    }
    group_or_data_2 = {
        'groups_and': [],
    }
    groups_or_data = [group_or_data_1, group_or_data_2]
    created_group_or = SimpleNamespace(api_name='group-or-3')
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._update_group_or',
        return_value=group_or_1,
    )
    create_group_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_group_or',
        return_value=created_group_or,
    )

    # act
    service._set_groups_or(groups_or_data=groups_or_data)

    # assert
    assert ruleset.groups_or.filter(id=group_or_1.id).exists()
    assert not ruleset.groups_or.filter(id=group_or_2.id).exists()
    update_group_or_mock.assert_called_once_with(
        group_or=group_or_1,
        group_or_data=group_or_data_1,
    )
    create_group_or_mock.assert_called_once_with(
        group_or_data=group_or_data_2,
    )


def test__create_related__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service._create_related()

    # assert
    assert result is None
    set_groups_or_mock.assert_not_called()


def test__create_related__groups_or_is_none__ok(mocker):

    """
    groups_or is None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service._create_related(groups_or=None)

    # assert
    assert result is None
    set_groups_or_mock.assert_not_called()


def test__create_related__groups_or_is_not_none__ok(mocker):

    """
    groups_or is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    groups_or = [
        {
            'api_name': 'group-or-1',
        },
    ]
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service._create_related(groups_or=groups_or)

    # assert
    assert result is None
    set_groups_or_mock.assert_called_once_with(groups_or_data=groups_or)


def test_create__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_instance_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_instance',
    )
    create_related_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_related',
    )
    create_actions_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._create_actions',
    )

    # act
    result = service.create()

    # assert
    assert result == ruleset
    create_instance_mock.assert_called_once_with()
    create_related_mock.assert_called_once_with()
    create_actions_mock.assert_called_once_with()


def test_partial_update__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
        message=None,
        order=0,
    )
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service.partial_update()

    # assert
    ruleset.refresh_from_db()
    assert result == ruleset
    assert ruleset.message is None
    assert ruleset.order == 0
    assert ruleset.type == FieldRuleType.SHOW
    set_groups_or_mock.assert_not_called()


def test_partial_update__scalar_fields_updated__ok(mocker):

    """
    Scalar fields updated
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
        message=None,
        order=0,
    )
    message = 'Custom message'
    order = 5
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service.partial_update(
        message=message,
        order=order,
        type=FieldRuleType.VALIDATOR,
    )

    # assert
    ruleset.refresh_from_db()
    assert result == ruleset
    assert ruleset.message == message
    assert ruleset.order == order
    assert ruleset.type == FieldRuleType.VALIDATOR
    set_groups_or_mock.assert_not_called()


def test_partial_update__groups_or_is_none__ok(mocker):

    """
    groups_or is None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
        order=0,
    )
    order = 3
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service.partial_update(
        order=order,
        groups_or=None,
    )

    # assert
    ruleset.refresh_from_db()
    assert result == ruleset
    assert ruleset.order == order
    set_groups_or_mock.assert_not_called()


def test_partial_update__groups_or_is_not_none__ok(mocker):

    """
    groups_or is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        name='Field',
        type=FieldType.STRING,
        order=1,
    )
    ruleset = FieldTemplateRuleSet.objects.create(
        field=field,
        account=account,
        template=template,
        type=FieldRuleType.SHOW,
        order=0,
    )
    order = 3
    groups_or = [
        {
            'api_name': 'group-or-1',
        },
    ]
    service = FieldTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.templates.field_template_rule.'
        'FieldTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service.partial_update(
        order=order,
        groups_or=groups_or,
    )

    # assert
    ruleset.refresh_from_db()
    assert result == ruleset
    assert ruleset.order == order
    set_groups_or_mock.assert_called_once_with(groups_or_data=groups_or)
