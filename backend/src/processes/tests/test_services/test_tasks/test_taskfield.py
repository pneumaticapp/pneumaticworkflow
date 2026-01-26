import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import (
    FieldType,
    WorkflowEventType,
)
from src.processes.messages import workflow as messages
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.services.tasks.exceptions import (
    TaskFieldException,
)
from src.processes.services.tasks.field import (
    FieldData,
    TaskFieldService,
)
from src.processes.services.tasks.selection import (
    SelectionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_create_instance__task_field__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    field_template = FieldTemplate.objects.create(
        type=FieldType.FILE,
        name='Some file',
        description='Some description',
        api_name='some-api-name',
        order=11,
        task=template.tasks.get(number=1),
        template=template,
        is_required=True,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    value = 'https://john.cena/john.cena'
    markdown_value = '[john.cena](https://john.cena/john.cena)'
    clear_value = 'https://clear-john.cena/john.cena'
    user_id = 123
    group_id = 321
    get_valid_value_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._get_valid_value',
        return_value=FieldData(
            value=value,
            markdown_value=markdown_value,
            clear_value=clear_value,
            user_id=user_id,
            group_id=group_id,
        ),
    )
    raw_value = ['555']
    service = TaskFieldService(
        user=user,
    )

    # act
    service._create_instance(
        instance_template=field_template,
        value=raw_value,
        task_id=task.id,
        workflow_id=workflow.id,
    )

    # assert
    get_valid_value_mock.assert_called_once_with(
        raw_value=raw_value,
        selections=None,
    )
    task_field = service.instance
    assert task_field.kickoff is None
    assert task_field.task == task
    assert task_field.type == field_template.type
    assert task_field.is_required == field_template.is_required
    assert task_field.name == field_template.name
    assert task_field.description == field_template.description
    assert task_field.api_name == field_template.api_name
    assert task_field.order == field_template.order
    assert task_field.value == value
    assert task_field.markdown_value == markdown_value
    assert task_field.clear_value == clear_value
    assert task_field.user_id == user_id
    assert task_field.group_id == group_id


def test_create_instance__kickoff_field__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user, tasks_count=1)
    field_template = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Some text',
        kickoff=template.kickoff_instance,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    value = 'https://john.cena/john.cena'
    markdown_value = '[john.cena](https://john.cena/john.cena)'
    get_valid_value_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._get_valid_value',
        return_value=FieldData(
            value=value,
            markdown_value=markdown_value,
        ),
    )
    raw_value = ['555']
    service = TaskFieldService(
        user=user,
    )

    # act
    service._create_instance(
        instance_template=field_template,
        value=raw_value,
        kickoff_id=workflow.kickoff_instance.id,
        workflow_id=workflow.id,
    )

    # assert
    get_valid_value_mock.assert_called_once_with(
        raw_value=raw_value,
        selections=None,
    )
    task_field = service.instance
    assert task_field.task is None
    assert task_field.kickoff_id == workflow.kickoff_instance.id


def test_create_instance__skip_value__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user, tasks_count=1)
    field_template = FieldTemplate.objects.create(
        type=FieldType.USER,
        name='Some user',
        kickoff=template.kickoff_instance,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    value = 'https://john.cena/john.cena'
    markdown_value = '[john.cena](https://john.cena/john.cena)'
    clear_value = 'https://clear-john.cena/john.cena'
    user_id = 123
    group_id = 321
    get_valid_value_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._get_valid_value',
        return_value=FieldData(
            value=value,
            markdown_value=markdown_value,
            clear_value=clear_value,
            user_id=user_id,
            group_id=group_id,
        ),
    )
    service = TaskFieldService(
        user=user,
    )

    # act
    service._create_instance(
        instance_template=field_template,
        task_id=task.id,
        workflow_id=workflow.id,
        skip_value=True,
    )

    # assert
    get_valid_value_mock.assert_not_called()
    task_field = service.instance
    assert task_field.value == ''
    assert task_field.clear_value is None
    assert task_field.markdown_value is None
    assert task_field.user_id is None
    assert task_field.group_id is None


@pytest.mark.parametrize('field_type', FieldType.TYPES_WITH_SELECTION)
def test_create_selections_with_value__radio_dropdown__not_value__ok(
    field_type,
    mocker,
):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=field_type,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    selection_template = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=field_type,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    create_selection_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'SelectionService.create',
    )

    # act
    service._create_selections_with_value(
        raw_value=None,
        instance_template=field_template,
    )

    # assert
    create_selection_mock.assert_called_once_with(
        instance_template=selection_template,
        field_id=task_field.id,
        is_selected=False,
    )


