import pytest

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


def test_mark__selection_marked__return_true(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
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
        return_value=True,
    )
    service = ChecklistService(instance=checklist, user=owner)

    # act
    result = service.mark(selection_id=selection.id)

    # assert
    assert result is True
    checklist_selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=owner,
    )
    selection_mark_mock.assert_called_once_with()


def test_mark__selection_not_marked__return_false(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
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
        return_value=False,
    )
    service = ChecklistService(instance=checklist, user=owner)

    # act
    result = service.mark(selection_id=selection.id)

    # assert
    assert result is False
    checklist_selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=owner,
    )
    selection_mark_mock.assert_called_once_with()


def test_unmark__selection_unmarked__return_true(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
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
        return_value=True,
    )
    service = ChecklistService(instance=checklist, user=owner)

    # act
    result = service.unmark(selection_id=selection.id)

    # assert
    assert result is True
    checklist_selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=owner,
    )
    selection_unmark_mock.assert_called_once_with()


def test_unmark__selection_not_unmarked__return_false(mocker):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
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
        return_value=False,
    )
    service = ChecklistService(instance=checklist, user=owner)

    # act
    result = service.unmark(selection_id=selection.id)

    # assert
    assert result is False
    checklist_selection_service_init_mock.assert_called_once_with(
        instance=selection,
        user=owner,
    )
    selection_unmark_mock.assert_called_once_with()
