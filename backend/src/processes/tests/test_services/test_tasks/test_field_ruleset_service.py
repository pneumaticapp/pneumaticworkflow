import pytest
from django.contrib.auth import get_user_model

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateRuleGroupAnd,
    FieldTemplateRuleGroupOr,
    FieldTemplateRuleSet,
)
from src.processes.models.workflows.fields import (
    TaskField,
)
from src.processes.services.tasks.fields.field import TaskFieldService
from src.processes.services.tasks.fields.field_ruleset import (
    FieldRuleSetService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_create__from_template__creates_ruleset_tree():

    """ Creates FieldRuleSet and groups from template """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        account=account,
        template=template,
        task=task_template,
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
    )
    ruleset_template = FieldTemplateRuleSet.objects.create(
        account=account,
        template=template,
        field=field_template,
        name='Show rule',
        type=FieldRuleType.SHOW,
        message='Custom validation message',
        order=1,
        api_name='ruleset-1',
    )
    group_or_template = FieldTemplateRuleGroupOr.objects.create(
        account=account,
        template=template,
        ruleset=ruleset_template,
        api_name='group-or-1',
    )
    FieldTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=group_or_template,
        field='source-field-api-name',
        operator=FieldRuleOperator.EQUAL,
        value='active',
        api_name='group-and-1',
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.first()
    task_field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
    )
    service = FieldRuleSetService(user=user)

    # act
    ruleset = service.create(
        instance_template=ruleset_template,
        field=task_field,
        workflow=workflow,
    )

    # assert
    assert ruleset.account == account
    assert ruleset.workflow == workflow
    assert ruleset.field == task_field
    assert ruleset.name == 'Show rule'
    assert ruleset.type == FieldRuleType.SHOW
    assert ruleset.message == 'Custom validation message'
    assert ruleset.order == 1
    assert ruleset.api_name == 'ruleset-1'

    groups_or = list(ruleset.groups_or.all())
    assert len(groups_or) == 1
    group_or = groups_or[0]
    assert group_or.api_name == 'group-or-1'
    assert group_or.account == account
    assert group_or.workflow == workflow

    groups_and = list(group_or.groups_and.all())
    assert len(groups_and) == 1
    group_and = groups_and[0]
    assert group_and.api_name == 'group-and-1'
    assert group_and.field == 'source-field-api-name'
    assert group_and.operator == FieldRuleOperator.EQUAL
    assert group_and.value == 'active'
    assert group_and.account == account
    assert group_and.workflow == workflow


def test_create__dict_groups__creates_ruleset_tree():

    """ Creates FieldRuleSet and groups from dict data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.first()
    task_field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
    )
    groups_or_data = [
        {
            'api_name': 'custom-or-1',
            'groups_and': [
                {
                    'api_name': 'custom-and-1',
                    'field': 'field-2',
                    'operator': FieldRuleOperator.NOT_EQUAL,
                    'value': 'draft',
                },
            ],
        },
    ]
    service = FieldRuleSetService(user=user)

    # act
    ruleset = service.create(
        field=task_field,
        workflow=workflow,
        name='Validator rule',
        type=FieldRuleType.VALIDATOR,
        message='Error text',
        order=2,
        api_name='custom-ruleset-1',
        groups_or=groups_or_data,
    )

    # assert
    assert ruleset.name == 'Validator rule'
    assert ruleset.type == FieldRuleType.VALIDATOR
    assert ruleset.message == 'Error text'
    assert ruleset.order == 2
    assert ruleset.api_name == 'custom-ruleset-1'

    groups_or = list(ruleset.groups_or.all())
    assert len(groups_or) == 1
    assert groups_or[0].api_name == 'custom-or-1'

    groups_and = list(groups_or[0].groups_and.all())
    assert len(groups_and) == 1
    assert groups_and[0].api_name == 'custom-and-1'
    assert groups_and[0].field == 'field-2'
    assert groups_and[0].operator == FieldRuleOperator.NOT_EQUAL
    assert groups_and[0].value == 'draft'


def test_task_field_service__create__calls_field_ruleset_service(mocker):

    """ TaskFieldService.create triggers FieldRuleSetService.create """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        account=account,
        template=template,
        task=task_template,
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
    )
    ruleset_template = FieldTemplateRuleSet.objects.create(
        account=account,
        template=template,
        field=field_template,
        name='Rule 1',
        type=FieldRuleType.SHOW,
        api_name='rule-1',
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.first()
    field_ruleset_service_init_mock = mocker.patch.object(
        FieldRuleSetService,
        attribute='__init__',
        return_value=None,
    )
    field_ruleset_service_create_mock = mocker.patch(
        'src.processes.services.tasks.fields.field_ruleset.'
        'FieldRuleSetService.create',
    )
    service = TaskFieldService(user=user)

    # act
    task_field = service.create(
        instance_template=field_template,
        workflow_id=workflow.id,
        task_id=task.id,
        skip_value=True,
    )

    # assert
    field_ruleset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    field_ruleset_service_create_mock.assert_called_once_with(
        instance_template=ruleset_template,
        field=task_field,
        workflow_id=workflow.id,
    )


def test_create__soft_deleted_groups__ignored():

    """ Soft deleted groups are ignored during create """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        account=account,
        template=template,
        task=task_template,
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
    )
    ruleset_template = FieldTemplateRuleSet.objects.create(
        account=account,
        template=template,
        field=field_template,
        name='Show rule',
        type=FieldRuleType.SHOW,
        api_name='ruleset-1',
    )
    group_or_active = FieldTemplateRuleGroupOr.objects.create(
        account=account,
        template=template,
        ruleset=ruleset_template,
        api_name='group-or-active',
        is_deleted=False,
    )
    FieldTemplateRuleGroupOr.objects.create(
        account=account,
        template=template,
        ruleset=ruleset_template,
        api_name='group-or-deleted',
        is_deleted=True,
    )
    FieldTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=group_or_active,
        field='source-field',
        operator=FieldRuleOperator.EQUAL,
        value='active',
        api_name='group-and-active',
        is_deleted=False,
    )
    FieldTemplateRuleGroupAnd.objects.create(
        account=account,
        template=template,
        group_or=group_or_active,
        field='source-field',
        operator=FieldRuleOperator.EQUAL,
        value='deleted',
        api_name='group-and-deleted',
        is_deleted=True,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.first()
    task_field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
    )
    service = FieldRuleSetService(user=user)

    # act
    ruleset = service.create(
        instance_template=ruleset_template,
        field=task_field,
        workflow=workflow,
    )

    # assert
    groups_or = list(ruleset.groups_or.all())
    assert len(groups_or) == 1
    assert groups_or[0].api_name == 'group-or-active'

    groups_and = list(groups_or[0].groups_and.all())
    assert len(groups_and) == 1
    assert groups_and[0].api_name == 'group-and-active'


def test_create__without_user__account_from_field_fallback_ok():

    """ Falls back to field account if user is None """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.first()
    task_field = TaskField.objects.create(
        account=account,
        workflow=workflow,
        task=task,
        name='Field 1',
        type=FieldType.STRING,
        api_name='field-1',
    )
    service = FieldRuleSetService(user=None)

    # act
    ruleset = service.create(
        field=task_field,
        name='Validator rule',
        type=FieldRuleType.VALIDATOR,
        api_name='custom-ruleset-1',
    )

    # assert
    assert ruleset.account == account
    assert ruleset.workflow_id == workflow.id
