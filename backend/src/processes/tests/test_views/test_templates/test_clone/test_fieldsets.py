import pytest

from src.processes.enums import (
    FieldSetLayout,
    FieldSetRuleType,
    FieldType,
    LabelPosition,
)
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateKickoff,
    FieldsetTemplateRule,
    FieldsetTemplateTaskTemplate,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_clone__fieldset_copied__ok(api_client):

    """Cloning a template copies its FieldsetTemplate
    to the new template with correct attributes."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='My Fieldset',
        description='Some description',
        label_position=LabelPosition.LEFT,
        layout=FieldSetLayout.HORIZONTAL,
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    assert new_template_id != template.id

    new_fieldsets = FieldsetTemplate.objects.filter(
        template_id=new_template_id,
    )
    assert new_fieldsets.count() == 1
    new_fs = new_fieldsets.first()
    assert new_fs.name == fieldset.name
    assert new_fs.description == fieldset.description
    assert new_fs.label_position == fieldset.label_position
    assert new_fs.layout == fieldset.layout
    assert new_fs.account_id == account.id
    assert new_fs.api_name != fieldset.api_name


def test_clone__fieldset_with_fields__ok(api_client):

    """Cloning copies FieldTemplate records
    belonging to the fieldset."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset with fields',
    )
    field_1 = fieldset.fields.first()
    # fixture creates one STRING field; add a second one
    field_2 = FieldTemplate.objects.create(
        template=template,
        fieldset=fieldset,
        account=account,
        name='Second field',
        type=FieldType.NUMBER,
        order=2,
        is_required=False,
        is_hidden=True,
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    new_fs = FieldsetTemplate.objects.get(template_id=new_template_id)
    new_fields = FieldTemplate.objects.filter(
        fieldset=new_fs,
    ).order_by('order')
    assert new_fields.count() == 2

    nf1 = new_fields[0]
    assert nf1.name == field_1.name
    assert nf1.type == field_1.type
    assert nf1.order == field_1.order
    assert nf1.template_id == new_template_id
    assert nf1.kickoff is None
    assert nf1.task is None

    nf2 = new_fields[1]
    assert nf2.name == field_2.name
    assert nf2.type == field_2.type
    assert nf2.order == field_2.order
    assert nf2.is_hidden == field_2.is_hidden


def test_clone__fieldset_with_selections__ok(api_client):

    """Cloning copies FieldTemplateSelection records
    for dropdown fields in a fieldset."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset with dropdown',
    )
    # Replace the default STRING field with a DROPDOWN + selections
    fieldset.fields.all().delete()
    field = FieldTemplate.objects.create(
        template=template,
        fieldset=fieldset,
        account=account,
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        order=1,
    )
    sel_1 = FieldTemplateSelection.objects.create(
        template=template,
        field_template=field,
        value='Option A',
    )
    sel_2 = FieldTemplateSelection.objects.create(
        template=template,
        field_template=field,
        value='Option B',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    new_fs = FieldsetTemplate.objects.get(template_id=new_template_id)
    new_field = FieldTemplate.objects.get(fieldset=new_fs)
    new_selections = FieldTemplateSelection.objects.filter(
        field_template=new_field,
    ).order_by('value')
    assert new_selections.count() == 2
    assert new_selections[0].value == sel_1.value
    assert new_selections[0].template_id == new_template_id
    assert new_selections[1].value == sel_2.value
    assert new_selections[1].template_id == new_template_id


def test_clone__fieldset_with_rules__ok(api_client):

    """Cloning copies FieldsetTemplateRule records
    and preserves the rule-field M2M relationships."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset with rules',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='100',
    )
    # fixture creates a NUMBER field + rule; link them via M2M
    field = fieldset.fields.first()
    rule = fieldset.rules.first()
    field.rules.add(rule)

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    new_fs = FieldsetTemplate.objects.get(template_id=new_template_id)

    new_rules = FieldsetTemplateRule.objects.filter(fieldset=new_fs)
    assert new_rules.count() == 1
    new_rule = new_rules.first()
    assert new_rule.type == rule.type
    assert new_rule.value == rule.value
    assert new_rule.id != rule.id
    assert new_rule.api_name != rule.api_name

    new_field = FieldTemplate.objects.get(fieldset=new_fs)
    assert list(new_field.rules.all()) == [new_rule]


def test_clone__multiple_fieldsets__ok(api_client):

    """Cloning a template with multiple fieldsets
    copies all of them."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fs_1 = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset One',
    )
    fs_2 = create_test_fieldset_template(
        account=account,
        template=template,
        name='Fieldset Two',
    )

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    new_fieldsets = FieldsetTemplate.objects.filter(
        template_id=new_template_id,
    ).order_by('name')
    assert new_fieldsets.count() == 2
    assert new_fieldsets[0].name == fs_1.name
    assert new_fieldsets[1].name == fs_2.name

    assert new_fieldsets[0].fields.count() == 1
    assert new_fieldsets[1].fields.count() == 1


def test_clone__no_kickoff_task_links__ok(api_client):

    """Cloning does NOT create FieldsetTemplateKickoff
    or FieldsetTemplateTaskTemplate records."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    task = template.tasks.first()
    kickoff = template.kickoff_instance
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=kickoff,
        task=task,
        name='Linked fieldset',
    )
    # Verify original has links
    assert FieldsetTemplateKickoff.objects.filter(
        fieldset=fieldset,
    ).exists()
    assert FieldsetTemplateTaskTemplate.objects.filter(
        fieldset=fieldset,
    ).exists()

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    new_fs = FieldsetTemplate.objects.get(template_id=new_template_id)

    assert not FieldsetTemplateKickoff.objects.filter(
        fieldset=new_fs,
    ).exists()
    assert not FieldsetTemplateTaskTemplate.objects.filter(
        fieldset=new_fs,
    ).exists()


def test_clone__no_fieldsets__ok(api_client):

    """Cloning a template without fieldsets still works
    and creates no fieldsets on the clone."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    assert FieldsetTemplate.objects.filter(
        template_id=new_template_id,
    ).count() == 0


def test_clone__fieldset_rule_multi_fields__ok(api_client):

    """Cloning preserves a rule linked to multiple fields
    via M2M."""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(user=user, tasks_count=1)
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name='Multi-field rule fieldset',
        rule_type=FieldSetRuleType.SUM_EQUAL,
        rule_value='200',
    )
    field_1 = fieldset.fields.first()
    # fixture creates one NUMBER field; add a second one
    field_2 = FieldTemplate.objects.create(
        template=template,
        fieldset=fieldset,
        account=account,
        name='Amount B',
        type=FieldType.NUMBER,
        order=2,
    )
    rule = fieldset.rules.first()
    # Link both fields to the rule
    for field in fieldset.fields.all():
        field.rules.add(rule)

    # act
    response = api_client.post(f'/templates/{template.id}/clone')

    # assert
    assert response.status_code == 200
    new_template_id = response.data['id']
    new_fs = FieldsetTemplate.objects.get(template_id=new_template_id)

    new_rule = FieldsetTemplateRule.objects.get(fieldset=new_fs)
    assert new_rule.value == rule.value
    assert new_rule.type == rule.type

    rule_fields = new_rule.fields.order_by('order')
    assert rule_fields.count() == 2
    assert rule_fields[0].name == field_1.name
    assert rule_fields[1].name == field_2.name
