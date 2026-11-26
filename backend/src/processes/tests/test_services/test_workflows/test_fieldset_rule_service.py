import pytest

from src.authentication.enums import AuthTokenType
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRule,
)
from src.processes.services.workflows.fieldsets.fieldset_rule import (
    FieldSetRuleService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
    create_test_fieldset,
)

pytestmark = pytest.mark.django_db


def test__create_instance__with_template__ok():

    """
    Call with instance_template and fieldset
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    fieldset = create_test_fieldset(
        workflow=workflow,
        name='Fieldset',
        order=1,
    )
    fieldset_template = FieldsetTemplate.objects.create(
        template=template,
        account=account,
        name='Fieldset tmpl',
    )
    rule_template = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset_template,
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
    assert service.instance.value == '100'
    assert service.instance.api_name == rule_template.api_name
    assert service.instance.account_id == account.id


def test_create__default_params__ok(mocker):

    """
    Call with default params
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_instance_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_instance',
    )
    create_related_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_related',
    )
    create_actions_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_actions',
    )
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )
    instance = mocker.Mock()
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=instance,
    )
    kwargs = {
        'some': 'value',
    }

    # act
    result = service.create(**kwargs)

    # assert
    create_instance_mock.assert_called_once_with(**kwargs)
    create_related_mock.assert_called_once_with(**kwargs)
    create_actions_mock.assert_called_once_with(**kwargs)
    validate_mock.assert_not_called()
    assert result is instance


def test_create__skip_validation_false__ok(mocker):

    """
    Call with skip_validation=False
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    create_instance_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_instance',
    )
    create_related_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_related',
    )
    create_actions_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService._create_actions',
    )
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )
    instance = mocker.Mock()
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        instance=instance,
    )
    kwargs = {
        'skip_validation': False,
    }

    # act
    result = service.create(**kwargs)

    # assert
    create_instance_mock.assert_called_once_with(**kwargs)
    create_related_mock.assert_called_once_with(**kwargs)
    create_actions_mock.assert_called_once_with(**kwargs)
    validate_mock.assert_called_once_with(**kwargs)
    assert result is instance


def test_partial_update__default_params__ok(mocker):

    """
    Call with default params
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    service = FieldSetRuleService(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )

    result_mock = mocker.Mock()
    mock_super_partial_update = mocker.patch(
        'src.generics.base.service.'
        'BaseModelService.partial_update',
        return_value=result_mock,
    )
    validate_mock = mocker.patch(
        'src.processes.services.workflows.fieldsets.fieldset_rule.'
        'FieldSetRuleService.validate',
    )
    kwargs = {
        'value': 200,
    }

    # act
    result = service.partial_update(**kwargs)

    # assert
    assert result is result_mock
    mock_super_partial_update.assert_called_once_with(**kwargs)
    validate_mock.assert_called_once_with(**kwargs)
