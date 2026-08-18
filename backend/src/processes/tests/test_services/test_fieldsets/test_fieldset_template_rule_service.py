from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldSetRuleOperator,
    FieldType,
)
from src.processes.messages import fieldset as fs_messages
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldSetTemplateRuleGroupAnd,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleSet,
)
from src.processes.services.exceptions import (
    FieldsetTemplateRuleServiceException,
    FieldsetTemplateRuleSumMaxFieldsNotNumber,
    FieldsetTemplateRuleSumMaxInvalidValue,
)
from src.processes.services.fieldsets.fieldset_rule import (
    FieldsetTemplateRuleSetService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test__validate_sum__default_params__ok():

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
    )
    ruleset.fields.add(field_1)
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._validate_sum(group_and=group_and)

    # assert
    assert result == Decimal(100)


def test__validate_sum__falsy_value__raise_exception():

    """
    Falsy value
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value=None,
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxInvalidValue) as ex:
        service._validate_sum(group_and=group_and)

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0004


def test__validate_sum__invalid_decimal__raise_exception():

    """
    Invalid decimal
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='not-a-number',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxInvalidValue) as ex:
        service._validate_sum(group_and=group_and)

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0004


def test__validate_sum__non_number_fields__raise_exception():

    """
    Non-number fields
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.STRING,
        order=1,
    )
    ruleset.fields.add(field_1)
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleSumMaxFieldsNotNumber) as ex:
        service._validate_sum(group_and=group_and)

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0003


def test__validate_sum__all_fields_are_number__ok():

    """
    All fields are NUMBER
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='0.3',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._validate_sum(group_and=group_and)

    # assert
    assert result == Decimal('0.3')


def test__get_valid_fields__default_params__ok():

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
        api_name='field-1',
    )
    fields_api_names = [field_1.api_name]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._get_valid_fields(fields_api_names=fields_api_names)

    # assert
    assert len(result) == 1
    assert result[0] == field_1


def test__get_valid_fields__type_kwarg_provided__raise_exception():

    """
    type kwarg provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    missing_api_name = 'missing-field-1'
    rule_type = 'custom-rule'
    fields_api_names = [missing_api_name]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleServiceException) as ex:
        service._get_valid_fields(
            fields_api_names=fields_api_names,
            type=rule_type,
        )

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0005(
        rule=rule_type,
        field=missing_api_name,
    )


def test__get_valid_fields__type_kwarg_omitted_or_falsy__raise_exception():

    """
    type kwarg omitted or falsy
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    missing_api_name = 'missing-field-1'
    fields_api_names = [missing_api_name]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleServiceException) as ex:
        service._get_valid_fields(
            fields_api_names=fields_api_names,
            type=None,
        )

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0005(
        field=missing_api_name,
    )


def test__get_valid_fields__all_api_names_found__ok():

    """
    All api_names found
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        order=2,
        api_name='field-1',
    )
    field_2 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        order=1,
        api_name='field-2',
    )
    fields_api_names = [field_1.api_name, field_2.api_name]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._get_valid_fields(fields_api_names=fields_api_names)

    # assert
    assert len(result) == 2
    assert result[0] == field_1
    assert result[1] == field_2


def test__get_valid_fields__missing_api_name__raise_exception():

    """
    Missing api_name
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset_1 = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset 1',
    )
    fieldset_2 = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset 2',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset_1,
        account=account,
        template=template,
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset_2,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
        api_name='field-1',
    )
    fields_api_names = [field_1.api_name]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    with pytest.raises(FieldsetTemplateRuleServiceException) as ex:
        service._get_valid_fields(fields_api_names=fields_api_names)

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0005(
        field=field_1.api_name,
    )


def test__get_valid_fields__empty_fields_api_names__ok():

    """
    Empty fields_api_names
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    fields_api_names = []
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )

    # act
    result = service._get_valid_fields(fields_api_names=fields_api_names)

    # assert
    assert result == []


def test__create_instance__default_params__ok():

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._create_instance(
        fieldset_id=fieldset.id,
    )

    # assert
    assert result == service.instance
    assert result.fieldset_id == fieldset.id
    assert result.message is None
    assert result.order == 0
    assert result.template_id == template.id
    assert result.account_id == account.id
    assert result.api_name.startswith('fieldset-ruleset')


def test__create_instance__resolve_template_id_from_fieldset__ok():

    """
    Resolve template_id from fieldset
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._create_instance(
        fieldset_id=fieldset.id,
        template_id=None,
    )

    # assert
    assert result.template_id == fieldset.template_id


