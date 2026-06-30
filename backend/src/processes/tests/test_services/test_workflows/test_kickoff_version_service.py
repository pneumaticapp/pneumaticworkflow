import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleType,
    FieldType,
    LabelPosition,
)
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRule,
)
from src.processes.services.workflows.kickoff_version import (
    KickoffUpdateVersionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)


pytestmark = pytest.mark.django_db


def test__update_field__no_fieldset__ok():

    """
    fieldset is None (default)
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data = {
        'api_name': 'field-1',
        'name': 'Test field',
        'description': 'Desc',
        'type': FieldType.STRING,
        'is_required': True,
        'is_hidden': False,
        'order': 1,
        'dataset_id': None,
    }

    # act
    field, created = service._update_field(
        template=field_data,
        fieldset=None,
    )

    # assert
    assert created is True
    assert field.kickoff == kickoff
    assert field.api_name == 'field-1'
    assert field.name == 'Test field'
    assert field.description == 'Desc'
    assert field.type == FieldType.STRING
    assert field.is_required is True
    assert field.is_hidden is False
    assert field.order == 1
    assert field.workflow == kickoff.workflow
    assert field.account == kickoff.account
    assert field.dataset_id is None
    assert field.fieldset is None


def test__update_field__fieldset__ok():

    """
    fieldset provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='Test fieldset',
        api_name='fs-1',
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data = {
        'api_name': 'field-1',
        'name': 'Number field',
        'description': '',
        'type': FieldType.NUMBER,
        'is_required': False,
        'is_hidden': True,
        'order': 2,
        'dataset_id': None,
    }

    # act
    field, created = service._update_field(
        template=field_data,
        fieldset=fieldset,
    )

    # assert
    assert created is True
    assert field.kickoff == kickoff
    assert field.fieldset == fieldset
    assert field.api_name == 'field-1'
    assert field.name == 'Number field'
    assert field.type == FieldType.NUMBER
    assert field.is_required is False
    assert field.is_hidden is True
    assert field.order == 2


def test__update_field_selections__provided__ok():

    """
    selections provided — creates and deletes stale
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        api_name='field-1',
        name='Checkbox',
        type=FieldType.CHECKBOX,
        order=1,
    )

    # stale selection to be deleted
    stale_selection = FieldSelection.objects.create(
        field=field,
        api_name='sel-old',
        value='Old value',
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data = {
        'selections': [
            {
                'api_name': 'sel-1',
                'value': 'First',
            },
            {
                'api_name': 'sel-2',
                'value': 'Second',
            },
        ],
    }

    # act
    service._update_field_selections(
        field=field,
        field_data=field_data,
    )

    # assert
    selections = field.selections.order_by('api_name')
    assert selections.count() == 2
    assert selections[0].api_name == 'sel-1'
    assert selections[0].value == 'First'
    assert selections[1].api_name == 'sel-2'
    assert selections[1].value == 'Second'
    assert FieldSelection.objects.filter(
        id=stale_selection.id,
    ).exists() is False


def test__update_field_selections__empty__skip():

    """
    no selections — skips
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        api_name='field-1',
        name='Text field',
        type=FieldType.STRING,
        order=1,
    )
    existing_selection = FieldSelection.objects.create(
        field=field,
        api_name='sel-existing',
        value='Existing',
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data = {}

    # act
    service._update_field_selections(
        field=field,
        field_data=field_data,
    )

    # assert
    assert field.selections.count() == 1
    assert field.selections.filter(
        id=existing_selection.id,
    ).exists() is True


def test__update_fieldset_rules__rules_data_is_none__delete_all():

    """
    rules_data is None — defaults to empty, deletes all
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    existing_rule = fieldset.rules.first()
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )

    # act
    service._update_fieldset_rules(
        fieldset=fieldset,
        rules_data=None,
    )

    # assert
    assert fieldset.rules.count() == 0
    assert FieldSetRule.objects.filter(
        id=existing_rule.id,
    ).exists() is False


def test__update_fieldset_rules__provided__ok():

    """
    rules_data provided — creates and deletes stale
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='50',
    )

    # stale rule to be deleted
    stale_rule = fieldset.rules.first()
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    rules_data = [
        {
            'api_name': 'rule-1',
            'type': FieldSetRuleType.SUM_EQUAL,
            'value': '100',
        },
    ]

    # act
    service._update_fieldset_rules(
        fieldset=fieldset,
        rules_data=rules_data,
    )

    # assert
    rules = fieldset.rules.all()
    assert rules.count() == 1
    assert rules[0].api_name == 'rule-1'
    assert rules[0].type == FieldSetRuleType.SUM_EQUAL
    assert rules[0].value == '100'
    assert rules[0].account_id == account.id
    assert FieldSetRule.objects.filter(
        id=stale_rule.id,
    ).exists() is False


