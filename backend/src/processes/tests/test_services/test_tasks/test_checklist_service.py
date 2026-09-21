import pytest
from django.utils import timezone

from src.processes.models.workflows.checklist import ChecklistSelection
from src.processes.services.tasks.checklist import ChecklistService
from src.processes.services.tasks.checklist_selection import (
    ChecklistSelectionService,
)
from src.processes.tests.fixtures import (
    create_checklist_template,
    create_test_account,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_mark__not_marked__emit_checklist_item_marked(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    checklist = workflow.tasks.get(number=1).checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    checklist_selection_service_init_mock = mocker.patch.object(
        ChecklistSelectionService,
        attribute='__init__',
        return_value=None,
    )
    selection_mark_mock = mocker.patch(
        'src.processes.services.tasks.checklist.'
        'ChecklistSelectionService.mark',
    )
    checklist_item_marked_mock = mocker.patch(
        'src.processes.services.tasks.checklist.'
        'AuditEventService.checklist_item_marked',
    )
    service = ChecklistService(
        instance=checklist,
        user=owner,
    )

    # act
    service.mark(selection_id=selection.id)

    # assert
    checklist_selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=owner,
    )
    selection_mark_mock.assert_called_once_with()
    checklist_item_marked_mock.assert_called_once_with(
        user=owner,
        auth_type=service.auth_type,
        checklist=checklist,
        selection_id=selection.id,
    )


def test_mark__already_marked__not_emit(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    checklist = workflow.tasks.get(number=1).checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    selection.date_selected = timezone.now()
    selection.save()
    checklist_selection_service_init_mock = mocker.patch.object(
        ChecklistSelectionService,
        attribute='__init__',
        return_value=None,
    )
    selection_mark_mock = mocker.patch(
        'src.processes.services.tasks.checklist.'
        'ChecklistSelectionService.mark',
    )
    checklist_item_marked_mock = mocker.patch(
        'src.processes.services.tasks.checklist.'
        'AuditEventService.checklist_item_marked',
    )
    service = ChecklistService(
        instance=checklist,
        user=owner,
    )

    # act
    service.mark(selection_id=selection.id)

    # assert
    checklist_selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=owner,
    )
    selection_mark_mock.assert_called_once_with()
    checklist_item_marked_mock.assert_not_called()


def test_unmark__marked__emit_checklist_item_unmarked(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    checklist = workflow.tasks.get(number=1).checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    selection.date_selected = timezone.now()
    selection.save()
    checklist_selection_service_init_mock = mocker.patch.object(
        ChecklistSelectionService,
        attribute='__init__',
        return_value=None,
    )
    selection_unmark_mock = mocker.patch(
        'src.processes.services.tasks.checklist.'
        'ChecklistSelectionService.unmark',
    )
    checklist_item_unmarked_mock = mocker.patch(
        'src.processes.services.tasks.checklist.'
        'AuditEventService.checklist_item_unmarked',
    )
    service = ChecklistService(
        instance=checklist,
        user=owner,
    )

    # act
    service.unmark(selection_id=selection.id)

    # assert
    checklist_selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=owner,
    )
    selection_unmark_mock.assert_called_once_with()
    checklist_item_unmarked_mock.assert_called_once_with(
        user=owner,
        auth_type=service.auth_type,
        checklist=checklist,
        selection_id=selection.id,
    )


def test_unmark__not_marked__not_emit(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(
        user=owner,
        template=template,
    )
    checklist = workflow.tasks.get(number=1).checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    checklist_selection_service_init_mock = mocker.patch.object(
        ChecklistSelectionService,
        attribute='__init__',
        return_value=None,
    )
    selection_unmark_mock = mocker.patch(
        'src.processes.services.tasks.checklist.'
        'ChecklistSelectionService.unmark',
    )
    checklist_item_unmarked_mock = mocker.patch(
        'src.processes.services.tasks.checklist.'
        'AuditEventService.checklist_item_unmarked',
    )
    service = ChecklistService(
        instance=checklist,
        user=owner,
    )

    # act
    service.unmark(selection_id=selection.id)

    # assert
    checklist_selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=owner,
    )
    selection_unmark_mock.assert_called_once_with()
    checklist_item_unmarked_mock.assert_not_called()
