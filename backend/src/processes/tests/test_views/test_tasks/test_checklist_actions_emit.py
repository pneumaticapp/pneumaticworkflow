import pytest

from src.authentication.services.guest_auth import GuestJWTAuthService
from src.logs.events.enums import (
    ActorType,
    EventCategory,
    EventName,
    EventObjectType,
)
from src.logs.events.schema import Actor, EventObject
from src.processes.models.workflows.checklist import ChecklistSelection
from src.processes.services.tasks.exceptions import (
    ChecklistServiceException,
)
from src.processes.tests.fixtures import (
    create_checklist_template,
    create_test_account,
    create_test_guest,
    create_test_owner,
    create_test_performer,
    create_test_template,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_mark__performer__emit_checklist_mark(
    mocker,
    api_client,
    fake_stream,
):

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
    task = workflow.tasks.get(number=1)
    checklist = task.checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    mark_mock = mocker.patch(
        'src.processes.views.checklist.ChecklistService.mark',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path=f'/v2/tasks/checklists/{checklist.id}/mark',
        data={'selection_id': selection.id},
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TASK_CHECKLIST_MARK
    assert event.category == EventCategory.ACTIVITY
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.CHECKLIST,
        id=checklist.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'checklist_api_name': 'checklist',
        'selection_id': selection.id,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id
    mark_mock.assert_called_once_with(selection_id=selection.id)


def test_mark__guest__emit_guest_actor(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    create_test_performer(task=task, user=guest)
    checklist = task.checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    mark_mock = mocker.patch(
        'src.processes.views.checklist.ChecklistService.mark',
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )

    # act
    response = api_client.post(
        path=f'/v2/tasks/checklists/{checklist.id}/mark',
        data={'selection_id': selection.id},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TASK_CHECKLIST_MARK
    assert event.category == EventCategory.ACTIVITY
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.GUEST,
        id=guest.id,
        email=guest.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.CHECKLIST,
        id=checklist.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'checklist_api_name': 'checklist',
        'selection_id': selection.id,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id
    mark_mock.assert_called_once_with(selection_id=selection.id)


def test_mark__selection_id_is_null__no_event(
    mocker,
    api_client,
    fake_stream,
):

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
    task = workflow.tasks.get(number=1)
    checklist = task.checklists.get()
    mark_mock = mocker.patch(
        'src.processes.views.checklist.ChecklistService.mark',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path=f'/v2/tasks/checklists/{checklist.id}/mark',
        data={'selection_id': None},
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'selection_id'
    assert fake_stream.events == []
    mark_mock.assert_not_called()


def test_mark__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

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
    task = workflow.tasks.get(number=1)
    checklist = task.checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    message = 'some message'
    mark_mock = mocker.patch(
        'src.processes.views.checklist.ChecklistService.mark',
        side_effect=ChecklistServiceException(message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path=f'/v2/tasks/checklists/{checklist.id}/mark',
        data={'selection_id': selection.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    mark_mock.assert_called_once_with(selection_id=selection.id)


def test_unmark__performer__emit_checklist_unmark(
    mocker,
    api_client,
    fake_stream,
):

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
    task = workflow.tasks.get(number=1)
    checklist = task.checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    unmark_mock = mocker.patch(
        'src.processes.views.checklist.ChecklistService.unmark',
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path=f'/v2/tasks/checklists/{checklist.id}/unmark',
        data={'selection_id': selection.id},
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TASK_CHECKLIST_UNMARK
    assert event.category == EventCategory.ACTIVITY
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.USER,
        id=owner.id,
        email=owner.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.CHECKLIST,
        id=checklist.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'checklist_api_name': 'checklist',
        'selection_id': selection.id,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id
    unmark_mock.assert_called_once_with(selection_id=selection.id)


def test_unmark__guest__emit_guest_actor(
    mocker,
    api_client,
    fake_stream,
):

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    guest = create_test_guest(account=account)
    template = create_test_template(
        user=owner,
        is_active=True,
        tasks_count=1,
    )
    create_checklist_template(task_template=template.tasks.get(number=1))
    workflow = create_test_workflow(user=owner, template=template)
    task = workflow.tasks.get(number=1)
    create_test_performer(task=task, user=guest)
    checklist = task.checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    unmark_mock = mocker.patch(
        'src.processes.views.checklist.ChecklistService.unmark',
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )

    # act
    response = api_client.post(
        path=f'/v2/tasks/checklists/{checklist.id}/unmark',
        data={'selection_id': selection.id},
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 200
    assert len(fake_stream.events) == 1
    event = fake_stream.last_event()
    assert event.type == EventName.TASK_CHECKLIST_UNMARK
    assert event.category == EventCategory.ACTIVITY
    assert event.account_id == account.id
    assert event.actor == Actor(
        type=ActorType.GUEST,
        id=guest.id,
        email=guest.email,
    )
    assert event.object == EventObject(
        type=EventObjectType.CHECKLIST,
        id=checklist.id,
    )
    assert event.payload == {
        'workflow_name': workflow.name,
        'task_name': task.name,
        'checklist_api_name': 'checklist',
        'selection_id': selection.id,
    }
    assert event.workflow_id == workflow.id
    assert event.task_id == task.id
    unmark_mock.assert_called_once_with(selection_id=selection.id)


def test_unmark__service_exception__no_event(
    mocker,
    api_client,
    fake_stream,
):

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
    task = workflow.tasks.get(number=1)
    checklist = task.checklists.get()
    selection = ChecklistSelection.objects.get(
        checklist=checklist,
        api_name='cl-selection-1',
    )
    message = 'some message'
    unmark_mock = mocker.patch(
        'src.processes.views.checklist.ChecklistService.unmark',
        side_effect=ChecklistServiceException(message),
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.post(
        path=f'/v2/tasks/checklists/{checklist.id}/unmark',
        data={'selection_id': selection.id},
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details'] == {}
    assert fake_stream.events == []
    unmark_mock.assert_called_once_with(selection_id=selection.id)