def test__update_field_rules__provided__ok():

    """
    rules provided — links rules
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    rule_1 = fieldset.rules.first()
    field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        fieldset=fieldset,
        api_name='field-1',
        name='Number field',
        type=FieldType.NUMBER,
        order=1,
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data = {
        'rules': [
            {'api_name': rule_1.api_name},
        ],
    }

    # act
    service._update_field_rules(
        field=field,
        field_data=field_data,
        fieldset=fieldset,
    )

    # assert
    assert field.rules.count() == 1
    assert field.rules.filter(id=rule_1.id).exists() is True


def test__update_field_rules__empty__clear():

    """
    no rules — clears rules
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    rule_1 = fieldset.rules.first()
    field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        fieldset=fieldset,
        api_name='field-1',
        name='Number field',
        type=FieldType.NUMBER,
        order=1,
    )
    field.rules.add(rule_1)
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data = {}

    # act
    service._update_field_rules(
        field=field,
        field_data=field_data,
        fieldset=fieldset,
    )

    # assert
    assert field.rules.count() == 0


def test__update_fields__provided__ok(mocker):

    """
    fields data provided — deletes stale fields
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    field_1 = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        api_name='field-1',
        name='Field 1',
        type=FieldType.STRING,
        order=1,
    )

    # stale field to be deleted
    stale_field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        api_name='field-stale',
        name='Stale',
        type=FieldType.STRING,
        order=2,
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data_1 = {
        'api_name': 'field-1',
        'name': 'Field 1',
        'description': '',
        'type': FieldType.STRING,
        'is_required': False,
        'is_hidden': False,
        'order': 1,
        'dataset_id': None,
    }
    data = [field_data_1]

    update_field_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field',
        return_value=(field_1, True),
    )
    update_field_selections_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field_selections',
    )

    # act
    service._update_fields(data=data)

    # assert
    update_field_mock.assert_called_once_with(
        field_data_1, fieldset=None,
    )
    update_field_selections_mock.assert_called_once_with(
        field_1, field_data_1,
    )
    assert TaskField.objects.filter(
        id=field_1.id,
    ).exists() is True
    assert TaskField.objects.filter(
        id=stale_field.id,
    ).exists() is False


def test__update_fs_fields__none__delete_all(mocker):

    """
    fields_data is None — defaults to empty, deletes all
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
    )

    # existing field to be deleted
    existing_field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        fieldset=fieldset,
        api_name='field-old',
        name='Old field',
        type=FieldType.STRING,
        order=1,
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )

    update_field_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field',
    )
    update_field_selections_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field_selections',
    )
    update_field_rules_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field_rules',
    )

    # act
    service._update_fieldset_fields(
        fieldset=fieldset,
        fields_data=None,
    )

    # assert
    update_field_mock.assert_not_called()
    update_field_selections_mock.assert_not_called()
    update_field_rules_mock.assert_not_called()
    assert TaskField.objects.filter(
        id=existing_field.id,
    ).exists() is False


def test__update_fs_fields__provided__ok(mocker):

    """
    fields_data provided — deletes stale fields
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
    )
    field_1 = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        fieldset=fieldset,
        api_name='field-1',
        name='Field 1',
        type=FieldType.STRING,
        order=1,
    )

    # stale field to be deleted
    stale_field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        fieldset=fieldset,
        api_name='field-stale',
        name='Stale',
        type=FieldType.STRING,
        order=2,
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data_1 = {'api_name': 'field-1'}
    fields_data = [field_data_1]

    update_field_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field',
        return_value=(field_1, True),
    )
    update_field_selections_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field_selections',
    )
    update_field_rules_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field_rules',
    )

    # act
    service._update_fieldset_fields(
        fieldset=fieldset,
        fields_data=fields_data,
    )

    # assert
    update_field_mock.assert_called_once_with(
        field_data_1, fieldset=fieldset,
    )
    update_field_selections_mock.assert_called_once_with(
        field_1, field_data_1,
    )
    update_field_rules_mock.assert_called_once_with(
        field_1, field_data_1, fieldset,
    )
    assert TaskField.objects.filter(
        id=field_1.id,
    ).exists() is True
    assert TaskField.objects.filter(
        id=stale_field.id,
    ).exists() is False


def test__update_fieldsets__none__delete_all(mocker):

    """
    data is None — defaults to empty, deletes all
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance

    # existing fieldset to be deleted
    existing_fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-old',
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )

    update_fieldset_rules_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldset_rules',
    )
    update_fieldset_fields_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldset_fields',
    )

    # act
    service._update_fieldsets(data=None)

    # assert
    update_fieldset_rules_mock.assert_not_called()
    update_fieldset_fields_mock.assert_not_called()
    assert FieldSet.objects.filter(
        id=existing_fieldset.id,
    ).exists() is False


