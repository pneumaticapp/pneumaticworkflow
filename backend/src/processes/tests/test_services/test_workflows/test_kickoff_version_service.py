import pytest

from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldSetLayout,
    FieldType,
    LabelPosition, FieldSetRuleOperator,
)
from src.processes.models.workflows.fields import (
    FieldRuleSet,
    FieldSelection,
    TaskField,
)
from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRuleSet,
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
    assert field.kickoff_id is None
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


def test__update_fieldset_rulesets__no_key__keep():

    """ A snapshot taken before rulesets carries no such key """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, is_active=True, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    existing_ruleset = fieldset.rulesets.get()
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )

    # act
    service._update_fieldset_rulesets(fieldset=fieldset, version=1)

    # assert
    assert fieldset.rulesets.get().id == existing_ruleset.id


def test__update_fieldset_rulesets__empty_list__delete_all():

    """ An empty list means the fieldset has no rulesets any more """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, is_active=True, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='100',
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )

    # act
    service._update_fieldset_rulesets(
        fieldset=fieldset,
        version=1,
        rulesets_data=[],
    )

    # assert
    assert fieldset.rulesets.count() == 0


def test__update_fieldset_rulesets__provided__ok():

    """ Rulesets from the snapshot are created, stale ones removed """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, is_active=True, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    kickoff = workflow.kickoff_instance
    fieldset = create_test_fieldset(
        workflow=workflow,
        kickoff=kickoff,
        name='FS',
        api_name='fs-1',
        rule_operator=FieldSetRuleOperator.SUM_EQUAL,
        rule_value='50',
    )
    stale_ruleset = fieldset.rulesets.get()
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
    rulesets_data = [
        {
            'api_name': 'ruleset-1',
            'message': 'Must be 100',
            'order': 3,
            'fields': ['field-1'],
            'groups_or': [
                {
                    'api_name': 'group-or-1',
                    'groups_and': [
                        {
                            'api_name': 'group-and-1',
                            'operator': FieldSetRuleOperator.SUM_EQUAL,
                            'value': '100',
                        },
                    ],
                },
            ],
        },
    ]

    # act
    service._update_fieldset_rulesets(
        fieldset=fieldset,
        version=1,
        rulesets_data=rulesets_data,
    )

    # assert
    ruleset = fieldset.rulesets.get()
    assert ruleset.api_name == 'ruleset-1'
    assert ruleset.message == 'Must be 100'
    assert ruleset.order == 3
    assert ruleset.account_id == account.id
    assert list(ruleset.fields.values_list('id', flat=True)) == [field.id]
    group_and = ruleset.groups_or.get().groups_and.get()
    assert group_and.operator == FieldSetRuleOperator.SUM_EQUAL
    assert group_and.value == '100'
    assert FieldSetRuleSet.objects.filter(
        id=stale_ruleset.id,
    ).exists() is False


def test__update_field_rulesets__provided__ok():

    """ Field rulesets from the snapshot are created """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, is_active=True, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    kickoff = workflow.kickoff_instance
    field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        api_name='field-1',
        name='String field',
        type=FieldType.STRING,
        order=1,
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data = {
        'rulesets': [
            {
                'api_name': 'ruleset-1',
                'name': 'Show when yes',
                'type': FieldRuleType.SHOW,
                'message': None,
                'order': 0,
                'groups_or': [
                    {
                        'api_name': 'group-or-1',
                        'groups_and': [
                            {
                                'api_name': 'group-and-1',
                                'field': 'field-1',
                                'operator': FieldRuleOperator.EQUAL,
                                'value': 'yes',
                            },
                        ],
                    },
                ],
            },
        ],
    }

    # act
    service._update_field_rulesets(
        field=field,
        field_data=field_data,
        version=1,
    )

    # assert
    ruleset = field.rulesets.get()
    assert ruleset.api_name == 'ruleset-1'
    assert ruleset.name == 'Show when yes'
    assert ruleset.type == FieldRuleType.SHOW
    group_and = ruleset.groups_or.get().groups_and.get()
    assert group_and.field == 'field-1'
    assert group_and.operator == FieldRuleOperator.EQUAL
    assert group_and.value == 'yes'


def test__update_field_rulesets__empty_list__delete_all():

    """ An empty list means the field has no rulesets any more """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(user=user, is_active=True, tasks_count=1)
    workflow = create_test_workflow(user=user, template=template)
    kickoff = workflow.kickoff_instance
    field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        api_name='field-1',
        name='String field',
        type=FieldType.STRING,
        order=1,
    )
    FieldRuleSet.objects.create(
        account=account,
        workflow=workflow,
        field=field,
        api_name='ruleset-1',
        name='Show',
        type=FieldRuleType.SHOW,
        order=0,
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )

    # act
    service._update_field_rulesets(
        field=field,
        field_data={'rulesets': []},
        version=1,
    )

    # assert
    assert field.rulesets.count() == 0


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