def test__create_instance__explicit_template_id__ok():

    """
    Explicit template_id
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template_1 = create_test_template(user=user)
    template_2 = create_test_template(
        user=user,
        name='Test workflow 2',
    )
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template_1,
        name='Fieldset',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._create_instance(
        fieldset_id=fieldset.id,
        template_id=template_2.id,
    )

    # assert
    assert result.template_id == template_2.id
    assert result.fieldset_id == fieldset.id


def test__create_instance__api_name_provided__ok():

    """
    api_name provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    api_name = 'ruleset-custom-1'

    # act
    result = service._create_instance(
        fieldset_id=fieldset.id,
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    result = service._create_instance(
        fieldset_id=fieldset.id,
        api_name='',
    )

    # assert
    assert result.api_name.startswith('fieldset-ruleset')


def test__validate__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_sum_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate_sum',
    )

    # act
    result = service._validate(group_and=group_and)

    # assert
    assert result is None
    validate_sum_mock.assert_called_once_with(group_and=group_and)


def test__validate__type_is_not_validator__ok(mocker):

    """
    Type is not VALIDATOR
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
        type='show',
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_sum_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate_sum',
    )

    # act
    result = service._validate(group_and=group_and)

    # assert
    assert result is None
    validate_sum_mock.assert_not_called()


def test__validate__operator_not_a_sum_operator__ok(mocker):

    """
    Operator not a sum operator
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator='equal',
        value='100',
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_sum_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate_sum',
    )

    # act
    result = service._validate(group_and=group_and)

    # assert
    assert result is None
    validate_sum_mock.assert_not_called()


def test__set_fields__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
        api_name='field-1',
    )
    fields_api_names = [field_1.api_name]
    valid_fields = [field_1]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    get_valid_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._get_valid_fields',
        return_value=valid_fields,
    )

    # act
    service._set_fields(fields_api_names=fields_api_names)

    # assert
    assert service.instance.fields.count() == 1
    assert service.instance.fields.all()[0] == field_1
    get_valid_fields_mock.assert_called_once_with(
        fields_api_names=fields_api_names,
    )


def test__set_fields__non_empty_fields_api_names__ok(mocker):

    """
    Non-empty fields_api_names
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        order=2,
        api_name='field-1',
    )
    field_2 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        order=1,
        api_name='field-2',
    )
    fields_api_names = [field_1.api_name, field_2.api_name]
    valid_fields = [field_1, field_2]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    get_valid_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._get_valid_fields',
        return_value=valid_fields,
    )

    # act
    service._set_fields(fields_api_names=fields_api_names)

    # assert
    assert service.instance.fields.count() == 2
    assert service.instance.fields.all()[0] == field_1
    assert service.instance.fields.all()[1] == field_2
    get_valid_fields_mock.assert_called_once_with(
        fields_api_names=fields_api_names,
    )


def test__set_fields__empty_fields_api_names__ok(mocker):

    """
    Empty fields_api_names
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        order=1,
        api_name='field-1',
    )
    ruleset.fields.add(field_1)
    fields_api_names = []
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    get_valid_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._get_valid_fields',
    )

    # act
    service._set_fields(fields_api_names=fields_api_names)

    # assert
    assert service.instance.fields.count() == 0
    get_valid_fields_mock.assert_not_called()