def test__update_fieldsets__provided__ok(mocker):

    """
    data provided — creates and deletes stale
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance

    # stale fieldset to be deleted
    stale_fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='Stale FS',
        api_name='fs-stale',
        order=1,
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    rules_data_1 = [
        {
            'api_name': 'rule-1',
            'type': FieldSetRuleType.SUM_EQUAL,
            'value': '100',
        },
    ]
    fields_data_1 = [
        {'api_name': 'field-1'},
    ]
    data = [
        {
            'api_name': 'fs-1',
            'name': 'Fieldset 1',
            'description': 'Desc',
            'kickoff_links': [
                {
                    'order': 11,
                },
            ],
            'label_position': LabelPosition.TOP,
            'layout': FieldSetLayout.VERTICAL,
            'rules': rules_data_1,
            'fields': fields_data_1,
        },
    ]

    update_fieldset_rules_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldset_rules',
    )
    update_fieldset_fields_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldset_fields',
    )

    # act
    service._update_fieldsets(data=data)

    # assert
    fieldset = FieldSet.objects.get(
        kickoff=kickoff,
        api_name='fs-1',
    )
    assert fieldset.name == 'Fieldset 1'
    assert fieldset.description == 'Desc'
    assert fieldset.order == 11
    assert fieldset.label_position == LabelPosition.TOP
    assert fieldset.layout == FieldSetLayout.VERTICAL
    assert fieldset.account_id == account.id
    update_fieldset_rules_mock.assert_called_once_with(
        fieldset=fieldset,
        rules_data=rules_data_1,
    )
    update_fieldset_fields_mock.assert_called_once_with(
        fieldset=fieldset,
        fields_data=fields_data_1,
    )
    assert FieldSet.objects.filter(
        id=stale_fieldset.id,
    ).exists() is False


def test__update_from_version__fields__ok(mocker):

    """
    fields provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    fields_data = [{'api_name': 'field-1'}]
    data = {'fields': fields_data}
    version = 1

    update_fields_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fields',
    )
    update_fieldsets_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldsets',
    )

    # act
    service.update_from_version(
        data=data,
        version=version,
    )

    # assert
    update_fields_mock.assert_called_once_with(
        data=fields_data,
    )
    update_fieldsets_mock.assert_not_called()


def test__update_from_version__no_fields__skip(mocker):

    """
    fields not provided
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    fieldsets_data = []
    data = {'fieldsets': fieldsets_data}
    version = 1

    update_fields_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fields',
    )
    update_fieldsets_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldsets',
    )

    # act
    service.update_from_version(
        data=data,
        version=version,
    )

    # assert
    update_fields_mock.assert_not_called()
    update_fieldsets_mock.assert_called_once_with(
        data=fieldsets_data,
    )


def test__update_from_version__fieldsets__ok(mocker):

    """
    fieldsets provided (not None)
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    fieldsets_data = [{'api_name': 'fs-1'}]
    data = {'fieldsets': fieldsets_data}
    version = 1

    update_fields_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fields',
    )
    update_fieldsets_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldsets',
    )

    # act
    service.update_from_version(
        data=data,
        version=version,
    )

    # assert
    update_fields_mock.assert_not_called()
    update_fieldsets_mock.assert_called_once_with(
        data=fieldsets_data,
    )


def test__update_from_version__no_fieldsets__skip(mocker):

    """
    fieldsets key missing
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    kickoff = workflow.kickoff_instance
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    data = {}
    version = 1

    update_fields_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fields',
    )
    update_fieldsets_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldsets',
    )

    # act
    service.update_from_version(
        data=data,
        version=version,
    )

    # assert
    update_fields_mock.assert_not_called()
    update_fieldsets_mock.assert_not_called()
