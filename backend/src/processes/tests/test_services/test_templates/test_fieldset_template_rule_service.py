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


# FieldsetTemplateRuleService._create_instance


def test__create_instance__default_params__ok(mocker):

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
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._create_instance(
        type=FieldSetRuleType.SUM_MAX,
        fieldset_id=fieldset.id,
    )

    # assert
    assert service.instance is not None
    assert service.instance.type == FieldSetRuleType.SUM_MAX
    assert service.instance.value is None
    assert service.instance.fieldset_id == fieldset.id
    assert service.instance.account_id == account.id


def test__create_instance__all_params__ok(mocker):

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
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._create_instance(
        type=FieldSetRuleType.SUM_MAX,
        value='100',
        fieldset_id=fieldset.id,
    )

    # assert
    assert service.instance is not None
    assert service.instance.type == FieldSetRuleType.SUM_MAX
    assert service.instance.value == '100'
    assert service.instance.fieldset_id == fieldset.id
    assert service.instance.account_id == account.id


# FieldsetTemplateRuleService._validate_sum_max


def test__validate_sum_max__valid__ok(mocker):

    """
    Valid value, all number fields
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._validate_sum_max(
        value='100',
        fieldset_id=fieldset.id,
    )

    # assert - no exception raised


def test__validate_sum_max__empty_value__raise_exception(mocker):

    """
    Value is empty → exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxInvalidValue) as ex:
        service._validate_sum_max(value='')

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0004


def test__validate_sum_max__non_numeric__raise_exception(mocker):

    """
    Value is non-numeric → exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxInvalidValue) as ex:
        service._validate_sum_max(
            value='not_a_number',
        )

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0004


def test__validate_sum_max__non_num_fields__raise_exception(mocker):

    """
    Non-number fields exist → exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='String field',
        type=FieldType.STRING,
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxFieldsNotNumber) as ex:
        service._validate_sum_max(
            value='100',
            fieldset_id=fieldset.id,
        )

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0003


def test__validate_sum_max__value_from_kwargs__ok(mocker):

    """
    Value from kwargs
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._validate_sum_max(
        value='50',
        fieldset_id=fieldset.id,
    )

    # assert - no exception raised


def test__validate_sum_max__value_from_instance__ok(mocker):

    """
    Value from instance
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        order=1,
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    service._validate_sum_max(
        fieldset_id=fieldset.id,
    )

    # assert - no exception raised


def test__validate_sum_max__fset_id_from_kwargs__ok(mocker):

    """
    fieldset_id from kwargs
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._validate_sum_max(
        value='100',
        fieldset_id=fieldset.id,
    )

    # assert - no exception raised


def test__validate_sum_max__fset_id_from_instance__ok(mocker):

    """
    fieldset_id from instance
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        order=1,
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    service._validate_sum_max(
        value='100',
    )

    # assert - no exception raised


# FieldsetTemplateRuleService._validate


def test__validate__type_from_kwargs__ok(mocker):

    """
    Type from kwargs
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_sum_max_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._validate_sum_max',
    )

    # act
    service._validate(type=FieldSetRuleType.SUM_MAX, value='100')

    # assert
    validate_sum_max_mock.assert_called_once_with(
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )


def test__validate__type_from_instance__ok(mocker):

    """
    Type from instance
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # mock
    validate_sum_max_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._validate_sum_max',
    )

    # act
    service._validate(value='200')

    # assert
    validate_sum_max_mock.assert_called_once_with(
        value='200',
    )


# FieldsetTemplateRuleService.create


def test_create__valid_data__ok(mocker):

    """
    Call with valid data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    FieldTemplate.objects.create(
        account=account,
        fieldset=fieldset,
        name='Number field',
        type=FieldType.NUMBER,
        order=1,
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._validate',
    )

    # act
    result = service.create(
        type=FieldSetRuleType.SUM_MAX,
        value='100',
        fieldset_id=fieldset.id,
    )

    # assert
    assert result.type == FieldSetRuleType.SUM_MAX
    assert result.value == '100'
    assert result.fieldset_id == fieldset.id
    validate_mock.assert_called_once_with(
        type=FieldSetRuleType.SUM_MAX,
        value='100',
        fieldset_id=fieldset.id,
    )


# FieldsetTemplateRuleService.partial_update


def test_partial_update__valid_data__ok(mocker):

    """
    Call with valid data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset',
        order=1,
    )
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldsetTemplateRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # mock
    validate_mock = mocker.patch(
        'src.processes.services.templates.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleService._validate',
    )

    # act
    result = service.partial_update(value='200')

    # assert
    assert result.value == '200'
    validate_mock.assert_called_once_with(
        value='200',
    )