def test_create_selections_with_value__checkbox__not_value__ok(
    mocker,
):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.CHECKBOX,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    selection_template = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=FieldType.CHECKBOX,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    create_selection_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'SelectionService.create',
    )

    # act
    service._create_selections_with_value(
        raw_value=None,
        instance_template=field_template,
    )

    # assert
    create_selection_mock.assert_called_once_with(
        instance_template=selection_template,
        field_id=task_field.id,
        is_selected=False,
    )


def test_create_selections_with_value__checkbox_api_name__ok(
    mocker,
):

    # arrange
    create_selection_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'SelectionService.create',
    )
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.CHECKBOX,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    selection_template_1 = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_template,
        template=template,
    )
    selection_template_2 = FieldTemplateSelection.objects.create(
        value='second',
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=FieldType.CHECKBOX,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    raw_value = [selection_template_1.api_name]

    # act
    service._create_selections_with_value(
        raw_value=raw_value,
        instance_template=field_template,
    )

    # assert
    create_selection_mock.call_count = 2
    create_selection_mock.assert_has_calls([
        mocker.call(
            instance_template=selection_template_1,
            field_id=task_field.id,
            is_selected=True,
        ),
        mocker.call(
            instance_template=selection_template_2,
            field_id=task_field.id,
            is_selected=False,
        ),
    ])


@pytest.mark.parametrize('field_type', FieldType.TYPES_WITH_SELECTION)
def test_create_selections_with_value__radio_dropdown_api_name__ok(
    field_type,
    mocker,
):

    # arrange
    create_selection_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'SelectionService.create',
    )
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=field_type,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    selection_template_1 = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_template,
        template=template,
    )
    selection_template_2 = FieldTemplateSelection.objects.create(
        value='second',
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=field_type,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    raw_value = selection_template_1.api_name

    # act
    service._create_selections_with_value(
        raw_value=raw_value,
        instance_template=field_template,
    )

    # assert
    create_selection_mock.call_count = 2
    create_selection_mock.assert_has_calls([
        mocker.call(
            instance_template=selection_template_1,
            field_id=task_field.id,
            is_selected=True,
        ),
        mocker.call(
            instance_template=selection_template_2,
            field_id=task_field.id,
            is_selected=False,
        ),
    ])


def test_link_new_attachments__not_attached__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )

    # act
    service._link_new_attachments(
        attachments_ids=[attachment.id],
    )

    # assert
    attachment.refresh_from_db()
    assert attachment.output_id == task_field.id
    assert attachment.workflow_id == workflow.id


def test_link_new_attachments__update_attached__ok():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    attachment = FileAttachment.objects.create(
        output_id=task_field.id,
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )

    # act
    service._link_new_attachments(
        attachments_ids=[attachment.id],
    )

    # assert
    attachment.refresh_from_db()
    assert attachment.output_id == task_field.id
    assert attachment.workflow_id == workflow.id


def test_link_new_attachments__event_attachment__not_link():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
    )

    event = WorkflowEventService.comment_created_event(
        user=user,
        attachments=[attachment.id],
        task=task,
        text=None,
        after_create_actions=False,
    )
    attachment.event = event
    attachment.save()

    service = TaskFieldService(
        instance=task_field,
        user=user,
    )

    # act
    service._link_new_attachments(
        attachments_ids=[attachment.id],
    )

    # assert
    attachment.refresh_from_db()
    assert attachment.output_id is None
    assert attachment.workflow_id is None


def test_link_new_attachments__another_account_attachment__not_update():

    # arrange
    another_account = create_test_account()
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=another_account.id,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )

    # act
    service._link_new_attachments(
        attachments_ids=[attachment.id],
    )

    # assert
    attachment.refresh_from_db()
    assert attachment.output_id is None
    assert attachment.workflow_id is None


def test_link_new_attachments__not_value__not_attached():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )

    # act
    service._link_new_attachments(
        attachments_ids=[],
    )

    # assert
    attachment.refresh_from_db()
    assert attachment.output_id is None
    assert attachment.workflow_id is None


@pytest.mark.parametrize('field_type', FieldType.TYPES_WITH_SELECTION)
def test_update_selections__radio_dropdown__not_value__ok(
    field_type,
    mocker,
):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=field_type,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    selection_template = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=field_type,
        workflow=workflow,
        account=user.account,
    )
    selection = FieldSelection.objects.create(
        field=task_field,
        value=selection_template.value,
        api_name=selection_template.api_name,
        is_selected=False,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    update_selection_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'SelectionService.partial_update',
    )
    selection_service_init_mock = mocker.patch.object(
        SelectionService,
        attribute='__init__',
        return_value=None,
    )

    # act
    service._update_selections(raw_value=None)

    # assert
    selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=user,
    )
    update_selection_mock.assert_called_once_with(
        is_selected=False,
        force_save=True,
    )