def test__create_group_and__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and_data = {
        'operator': FieldSetRuleOperator.SUM_EQUAL,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
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
    assert result.operator == FieldSetRuleOperator.SUM_EQUAL
    assert result.value is None
    assert result.api_name.startswith('fieldset-rule-group-and')
    validate_mock.assert_called_once_with(group_and=result)


def test__create_group_and__api_name_provided__ok(mocker):

    """
    api_name provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    api_name = 'group-and-custom-1'
    group_and_data = {
        'operator': FieldSetRuleOperator.SUM_EQUAL,
        'api_name': api_name,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
    )

    # act
    result = service._create_group_and(
        group_or=group_or,
        group_and_data=group_and_data,
    )

    # assert
    assert result.api_name == api_name
    validate_mock.assert_called_once_with(group_and=result)


def test__create_group_and__api_name_omitted__ok(mocker):

    """
    api_name omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and_data = {
        'operator': FieldSetRuleOperator.SUM_EQUAL,
        'api_name': '',
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
    )

    # act
    result = service._create_group_and(
        group_or=group_or,
        group_and_data=group_and_data,
    )

    # assert
    assert result.api_name.startswith('fieldset-rule-group-and')
    validate_mock.assert_called_once_with(group_and=result)


def test__create_group_and__value_provided__ok(mocker):

    """
    value provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    value = '200'
    group_and_data = {
        'operator': FieldSetRuleOperator.SUM_EQUAL,
        'value': value,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
    )

    # act
    result = service._create_group_and(
        group_or=group_or,
        group_and_data=group_and_data,
    )

    # assert
    assert result.value == value
    validate_mock.assert_called_once_with(group_and=result)


def test__update_group_and__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    group_and_data = {}
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
    )

    # act
    result = service._update_group_and(
        group_and=group_and,
        group_and_data=group_and_data,
    )

    # assert
    group_and.refresh_from_db()
    assert result == group_and
    assert group_and.operator == FieldSetRuleOperator.SUM_EQUAL
    assert group_and.value == '100'
    validate_mock.assert_called_once_with(group_and=group_and)


def test__update_group_and__operator_in_payload__ok(mocker):

    """
    operator in payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    operator = FieldSetRuleOperator.SUM_GREATER_THAN
    group_and_data = {
        'operator': operator,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
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
    assert group_and.value == '100'
    validate_mock.assert_called_once_with(group_and=group_and)


def test__update_group_and__value_in_payload__ok(mocker):

    """
    value in payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    value = '200'
    group_and_data = {
        'value': value,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
    )

    # act
    result = service._update_group_and(
        group_and=group_and,
        group_and_data=group_and_data,
    )

    # assert
    group_and.refresh_from_db()
    assert result == group_and
    assert group_and.operator == FieldSetRuleOperator.SUM_EQUAL
    assert group_and.value == value
    validate_mock.assert_called_once_with(group_and=group_and)


def test__update_group_and__operator_and_value_in_payload__ok(mocker):

    """
    operator and value in payload
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    operator = FieldSetRuleOperator.SUM_LESS_THAN
    value = '50'
    group_and_data = {
        'operator': operator,
        'value': value,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
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
    assert group_and.value == value
    validate_mock.assert_called_once_with(group_and=group_and)


def test__update_group_and__no_operator_or_value__ok(mocker):

    """
    No operator or value
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    group_and_data = {
        'api_name': 'group-and-1',
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    validate_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._validate',
    )

    # act
    result = service._update_group_and(
        group_and=group_and,
        group_and_data=group_and_data,
    )

    # assert
    group_and.refresh_from_db()
    assert result == group_and
    assert group_and.operator == FieldSetRuleOperator.SUM_EQUAL
    assert group_and.value == '100'
    validate_mock.assert_called_once_with(group_and=group_and)


def test__set_groups_and__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and_1 = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    groups_and_data = []
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._update_group_and',
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and_1 = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    group_and_data_1 = {
        'api_name': group_and_1.api_name,
        'operator': FieldSetRuleOperator.SUM_EQUAL,
    }
    groups_and_data = [group_and_data_1]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._update_group_and',
        return_value=group_and_1,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and_1 = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    group_and_data_1 = {
        'operator': FieldSetRuleOperator.SUM_GREATER_THAN,
        'value': '50',
    }
    groups_and_data = [group_and_data_1]
    created_group_and = SimpleNamespace(api_name='group-and-2')
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._update_group_and',
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
    )
    group_and_1 = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    group_and_2 = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-2',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='200',
    )
    group_and_data_1 = {
        'api_name': group_and_1.api_name,
        'operator': FieldSetRuleOperator.SUM_EQUAL,
    }
    group_and_data_2 = {
        'operator': FieldSetRuleOperator.SUM_GREATER_THAN,
        'value': '50',
    }
    groups_and_data = [group_and_data_1, group_and_data_2]
    created_group_and = SimpleNamespace(api_name='group-and-3')
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._update_group_and',
        return_value=group_and_1,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or_data = {}
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    assert result.fieldset_rule_id == ruleset.id
    assert result.account_id == account.id
    assert result.template_id == template.id
    assert result.api_name.startswith('fieldset-rule-group-or')
    create_group_and_mock.assert_not_called()


def test__create_group_or__api_name_provided__ok(mocker):

    """
    api_name provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    api_name = 'group-or-custom-1'
    group_or_data = {
        'api_name': api_name,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or_data = {
        'api_name': '',
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    assert result.api_name.startswith('fieldset-rule-group-or')
    create_group_and_mock.assert_not_called()


def test__create_group_or__groups_and_omitted__ok(mocker):

    """
    groups_and omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or_data = {
        'api_name': 'group-or-1',
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    assert result.api_name == 'group-or-1'
    assert result.groups_and.count() == 0
    create_group_and_mock.assert_not_called()


def test__create_group_or__groups_and_is_not_none__ok(mocker):

    """
    groups_and is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_and_data_1 = {
        'operator': FieldSetRuleOperator.SUM_EQUAL,
        'value': '100',
    }
    group_or_data = {
        'groups_and': [group_and_data_1],
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_group_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_and',
    )

    # act
    result = service._create_group_or(group_or_data=group_or_data)

    # assert
    assert result.fieldset_rule_id == ruleset.id
    create_group_and_mock.assert_called_once_with(
        group_or=result,
        group_and_data=group_and_data_1,
    )


def test__update_group_or__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    group_or_data = {}
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_and',
    )

    # act
    result = service._update_group_or(
        group_or=group_or,
        group_or_data=group_or_data,
    )

    # assert
    assert result == group_or
    assert result.api_name == 'group-or-1'
    set_groups_and_mock.assert_not_called()


def test__update_group_or__groups_and_omitted__ok(mocker):

    """
    groups_and omitted
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    group_and_1 = FieldSetTemplateRuleGroupAnd.objects.create(
        group_or=group_or,
        account=account,
        template=template,
        api_name='group-and-1',
        operator=FieldSetRuleOperator.SUM_EQUAL,
        value='100',
    )
    group_or_data = {
        'groups_and': None,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_and',
    )

    # act
    result = service._update_group_or(
        group_or=group_or,
        group_or_data=group_or_data,
    )

    # assert
    assert result == group_or
    assert group_or.groups_and.filter(id=group_and_1.id).exists()
    set_groups_and_mock.assert_not_called()


def test__update_group_or__groups_and_is_not_none__ok(mocker):

    """
    groups_and is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    groups_and_data = [
        {
            'operator': FieldSetRuleOperator.SUM_EQUAL,
            'value': '100',
        },
    ]
    group_or_data = {
        'groups_and': groups_and_data,
    }
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_groups_and_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_and',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or_1 = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    groups_or_data = []
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._update_group_or',
    )
    create_group_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_or',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or_1 = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    group_or_data_1 = {
        'api_name': group_or_1.api_name,
    }
    groups_or_data = [group_or_data_1]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._update_group_or',
        return_value=group_or_1,
    )
    create_group_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_or',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or_1 = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    group_or_data_1 = {
        'api_name': 'unknown-group-or-1',
    }
    groups_or_data = [group_or_data_1]
    created_group_or = SimpleNamespace(api_name='unknown-group-or-1')
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._update_group_or',
    )
    create_group_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_or',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    group_or_1 = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
        api_name='group-or-1',
    )
    group_or_2 = FieldSetTemplateRuleGroupOr.objects.create(
        fieldset_rule=ruleset,
        account=account,
        template=template,
        api_name='group-or-2',
    )
    group_or_data_1 = {
        'api_name': group_or_1.api_name,
    }
    group_or_data_2 = {
        'api_name': 'group-or-3',
    }
    groups_or_data = [group_or_data_1, group_or_data_2]
    created_group_or = SimpleNamespace(api_name='group-or-3')
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    update_group_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._update_group_or',
        return_value=group_or_1,
    )
    create_group_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_group_or',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service._create_related()

    # assert
    assert result is None
    set_fields_mock.assert_not_called()
    set_groups_or_mock.assert_not_called()


