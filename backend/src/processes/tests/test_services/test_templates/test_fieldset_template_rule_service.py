import pytest
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldSetRuleType,
    FieldType,
)
from src.processes.messages import fieldset as fs_messages
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.services.exceptions import (
    FieldsetTemplateRuleServiceException,
    FieldsetTemplateRuleSumMaxFieldsNotNumber,
    FieldsetTemplateRuleSumMaxInvalidValue,
)
from src.processes.services.templates.fieldsets.fieldset_rule import (
    FieldsetTemplateRuleService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test__create_instance__default_params__ok():

    """
    Call with default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._create_instance(
        type=FieldSetRuleType.SUM_EQUAL,
        fieldset_id=fieldset.id,
    )

    # assert
    assert service.instance is not None
    assert result is service.instance
    assert service.instance.type == FieldSetRuleType.SUM_EQUAL
    assert service.instance.value is None
    assert service.instance.fieldset_id == fieldset.id
    assert service.instance.account_id == account.id


def test__create_instance__all_params__ok():

    """
    Call with all parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._create_instance(
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
        fieldset_id=fieldset.id,
    )

    # assert
    assert service.instance is not None
    assert service.instance.type == FieldSetRuleType.SUM_EQUAL
    assert service.instance.value == '100'
    assert service.instance.fieldset_id == fieldset.id
    assert service.instance.account_id == account.id


def test__validate_sum_equal__valid__ok():

    """
    Value from kwargs, valid number, all NUMBER fields → ok
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    field = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        api_name='num',
        order=1,
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100.5',
    )
    rule.fields.add(field)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    result = service._validate_sum_equal()

    # assert
    assert result == 100.5


def test__validate_sum_equal__empty_value__raise_exception():

    """
    Value is empty → raises SumMaxInvalidValue
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value=None,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxInvalidValue) as ex:
        service._validate_sum_equal()

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0004


def test__validate_sum_equal__non_numeric__raise_exception():

    """
    Value is non-numeric → raises SumMaxInvalidValue
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='abc',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxInvalidValue) as ex:
        service._validate_sum_equal()

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0004


@pytest.mark.parametrize(
    'field_type',
    (
        FieldType.STRING,
        FieldType.TEXT,
        FieldType.RADIO,
        FieldType.CHECKBOX,
        FieldType.DATE,
        FieldType.URL,
        FieldType.DROPDOWN,
        FieldType.FILE,
        FieldType.USER,
    ),
)
def test__validate_sum_equal__non_number_type__raise_exception(field_type):

    """
    Non-NUMBER field exists → raises SumMaxFieldsNotNumber
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    field = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='String field',
        type=field_type,
        api_name='str_field',
        order=1,
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    rule.fields.add(field)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxFieldsNotNumber) as ex:
        service._validate_sum_equal()

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0003


def test__validate__call_method_by_type__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )
    validate_sum_equal_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._validate_sum_equal',
    )
    kwargs = {'type': FieldSetRuleType.SUM_EQUAL}

    # act
    service._validate(**kwargs)

    # assert
    validate_sum_equal_mock.assert_called_once_with(**kwargs)


def test_get_valid_fields__all_found__ok():

    """
    All fields found → returns list
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    field_1_api_name = 'field_1'
    field1 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.STRING,
        api_name=field_1_api_name,
        order=1,
    )
    field_2_api_name = 'field_2'
    field2 = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        api_name=field_2_api_name,
        order=2,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.instance = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
    )

    # act
    result = service._get_valid_fields([field_1_api_name, field_2_api_name])

    # assert
    assert len(result) == 2
    assert field1 in result
    assert field2 in result


def test_get_valid_fields__type_from_kwargs__ok():

    """
    rule_type from kwargs
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    field_api_name = 'field_1'
    field = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        api_name=field_api_name,
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.instance = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
    )

    # act
    result = service._get_valid_fields(
        fields_api_names=[field_api_name],
        type=FieldSetRuleType.SUM_EQUAL,
    )

    # assert
    assert result == [field]


def test_get_valid_fields__type_from_instance__ok():

    """
    rule_type from instance
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    field_api_name = 'field_1'
    field = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        api_name=field_api_name,
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.instance = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
    )

    # act
    result = service._get_valid_fields(
        fields_api_names=[field_api_name],
    )

    # assert
    assert result == [field]


def test_get_valid_fields__one_failed__raise_exception():

    """
    failed_api_names has 1 element → raises exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        api_name='num',
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.instance = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleServiceException) as ex:
        service._get_valid_fields(['missing'])

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0005(
        rule=FieldSetRuleType.SUM_EQUAL,
        field='missing',
    )