def test_update_selections__checkbox__not_value__ok(
    mocker,
):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.CHECKBOX,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    selection_template = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=FieldType.CHECKBOX,
        workflow=workflow,
        account=user.account,
    )
    selection = FieldSelection.objects.create(
        field=task_field,
        value=selection_template.value,
        api_name=selection_template.api_name,
        is_selected=False,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    update_selection_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'SelectionService.partial_update',
    )
    selection_service_init_mock = mocker.patch.object(
        SelectionService,
        attribute='__init__',
        return_value=None,
    )

    # act
    service._update_selections(raw_value=None)

    # assert
    selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=user,
    )
    update_selection_mock.assert_called_once_with(
        is_selected=False,
        force_save=True,
    )


def test_update_selections__checkbox_api_name__ok(
    mocker,
):

    # arrange
    update_selection_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'SelectionService.partial_update',
    )
    selection_service_init_mock = mocker.patch.object(
        SelectionService,
        attribute='__init__',
        return_value=None,
    )
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.CHECKBOX,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    selection_template_1 = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_template,
        template=template,
    )
    selection_template_2 = FieldTemplateSelection.objects.create(
        value='second',
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=FieldType.CHECKBOX,
        workflow=workflow,
        account=user.account,
    )
    selection_1 = FieldSelection.objects.create(
        field=task_field,
        value=selection_template_1.value,
        api_name=selection_template_1.api_name,
        is_selected=True,
    )
    selection_2 = FieldSelection.objects.create(
        field=task_field,
        value=selection_template_2.value,
        api_name=selection_template_2.api_name,
        is_selected=True,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    raw_value = [selection_1.api_name]

    # act
    service._update_selections(raw_value=raw_value)

    # assert
    selection_service_init_mock.call_count = 2
    selection_service_init_mock.assert_has_calls([
        mocker.call(instance=selection_1, user=user),
        mocker.call(instance=selection_2, user=user),
    ])
    update_selection_mock.call_count = 2
    update_selection_mock.assert_has_calls([
        mocker.call(
            is_selected=True,
            force_save=True,
        ),
        mocker.call(
            is_selected=False,
            force_save=True,
        ),
    ])


@pytest.mark.parametrize('field_type', FieldType.TYPES_WITH_SELECTION)
def test_update_selections__radio_dropdown_api_name__ok(
    field_type,
    mocker,
):

    # arrange
    update_selection_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'SelectionService.partial_update',
    )
    selection_service_init_mock = mocker.patch.object(
        SelectionService,
        attribute='__init__',
        return_value=None,
    )
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=field_type,
        name='field',
        template=template,
        api_name='api-name-1',
    )
    selection_template_1 = FieldTemplateSelection.objects.create(
        value='first',
        field_template=field_template,
        template=template,
    )
    selection_template_2 = FieldTemplateSelection.objects.create(
        value='second',
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=field_type,
        workflow=workflow,
        account=user.account,
    )
    selection_1 = FieldSelection.objects.create(
        field=task_field,
        value=selection_template_1.value,
        api_name=selection_template_1.api_name,
        is_selected=False,
    )
    selection_2 = FieldSelection.objects.create(
        field=task_field,
        value=selection_template_2.value,
        api_name=selection_template_2.api_name,
        is_selected=True,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    raw_value = selection_1.api_name

    # act
    service._update_selections(raw_value=raw_value)

    # assert
    selection_service_init_mock.call_count = 2
    selection_service_init_mock.assert_has_calls([
        mocker.call(instance=selection_1, user=user),
        mocker.call(instance=selection_2, user=user),
    ])
    update_selection_mock.call_count = 2
    update_selection_mock.assert_has_calls([
        mocker.call(
            is_selected=True,
            force_save=True,
        ),
        mocker.call(
            is_selected=False,
            force_save=True,
        ),
    ])


def test_partial_update__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=FieldType.NUMBER,
        workflow=workflow,
        account=user.account,
    )
    value = 'value'
    clear_value = 'clear value'
    markdown_value = 'markdown value'
    user_id = 123
    group_id = 321
    get_valid_value_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._get_valid_value',
        return_value=FieldData(
            value=value,
            markdown_value=markdown_value,
            clear_value=clear_value,
            user_id=user_id,
            group_id=group_id,
        ),
    )
    link_new_attachments_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._link_new_attachments',
    )
    update_selections_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._update_selections',
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    raw_value = 'raw value'

    # act
    service.partial_update(value=raw_value)

    # assert
    get_valid_value_mock.assert_called_once_with(
        raw_value=raw_value,
        selections=None,
    )
    link_new_attachments_mock.assert_not_called()
    update_selections_mock.assert_not_called()
    task_field.refresh_from_db()
    assert task_field.value == value
    assert task_field.markdown_value == markdown_value
    assert task_field.clear_value == clear_value
    assert task_field.user_id == user_id
    assert task_field.group_id == group_id