def test__create_related__fields_is_none__ok(mocker):

    """
    fields is None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service._create_related(fields=None)

    # assert
    assert result is None
    set_fields_mock.assert_not_called()
    set_groups_or_mock.assert_not_called()


def test__create_related__fields_is_not_none__ok(mocker):

    """
    fields is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    fields = ['field-1']
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service._create_related(fields=fields)

    # assert
    assert result is None
    set_fields_mock.assert_called_once_with(fields_api_names=fields)
    set_groups_or_mock.assert_not_called()


def test__create_related__groups_or_is_none__ok(mocker):

    """
    groups_or is None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service._create_related(groups_or=None)

    # assert
    assert result is None
    set_fields_mock.assert_not_called()
    set_groups_or_mock.assert_not_called()


def test__create_related__groups_or_is_not_none__ok(mocker):

    """
    groups_or is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    groups_or = [
        {
            'api_name': 'group-or-1',
        },
    ]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service._create_related(groups_or=groups_or)

    # assert
    assert result is None
    set_groups_or_mock.assert_called_once_with(groups_or_data=groups_or)
    set_fields_mock.assert_not_called()


def test_create__default_params__ok(mocker):

    """
    Default parameters
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    create_instance_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_instance',
    )
    create_related_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_related',
    )
    create_actions_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._create_actions',
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
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
        message=None,
        order=0,
    )
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service.partial_update()

    # assert
    ruleset.refresh_from_db()
    assert result == ruleset
    assert ruleset.message is None
    assert ruleset.order == 0
    set_fields_mock.assert_not_called()
    set_groups_or_mock.assert_not_called()


def test_partial_update__scalar_fields_updated__ok(mocker):

    """
    Scalar fields updated
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
        message=None,
        order=0,
    )
    message = 'Custom message'
    order = 5
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service.partial_update(
        message=message,
        order=order,
    )

    # assert
    ruleset.refresh_from_db()
    assert result == ruleset
    assert ruleset.message == message
    assert ruleset.order == order
    set_fields_mock.assert_not_called()
    set_groups_or_mock.assert_not_called()


