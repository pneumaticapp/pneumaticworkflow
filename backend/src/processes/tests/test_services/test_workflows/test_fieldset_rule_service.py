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
from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRule,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.services.exceptions import FieldsetServiceException
from src.processes.services.workflows.fieldsets.fieldset_rule import (
    FieldSetRuleService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


# FieldSetRuleService._create_instance


def test__create_instance__with_template__ok(mocker):

    """
    Call with instance_template and fieldset
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset tmpl',
        order=1,
    )
    rule_template = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset_template,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # act
    service._create_instance(
        instance_template=rule_template,
        fieldset=fieldset,
    )

    # assert
    assert service.instance is not None
    assert service.instance.fieldset_id == fieldset.id
    assert service.instance.type == FieldSetRuleType.SUM_MAX
    assert service.instance.value == '100'
    assert service.instance.api_name == rule_template.api_name
    assert service.instance.account_id == account.id


# FieldSetRuleService._validate_sum_max


def test__validate_sum_max__within_threshold__ok(mocker):

    """
    Total within threshold
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='30',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='20',
        order=2,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    service._validate_sum_max(
        fieldset=fieldset,
        value='100',
    )

    # assert - no exception raised


def test__validate_sum_max__exceeds__raise_exception(mocker):

    """
    Total exceeds threshold → exception
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='60',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='50',
        order=2,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    with pytest.raises(FieldsetServiceException) as ex:
        service._validate_sum_max(
            fieldset=fieldset,
            value='100',
        )

    # assert
    assert ex.value.message == fs_messages.MSG_FS_0002(100.0)


def test__validate_sum_max__null_values__skip(mocker):

    """
    Fields with null values skipped
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 1',
        type=FieldType.NUMBER,
        value='30',
        order=1,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 2',
        type=FieldType.NUMBER,
        value='',
        order=2,
    )
    TaskField.objects.create(
        account=account,
        workflow=workflow,
        fieldset=fieldset,
        name='Field 3',
        type=FieldType.NUMBER,
        value='',
        order=3,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # act
    service._validate_sum_max(
        fieldset=fieldset,
        value='100',
    )

    # assert - no exception raised, null/empty fields are skipped


# FieldSetRuleService.validate


def test_validate__known_type__ok(mocker):

    """
    Known type, validator exists
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_sum_max_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._validate_sum_max',
    )

    # act
    service.validate(type=FieldSetRuleType.SUM_MAX)

    # assert
    validate_sum_max_mock.assert_called_once_with(
        type=FieldSetRuleType.SUM_MAX,
    )


def test_validate__unknown_type__skip(mocker):

    """
    Unknown type, no validator
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_sum_max_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._validate_sum_max',
    )

    # act
    service.validate(type='unknown_type')

    # assert
    validate_sum_max_mock.assert_not_called()


# FieldSetRuleService.create


def test_create__skip_val_false__ok(mocker):

    """
    skip_validation is False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset tmpl',
        order=1,
    )
    rule_template = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset_template,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )

    # act
    result = service.create(
        instance_template=rule_template,
        fieldset=fieldset,
        skip_validation=False,
    )

    # assert
    assert result.type == FieldSetRuleType.SUM_MAX
    assert result.value == '100'
    assert result.fieldset_id == fieldset.id
    validate_mock.assert_called_once_with(
        instance_template=rule_template,
        fieldset=fieldset,
        skip_validation=False,
    )


def test_create__skip_val_not_false__ok(mocker):

    """
    skip_validation is not False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset tmpl',
        order=1,
    )
    rule_template = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset_template,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    # mock
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )

    # act
    result = service.create(
        instance_template=rule_template,
        fieldset=fieldset,
        skip_validation=None,
    )

    # assert
    assert result.type == FieldSetRuleType.SUM_MAX
    assert result.fieldset_id == fieldset.id
    validate_mock.assert_not_called()


# FieldSetRuleService.partial_update


def test_partial_update__valid_data__ok(mocker):

    """
    Call with valid data
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = FieldSet.objects.create(
        account=account,
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    rule = FieldSetRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_MAX,
        value='100',
    )
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=rule,
    )

    # mock
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )

    # act
    result = service.partial_update(value='200')

    # assert
    assert result.value == '200'
    validate_mock.assert_called_once_with(
        value='200',
    )