def test_partial_update__type_file__ok(mocker):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    deleted_attachment = FileAttachment.objects.create(
        name='test',
        url='https://test.test',
        size=1488,
        account_id=user.account_id,
        output=task_field,
    )
    value = 'https://john.cena/john.cena'
    clear_value = 'https://clear-john.cena/john.cena'
    markdown_value = '[john.cena](https://john.cena/john.cena)'
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url=value,
        size=1488,
        account_id=user.account_id,
        output=task_field,
    )
    get_valid_value_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._get_valid_value',
        return_value=FieldData(
            value=value,
            markdown_value=markdown_value,
            clear_value=clear_value,
        ),
    )
    link_new_attachments_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._link_new_attachments',
    )
    update_selections_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._update_selections',
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    raw_value = [str(attachment.id)]

    # act
    service.partial_update(value=raw_value)

    # assert
    get_valid_value_mock.assert_called_once_with(
        raw_value=raw_value,
        selections=None,
    )
    assert not FileAttachment.objects.filter(id=deleted_attachment.id).exists()
    link_new_attachments_mock.assert_called_once_with(raw_value)
    update_selections_mock.assert_not_called()
    task_field.refresh_from_db()
    assert task_field.value == value
    assert task_field.markdown_value == markdown_value
    assert task_field.clear_value == clear_value
    assert task_field.user_id is None
    assert task_field.group_id is None


def test_partial_update__type_file_null_value__ok(mocker):

    # arrange
    value = ''
    markdown_value = ''
    clear_value = ''
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        is_required=True,
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    deleted_attachment = FileAttachment.objects.create(
        name='test',
        url='https://test.test',
        size=1488,
        account_id=user.account_id,
        output=task_field,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )
    raw_value = None

    get_valid_value_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._get_valid_value',
        return_value=FieldData(
            value=value,
            markdown_value=markdown_value,
            clear_value=clear_value,
        ),
    )

    link_new_attachments_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._link_new_attachments',
    )
    update_selections_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._update_selections',
    )

    # act
    service.partial_update(value=raw_value)

    # assert
    get_valid_value_mock.assert_called_once_with(
        raw_value=raw_value,
        selections=None,
    )
    assert not FileAttachment.objects.filter(id=deleted_attachment.id).exists()
    link_new_attachments_mock.assert_called_once_with(raw_value)
    update_selections_mock.assert_not_called()
    task_field.refresh_from_db()
    assert task_field.value == value
    assert task_field.markdown_value == markdown_value
    assert task_field.clear_value == clear_value
    assert task_field.user_id is None
    assert task_field.group_id is None


@pytest.mark.parametrize('raw_value', (0, 176516132789, 176516132.00000123))
def test_get_valid_number_value__valid_value__ok(raw_value):

    # arrange
    user = create_test_user()
    service = TaskFieldService(user=user)

    # act
    field_data = service._get_valid_number_value(raw_value=raw_value)

    # assert
    assert field_data.value == raw_value
    assert field_data.markdown_value == raw_value
    assert field_data.clear_value == raw_value


@pytest.mark.parametrize('raw_value', (None, '1,2', '1a'))
def test_get_valid_number_value__invalid_value__raise_exception(raw_value):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    field_api_name = 'api-name-1'
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.NUMBER,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)
    raw_value = None

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_number_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0084
    assert ex.value.api_name == field_api_name


def test_get_valid_string_value__ok(mocker):

    # arrange
    user = create_test_user()
    service = TaskFieldService(user=user)
    raw_value = 'text 123'
    clear_value = 'clear value'
    clear_markdown_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'MarkdownService.clear',
        return_value=clear_value,
    )

    # act
    field_data = service._get_valid_string_value(raw_value=raw_value)

    # assert
    assert field_data.value == raw_value
    assert field_data.markdown_value == raw_value
    assert field_data.clear_value == clear_value
    clear_markdown_mock.assert_called_once_with(raw_value)