def test_partial_update__fields_is_none__ok(mocker):

    """
    fields is None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
        message=None,
    )
    message = 'Updated message'
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service.partial_update(
        message=message,
        fields=None,
    )

    # assert
    ruleset.refresh_from_db()
    assert result == ruleset
    assert ruleset.message == message
    set_fields_mock.assert_not_called()
    set_groups_or_mock.assert_not_called()


def test_partial_update__fields_is_not_none__ok(mocker):

    """
    fields is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
        message=None,
    )
    message = 'Updated message'
    fields = ['field-1']
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
    )

    # act
    result = service.partial_update(
        message=message,
        fields=fields,
    )

    # assert
    ruleset.refresh_from_db()
    assert result == ruleset
    assert ruleset.message == message
    set_fields_mock.assert_called_once_with(fields_api_names=fields)
    set_groups_or_mock.assert_not_called()


def test_partial_update__groups_or_is_none__ok(mocker):

    """
    groups_or is None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
        order=0,
    )
    order = 3
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
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
    set_fields_mock.assert_not_called()


def test_partial_update__groups_or_is_not_none__ok(mocker):

    """
    groups_or is not None
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user)
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Fieldset',
    )
    ruleset = FieldSetTemplateRuleSet.objects.create(
        fieldset=fieldset,
        account=account,
        template=template,
        order=0,
    )
    order = 3
    groups_or = [
        {
            'api_name': 'group-or-1',
        },
    ]
    service = FieldsetTemplateRuleSetService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=ruleset,
    )
    set_fields_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_fields',
    )
    set_groups_or_mock = mocker.patch(
        'src.processes.services.fieldsets.fieldset_rule.'
        'FieldsetTemplateRuleSetService._set_groups_or',
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
    set_fields_mock.assert_not_called()