def test_get_valid_fields__two_failed__raise_exception():

    """
    failed_api_names has 2 elements → raises exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.instance = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleServiceException) as ex:
        service._get_valid_fields(['missing1', 'missing2'])

    # assert
    assert ex.value.message in {
        fs_messages.MSG_FS_0005(
            rule=FieldSetRuleType.SUM_EQUAL,
            field='missing1',
        ), fs_messages.MSG_FS_0005(
            rule=FieldSetRuleType.SUM_EQUAL,
            field='missing2',
        ),
    }


def test_set_fields__fields_provided__set_fields(mocker):

    """
    Non-empty list → fields are set
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    field_api_name = 'num'
    field = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        api_name=field_api_name,
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
    )
    service.instance = rule
    get_valid_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._get_valid_fields',
        return_value=[field],
    )

    # act
    service._set_fields([field_api_name])

    # assert
    get_valid_fields_mock.assert_called_once_with(['num'])
    assert list(rule.fields.all()) == [field]


def test_set_fields__fields_not_provided__clear_fields(mocker):

    """
    Empty list → fields are cleared
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    field = FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        api_name='num',
        order=1,
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
    )
    rule.fields.add(field)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.instance = rule
    get_valid_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._get_valid_fields',
    )

    # act
    service._set_fields([])

    # assert
    get_valid_fields_mock.assert_not_called()
    assert rule.fields.count() == 0


def test_create_related__fields_provided__ok(mocker):

    """
    fields present in kwargs
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._set_fields',
    )
    fields = ['num']

    # act
    service._create_related(fields=fields)

    # assert
    set_fields_mock.assert_called_once_with(fields)


def test_create_related__fields_provided_empty_list__ok(mocker):

    """
    fields not in kwargs → no-op
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._set_fields',
    )

    # act
    service._create_related(fields=[])

    # assert
    set_fields_mock.assert_called_once_with([])


def test_create_related__fields_not_provided__skip(mocker):

    """
    fields not in kwargs → no-op
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._set_fields',
    )

    # act
    service._create_related()

    # assert
    set_fields_mock.assert_not_called()


def test_create__valid_data__ok(mocker):

    """
    Call with valid data → returns instance
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    service.instance = rule
    create_instance_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._create_instance',
    )
    create_related_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._create_related',
    )
    create_actions_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._create_actions',
    )
    validate_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._validate',
    )

    kwargs = {
        'fields': ['num'],
        'value': '100',
        'type': FieldSetRuleType.SUM_EQUAL,
        'fieldset_id': fieldset.id,
    }

    # act
    result = service.create(**kwargs)

    # assert
    assert result == rule
    create_instance_mock.assert_called_once_with(**kwargs)
    create_related_mock.assert_called_once_with(**kwargs)
    create_actions_mock.assert_called_once_with(**kwargs)
    validate_mock.assert_called_once_with(**kwargs)


def test_partial_update__with_fields__ok(mocker):

    """
    fields in update_kwargs → branch taken
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._set_fields',
    )
    validate_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._validate',
    )
    value = '200'
    fields = ['num']

    # act
    result = service.partial_update(value=value, fields=fields)

    # assert
    set_fields_mock.assert_called_once_with(fields)
    validate_mock.assert_called_once_with(value=value)
    assert result == rule
    rule.refresh_from_db()
    assert rule.value == value


def test_partial_update__without_fields__ok(mocker):

    """
    fields not in update_kwargs → branch skipped
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='100',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._set_fields',
    )
    validate_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.FieldsetTemplateRuleService'
        '._validate',
    )
    super_partial_mock = mocker.patch(
        'src.processes.services.templates.fieldsets'
        '.fieldset_rule.BaseModelService'
        '.partial_update',
        return_value=rule,
    )
    value = '200'

    # act
    result = service.partial_update(value=value)

    # assert
    super_partial_mock.assert_called_once_with(value=value, force_save=True)
    set_fields_mock.assert_not_called()
    validate_mock.assert_called_once_with(value=value)
    assert result == rule