@pytest.mark.parametrize('raw_value', (None, 0, []))
def test_get_valid_string_value__invalid_value__raise_exception(
    mocker,
    raw_value,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    field_api_name = 'api-name-1'
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.STRING,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)
    clear_markdown_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'MarkdownService.clear',
    )

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_string_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0025
    assert ex.value.api_name == field_api_name
    clear_markdown_mock.assert_not_called()


def test_get_valid_string_value__over_limit__raise_exception():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    field_api_name = 'api-name-1'
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.STRING,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)
    raw_value = 's' * (TaskFieldService.STRING_LENGTH + 1)

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_string_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0026(
        TaskFieldService.STRING_LENGTH,
    )
    assert ex.value.api_name == field_api_name


def test_get_valid_text_value__ok(mocker):

    # arrange
    user = create_test_user()
    service = TaskFieldService(user=user)
    raw_value = 'text 123'
    clear_value = 'clear value'
    clear_markdown_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'MarkdownService.clear',
        return_value=clear_value,
    )

    # act
    field_data = service._get_valid_text_value(raw_value=raw_value)

    # assert
    assert field_data.value == raw_value
    assert field_data.markdown_value == raw_value
    assert field_data.clear_value == clear_value
    clear_markdown_mock.assert_called_once_with(raw_value)


@pytest.mark.parametrize('raw_value', (None, 0, []))
def test_get_valid_text_value__invalid_value__raise_exception(
    mocker,
    raw_value,
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    field_api_name = 'api-name-1'
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.TEXT,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)
    clear_markdown_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'MarkdownService.clear',
    )

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_text_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0025
    assert ex.value.api_name == field_api_name
    clear_markdown_mock.assert_not_called()


def test_get_valid_dropdown_value__ok(mocker):

    # arrange
    service = TaskFieldService()
    raw_value = 'api_name'
    result_mock = mocker.Mock()
    selections_mock = mocker.Mock()
    get_valid_radio_value_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'TaskFieldService._get_valid_radio_value',
        return_value=result_mock,
    )

    # act
    field_data = service._get_valid_dropdown_value(
        raw_value=raw_value,
        selections=selections_mock,
    )

    # assert
    assert field_data == result_mock
    get_valid_radio_value_mock.assert_called_once_with(
        raw_value, selections=selections_mock,
    )


def test_get_valid_radio_value__api_name__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.RADIO,
        name='Radio field',
        template=template,
        api_name='api-name-1',
    )
    value = 'first option'
    selection_template = FieldTemplateSelection.objects.create(
        value=value,
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_template.api_name,
        is_required=field_template.is_required,
        type=field_template.type,
        workflow=workflow,
        account=user.account,
    )
    selection = FieldSelection.objects.create(
        field=task_field,
        value=selection_template.value,
        api_name=selection_template.api_name,
        is_selected=True,
    )
    service = TaskFieldService(instance=task_field)
    raw_value = selection.api_name
    clear_value = 'clear value'
    clear_markdown_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'MarkdownService.clear',
        return_value=clear_value,
    )

    # act
    field_data = service._get_valid_radio_value(
        raw_value=raw_value,
        selections=field_template.selections.all(),
    )

    # assert
    assert field_data.value == value
    assert field_data.markdown_value == value
    assert field_data.clear_value == clear_value
    clear_markdown_mock.assert_called_once_with(value)


def test_get_valid_radio_value__first_create_selection__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.RADIO,
        name='Radio field',
        template=template,
        api_name='api-name-1',
    )
    value = 'first option'
    selection_template = FieldTemplateSelection.objects.create(
        value=value,
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_template.api_name,
        is_required=field_template.is_required,
        type=field_template.type,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)
    raw_value = selection_template.api_name
    clear_value = 'clear value'
    clear_markdown_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'MarkdownService.clear',
        return_value=clear_value,
    )

    # act
    field_data = service._get_valid_radio_value(
        raw_value=raw_value,
        selections=field_template.selections.all(),
    )

    # assert
    assert field_data.value == selection_template.value
    assert field_data.markdown_value == selection_template.value
    assert field_data.clear_value == clear_value
    clear_markdown_mock.assert_called_once_with(value)


@pytest.mark.parametrize('raw_value', ('abc', None))
def test_get_valid_radio_value__not_string__raise_exception(raw_value):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.RADIO,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_radio_value(
            raw_value=raw_value,
            selections=task_field.selections.all(),
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0028
    assert ex.value.api_name == task_field.api_name


def test_get_valid_radio_value__not_exists_selection__raise_exception():

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user=user)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.RADIO,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_radio_value(
            raw_value='12352',
            selections=task_field.selections.all(),
        )
    # assert
    assert ex.value.message == messages.MSG_PW_0028
    assert ex.value.api_name == task_field.api_name