def test__update_fields__rulesets_provided__created():

    """ Top-level kickoff fields must get FieldRuleSet on version update. """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(user=user, template=template)
    kickoff = workflow.kickoff_instance
    field = TaskField.objects.create(
        kickoff=kickoff,
        workflow=workflow,
        account=account,
        api_name='comment',
        name='Comment',
        type=FieldType.STRING,
        order=1,
    )
    service = KickoffUpdateVersionService(
        user=user,
        auth_type=AuthTokenType.USER,
        is_superuser=False,
        instance=kickoff,
    )
    field_data = {
        'api_name': 'comment',
        'name': 'Comment',
        'description': '',
        'type': FieldType.STRING,
        'is_required': False,
        'is_hidden': False,
        'order': 1,
        'dataset_id': None,
        'rulesets': [
            {
                'api_name': 'show-comment',
                'name': 'Show when status is yes',
                'type': FieldRuleType.SHOW,
                'message': None,
                'order': 0,
                'groups_or': [
                    {
                        'api_name': 'group-or-1',
                        'groups_and': [
                            {
                                'api_name': 'group-and-1',
                                'field': 'status',
                                'operator': FieldRuleOperator.EQUAL,
                                'value': 'yes',
                            },
                        ],
                    },
                ],
            },
        ],
    }

    # act
    service._update_fields(data=[field_data], version=2)

    # assert
    ruleset = FieldRuleSet.objects.get(field=field, api_name='show-comment')
    assert ruleset.type == FieldRuleType.SHOW
    group_and = ruleset.groups_or.get().groups_and.get()
    assert group_and.field == 'status'
    assert group_and.value == 'yes'


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
    update_field_rulesets_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field_rulesets',
    )

    # act
    service._update_fieldset_fields(
        fieldset=fieldset,
        fields_data=None,
        version=1,
    )

    # assert
    update_field_mock.assert_not_called()
    update_field_selections_mock.assert_not_called()
    update_field_rulesets_mock.assert_not_called()
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
    update_field_rulesets_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_field_rulesets',
    )

    # act
    service._update_fieldset_fields(
        fieldset=fieldset,
        fields_data=fields_data,
        version=1,
    )

    # assert
    update_field_mock.assert_called_once_with(
        field_data_1, fieldset=fieldset,
    )
    update_field_selections_mock.assert_called_once_with(
        field_1, field_data_1,
    )
    update_field_rulesets_mock.assert_called_once_with(
        field_1, field_data_1, 1,
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

    update_fieldset_rulesets_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldset_rulesets',
    )
    update_fieldset_fields_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldset_fields',
    )

    # act
    service._update_fieldsets(data=None, version=1)

    # assert
    update_fieldset_rulesets_mock.assert_not_called()
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
    rulesets_data_1 = [
        {
            'api_name': 'ruleset-1',
            'message': None,
            'order': 0,
            'fields': [],
            'groups_or': [],
        },
    ]
    fields_data_1 = [
        {'api_name': 'field-1'},
    ]
    data = [
        {
            'api_name': 'fs-1',
            'name': 'Fieldset 1',
            'title': 'Fieldset Title',
            'description': 'Desc',
            'order': 11,
            'label_position': LabelPosition.TOP,
            'layout': FieldSetLayout.VERTICAL,
            'rulesets': rulesets_data_1,
            'fields': fields_data_1,
        },
    ]

    update_fieldset_rulesets_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldset_rulesets',
    )
    update_fieldset_fields_mock = mocker.patch(
        'src.processes.services.workflows.kickoff_version.'
        'KickoffUpdateVersionService._update_fieldset_fields',
    )

    # act
    service._update_fieldsets(data=data, version=1)

    # assert
    fieldset = FieldSet.objects.get(
        kickoff=kickoff,
        api_name='fs-1',
    )
    assert fieldset.name == 'Fieldset 1'
    assert fieldset.title == 'Fieldset Title'
    assert fieldset.description == 'Desc'
    assert fieldset.order == 11
    assert fieldset.label_position == LabelPosition.TOP
    assert fieldset.layout == FieldSetLayout.VERTICAL
    assert fieldset.account_id == account.id
    update_fieldset_rulesets_mock.assert_called_once_with(
        fieldset=fieldset,
        version=1,
        rulesets_data=rulesets_data_1,
    )
    update_fieldset_fields_mock.assert_called_once_with(
        fieldset=fieldset,
        fields_data=fields_data_1,
        version=1,
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
        version=version,
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
        version=version,
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