def test_get_valid_checkbox_value__one_api_name__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.CHECKBOX,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    value = 'first option'
    FieldTemplateSelection.objects.create(
        value='Another value',
        field_template=field_template,
        template=template,
    )
    selection_template = FieldTemplateSelection.objects.create(
        value=value,
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_template.api_name,
        is_required=field_template.is_required,
        type=field_template.type,
        workflow=workflow,
        account=user.account,
    )
    FieldSelection.objects.create(
        field=task_field,
        value=selection_template.value,
        api_name=selection_template.api_name,
        is_selected=True,
    )
    service = TaskFieldService(instance=task_field)
    raw_value = [selection_template.api_name]
    clear_value = 'clear value'
    clear_markdown_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'MarkdownService.clear',
        return_value=clear_value,
    )

    # act
    field_data = service._get_valid_checkbox_value(
        raw_value=raw_value,
        selections=field_template.selections.all(),
    )

    # assert
    assert field_data.value == value
    assert field_data.markdown_value == value
    assert field_data.clear_value == clear_value
    clear_markdown_mock.assert_called_once_with(value)


def test_get_valid_checkbox_value__many_api_names__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.CHECKBOX,
        name='Checkbox field',
        template=template,
        api_name='api-name-1',
    )
    value_1 = 'first option'
    selection_template_1 = FieldTemplateSelection.objects.create(
        value=value_1,
        field_template=field_template,
        template=template,
    )
    value_2 = 'second option'
    selection_template_2 = FieldTemplateSelection.objects.create(
        value=value_2,
        field_template=field_template,
        template=template,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_template.api_name,
        is_required=field_template.is_required,
        type=field_template.type,
        workflow=workflow,
        account=user.account,
    )
    FieldSelection.objects.create(
        field=task_field,
        value=selection_template_1.value,
        api_name=selection_template_1.api_name,
    )
    FieldSelection.objects.create(
        field=task_field,
        value=selection_template_2.value,
        api_name=selection_template_2.api_name,
    )
    clear_value = 'clear value'
    clear_markdown_mock = mocker.patch(
        'src.processes.services.tasks.field.'
        'MarkdownService.clear',
        return_value=clear_value,
    )
    service = TaskFieldService(instance=task_field)
    raw_value = [selection_template_1.api_name, selection_template_2.api_name]
    value = f'{value_1}, {value_2}'

    # act
    field_data = service._get_valid_checkbox_value(
        raw_value=raw_value,
        selections=field_template.selections.all(),
    )

    # assert
    assert field_data.value == value
    assert field_data.markdown_value == value
    assert field_data.clear_value == clear_value
    clear_markdown_mock.assert_called_once_with(value)


def test_get_valid_file_value__one_file__ok():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
    )
    service = TaskFieldService(user=user)
    raw_value = [str(attachment.id)]

    # act
    field_data = service._get_valid_file_value(raw_value=raw_value)

    # assert
    assert field_data.value == attachment.url
    assert field_data.markdown_value == (
        f'[{attachment.name}]({attachment.url})'
    )
    assert field_data.clear_value == attachment.url


def test_get_valid_file_value__multiple_files__ok():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    attachment_1 = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
        output=field,
    )
    attachment_2 = FileAttachment.objects.create(
        name='The Rock',
        url='https://rock.com',
        size=1483,
        account_id=user.account_id,
    )
    service = TaskFieldService(user=user, instance=field)
    raw_value = [str(attachment_1.id), str(attachment_2.id)]

    # act
    field_data = service._get_valid_file_value(raw_value=raw_value)

    # assert
    assert field_data.value == f'{attachment_1.url}, {attachment_2.url}'
    assert field_data.markdown_value == (
        f'[{attachment_1.name}]({attachment_1.url}), '
        f'[{attachment_2.name}]({attachment_2.url})'
    )
    assert field_data.clear_value == f'{attachment_1.url}, {attachment_2.url}'


def test_get_valid_file_value__new_field__ok():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    event = WorkflowEvent.objects.create(
        account=user.account,
        type=WorkflowEventType.COMMENT,
        workflow=workflow,
        task=task,
        user=user,
    )
    FileAttachment.objects.create(
        name='The Rock',
        url='https://rock.com',
        size=1483,
        account_id=user.account_id,
        output=field,
    )
    FileAttachment.objects.create(
        name='The Rock',
        url='https://rock.com',
        size=1483,
        account_id=user.account_id,
        event=event,
    )
    new_attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
    )

    service = TaskFieldService(user=user)
    raw_value = [str(new_attachment.id)]

    # act
    field_data = service._get_valid_file_value(raw_value=raw_value)

    # assert
    assert field_data.value == new_attachment.url
    assert field_data.markdown_value == (
        f'[{new_attachment.name}]({new_attachment.url})'
    )
    assert field_data.clear_value == new_attachment.url


def test_get_valid_file_value__not_list__raise_exception():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    attachment = FileAttachment.objects.create(
        name='john.cena',
        url='https://john.cena/john.cena',
        size=1488,
        account_id=user.account_id,
    )
    another_user = create_test_owner(email='test@test.test')
    another_attachment = FileAttachment.objects.create(
        name='another',
        url='https://another',
        size=1652,
        account_id=another_user.account_id,
    )
    service = TaskFieldService(
        instance=task_field,
        user=user,
    )

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_file_value(
            raw_value=[attachment.id, another_attachment.id],
        )

    # assert
    assert ex.value.message == messages.MSG_PW_0037
    assert ex.value.api_name == task_field.api_name


@pytest.mark.parametrize('raw_value', ('abc', None, []))
def test_get_valid_file_value__invalid_attach_id__raise_exception(raw_value):

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_file_value(raw_value=[raw_value])

    # assert
    assert ex.value.message == messages.MSG_PW_0036
    assert ex.value.api_name == task_field.api_name


def test_get_valid_file_value__incorrect_attachments_count__raise_exception():

    # arrange
    user = create_test_owner()
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name='api-name-1',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)
    raw_value = None

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_file_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0036
    assert ex.value.api_name == task_field.api_name


def test_get_valid_user_value__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account)

    service = TaskFieldService(user=account_owner)
    raw_value = str(user.email)
    user_name = f'{user.first_name} {user.last_name}'

    # act
    field_data = service._get_valid_user_value(raw_value=raw_value)

    # assert
    assert field_data.value == user_name
    assert field_data.markdown_value == user_name
    assert field_data.clear_value == user_name
    assert field_data.user_id == user.id
    assert field_data.group_id is None


@pytest.mark.parametrize('raw_value', (None, 'a1', []))
def test_get_valid_user_value__invalid_value__raise_exception(raw_value):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=account_owner)
    task = workflow.tasks.get(number=1)
    field_api_name = 'api-name-1'
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.USER,
        workflow=workflow,
    )
    service = TaskFieldService(
        user=account_owner,
        instance=task_field,
    )

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_user_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0090
    assert ex.value.api_name == field_api_name


@pytest.mark.parametrize('raw_value', (176516132, 176516132.00))
def test_get_valid_date_value__valid_value__ok(raw_value):

    # arrange
    user = create_test_user()
    service = TaskFieldService(user=user)
    user_fmt_value = 'Aug 06, 1975, 12:15AM'

    # act
    field_data = service._get_valid_date_value(raw_value=raw_value)

    # assert
    assert field_data.value == str(raw_value)
    assert field_data.markdown_value == user_fmt_value
    assert field_data.clear_value == user_fmt_value


@pytest.mark.parametrize('raw_value', ('176516132', '176516132.00', ' '))
def test_get_valid_date_value__invalid_value__raise_exception(raw_value):
    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.DATE,
        name='Date field',
        template=template,
        api_name='api-name-1',
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_template.api_name,
        is_required=field_template.is_required,
        type=field_template.type,
        workflow=workflow,
        account=user.account,
    )
    service = TaskFieldService(instance=task_field)

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_date_value(raw_value=raw_value)

    # assert
    assert ex.value.api_name == task_field.api_name
    assert ex.value.message == messages.MSG_PW_0032


@pytest.mark.parametrize('raw_value', (5165, True))
def test_get_valid_url_value__not_string__raise_exception(raw_value):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.URL,
        name='URL field',
        template=template,
        api_name='api-name-1',
    )
    service = TaskFieldService(user=user, instance=field_template)

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_url_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0034
    assert ex.value.api_name == field_template.api_name


@pytest.mark.parametrize(
    'raw_value',
    ('ssh://my.pneumatic.app', 'relative/path'),
)
def test_get_valid_url_value__invalid_url__raise_exception(raw_value):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.URL,
        name='URL field',
        template=template,
        api_name='api-name-1',
    )
    service = TaskFieldService(user=user, instance=field_template)

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_url_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0035
    assert ex.value.api_name == field_template.api_name


@pytest.mark.parametrize(
    'raw_value',
    ('https://my.pneumatic.app', 'https://192.168.0.1'),
)
def test_get_valid_url_value__valid_value__ok(raw_value):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, tasks_count=1)
    template_task = template.tasks.first()
    field_template = FieldTemplate.objects.create(
        task=template_task,
        type=FieldType.URL,
        name='URL field',
        template=template,
        api_name='api-name-1',
    )
    service = TaskFieldService(user=user, instance=field_template)

    # act
    field_data = service._get_valid_url_value(raw_value=raw_value)

    # assert
    assert field_data.value == raw_value
    assert field_data.markdown_value == f'[URL field]({raw_value})'
    assert field_data.clear_value == raw_value


def test_get_valid_user_value__by_email__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account, email='test@example.com')

    service = TaskFieldService(user=account_owner)
    raw_value = 'test@example.com'
    user_name = f'{user.first_name} {user.last_name}'

    # act
    field_data = service._get_valid_user_value(raw_value=raw_value)

    # assert
    assert field_data.value == user_name
    assert field_data.markdown_value == user_name
    assert field_data.clear_value == user_name
    assert field_data.user_id == user.id
    assert field_data.group_id is None


def test_get_valid_user_value__by_email_case_insensitive__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account, email='test@example.com')

    service = TaskFieldService(user=account_owner)
    raw_value = 'TEST@EXAMPLE.COM'
    user_name = f'{user.first_name} {user.last_name}'

    # act
    field_data = service._get_valid_user_value(raw_value=raw_value)

    # assert
    assert field_data.value == user_name
    assert field_data.markdown_value == user_name
    assert field_data.clear_value == user_name
    assert field_data.user_id == user.id
    assert field_data.group_id is None


def test_get_valid_user_value__by_group_name__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    group = create_test_group(account=account, name='Test Group')

    service = TaskFieldService(user=account_owner)
    raw_value = 'Test Group'

    # act
    field_data = service._get_valid_user_value(raw_value=raw_value)

    # assert
    assert field_data.value == group.name
    assert field_data.markdown_value == group.name
    assert field_data.clear_value == group.name
    assert field_data.user_id is None
    assert field_data.group_id == group.id


def test_get_valid_user_value__by_group_name_case_insensitive__ok():

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    group = create_test_group(account=account, name='Test Group')
    workflow = create_test_workflow(user=account_owner)
    task = workflow.tasks.get(number=1)
    field_api_name = 'api-name-1'
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.USER,
        workflow=workflow,
        account=account_owner.account,
    )

    service = TaskFieldService(
        user=account_owner,
        instance=task_field,
    )
    raw_value = 'TEST GROUP'

    # act
    field_data = service._get_valid_user_value(raw_value=raw_value)

    # assert
    assert field_data.value == group.name
    assert field_data.markdown_value == group.name
    assert field_data.clear_value == group.name
    assert field_data.user_id is None
    assert field_data.group_id == group.id


def test_get_valid_user_value__email_vs_group_name__prefer_email():
    """
    The test checks that if the value is suitable as an email,
    then we first look for a user, and not a group
    """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    user = create_test_admin(account=account, email='test@example.com')
    create_test_group(account=account, name='test@example.com')
    workflow = create_test_workflow(user=account_owner)
    task = workflow.tasks.get(number=1)
    field_api_name = 'api-name-1'
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.USER,
        workflow=workflow,
        account=account_owner.account,
    )

    service = TaskFieldService(
        user=account_owner,
        instance=task_field,
    )
    raw_value = 'test@example.com'
    user_name = f'{user.first_name} {user.last_name}'

    # act
    field_data = service._get_valid_user_value(raw_value=raw_value)

    # assert
    assert field_data.value == user_name
    assert field_data.markdown_value == user_name
    assert field_data.clear_value == user_name
    assert field_data.user_id == user.id
    assert field_data.group_id is None


@pytest.mark.parametrize(
    'raw_value',
    (
        'nonexistent@email.com',
        'invalid-email',
        '',
        '   ',
    ),
)
def test_get_valid_user_value__invalid_string__raise_exception(raw_value):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    workflow = create_test_workflow(user=account_owner)
    task = workflow.tasks.get(number=1)
    field_api_name = 'api-name-1'
    task_field = TaskField.objects.create(
        task=task,
        api_name=field_api_name,
        type=FieldType.USER,
        workflow=workflow,
    )
    service = TaskFieldService(
        user=account_owner,
        instance=task_field,
    )

    # act
    with pytest.raises(TaskFieldException) as ex:
        service._get_valid_user_value(raw_value=raw_value)

    # assert
    assert ex.value.message == messages.MSG_PW_0090
    assert ex.value.api_name == field_api_name
