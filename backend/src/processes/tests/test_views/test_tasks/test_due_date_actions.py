import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from src.utils.validation import ErrorCode
from src.generics.messages import MSG_GE_0007
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
    create_test_group
)
from src.processes.services.tasks.task import TaskService
from src.processes.services.tasks.exceptions import (
    TaskServiceException
)
from src.processes.enums import (
    PerformerType,
    DirectlyStatus,
    OwnerType
)
from src.processes.models import (
    TaskPerformer,
    TemplateOwner
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_create__ok(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() + timedelta(days=1)
    due_date_tsp = due_date.timestamp()

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={
            'due_date_tsp': due_date_tsp
        }
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(user=user, instance=task)
    set_due_date_mock.assert_called_once_with(value=due_date)


def test_create__user_in_group__ok(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    performer = create_test_user(
        account=user.account,
        email='test@test.test',
        is_account_owner=False
    )
    group = create_test_group(user.account, users=[performer])
    workflow = create_test_workflow(user)
    workflow.owners.add(performer)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED
    )
    api_client.token_authenticate(performer)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() + timedelta(days=1)
    due_date_tsp = due_date.timestamp()

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={
            'due_date_tsp': due_date_tsp
        }
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(user=performer, instance=task)
    set_due_date_mock.assert_called_once_with(value=due_date)


def test_delete__ok(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )

    # act
    response = api_client.delete(
        f'/v2/tasks/{task.id}/due-date'
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(user=user, instance=task)
    set_due_date_mock.assert_called_once_with(value=None)


def test_delete__user_in_group__ok(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    performer = create_test_user(
        account=user.account,
        email='test@test.test',
        is_account_owner=False
    )
    group = create_test_group(user.account, users=[performer])
    workflow = create_test_workflow(user)
    workflow.owners.add(performer)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        directly_status=DirectlyStatus.CREATED
    )
    api_client.token_authenticate(performer)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )

    # act
    response = api_client.delete(
        f'/v2/tasks/{task.id}/due-date'
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(user=performer, instance=task)
    set_due_date_mock.assert_called_once_with(value=None)


def test_create__workflow_starter_in_legacy_workflow__ok(
    mocker,
    api_client
):

    # arrange
    user = create_test_user(
        is_account_owner=False,
        is_admin=True,
    )
    template = create_test_template(user=user, tasks_count=1, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    workflow.legacy_template_name = template.name
    workflow.is_legacy_template = True
    workflow.save(
        update_fields=['legacy_template_name', 'is_legacy_template']
    )
    template.delete()

    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': due_date.timestamp()}
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(user=user, instance=task)
    set_due_date_mock.assert_called_once_with(value=due_date)


def test_create__request_user_is_not_account_user__not_found(
    mocker,
    api_client
):

    # arrange
    another_account_user = create_test_user(email='user2@test.test')
    api_client.token_authenticate(another_account_user)
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': due_date.timestamp()}
    )

    # assert
    assert response.status_code == 404
    service_init_mock.assert_not_called()
    set_due_date_mock.assert_not_called()


def test_create__request_user_is_not_authenticated__permission_denied(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': due_date.timestamp()}
    )

    # assert
    assert response.status_code == 401
    service_init_mock.assert_not_called()
    set_due_date_mock.assert_not_called()


def test_create__request_user_is_not_admin__permission_denied(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    not_admin = create_test_user(
        account=user.account,
        is_account_owner=False,
        is_admin=False,
        email='test@test.test'
    )
    template = create_test_template(user)
    TemplateOwner.objects.create(
        template=template,
        account=user.account,
        type=OwnerType.USER,
        user_id=not_admin.id,
    )
    workflow = create_test_workflow(
        template=template,
        user=user,
        tasks_count=1
    )
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(not_admin)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': due_date.timestamp()}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    set_due_date_mock.assert_not_called()


def test_create__request_user_is_not_template_owner__permission_denied(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    create_test_template(user)
    create_test_template(user)
    template = create_test_template(user)
    workflow = create_test_workflow(
        template=template,
        user=user,
        tasks_count=1
    )
    task = workflow.tasks.get(number=1)
    admin = create_test_user(
        account=user.account,
        is_account_owner=False,
        is_admin=True,
        email='test@test.test'
    )
    api_client.token_authenticate(admin)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': due_date.timestamp()}
    )

    # assert
    assert response.status_code == 403
    service_init_mock.assert_not_called()
    set_due_date_mock.assert_not_called()


def test_create__not_exist_task_id__not_found(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() + timedelta(days=1)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        f'/v2/tasks/{999999999}/due-date',
        data={'due_date_tsp': due_date.timestamp()}
    )

    # assert
    assert response.status_code == 404
    service_init_mock.assert_not_called()
    set_due_date_mock.assert_not_called()


def test_create__due_date_is_null__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': None}
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be null.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'due_date_tsp'
    service_init_mock.assert_not_called()
    set_due_date_mock.assert_not_called()


def test_create__due_date_tsp_is_blank__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': ''}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_GE_0007
    assert response.data['details']['reason'] == MSG_GE_0007
    assert response.data['details']['name'] == 'due_date_tsp'
    service_init_mock.assert_not_called()
    set_due_date_mock.assert_not_called()


@pytest.mark.parametrize('value', ([], 'undefined', '01/02/2023'))
def test_create__invalid_value__validation_error(
    value,
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': value}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_GE_0007
    assert response.data['details']['reason'] == MSG_GE_0007
    assert response.data['details']['name'] == 'due_date_tsp'
    service_init_mock.assert_not_called()
    set_due_date_mock.assert_not_called()


def test_create__due_date_less_then_current__ok(
    mocker,
    api_client
):
    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly'
    )
    due_date = timezone.now() - timedelta(hours=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': due_date.timestamp()}
    )

    # assert
    assert response.status_code == 204
    service_init_mock.assert_called_once_with(
        user=user,
        instance=task
    )
    set_due_date_mock.assert_called_once_with(value=due_date)


def test_create__service_exception__validation_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    workflow = create_test_workflow(user)
    task = workflow.tasks.get(number=1)
    api_client.token_authenticate(user)
    error_message = 'error message'
    service_init_mock = mocker.patch.object(
        TaskService,
        attribute='__init__',
        return_value=None
    )
    set_due_date_mock = mocker.patch(
        'src.processes.services.tasks.task.'
        'TaskService.set_due_date_directly',
        side_effect=TaskServiceException(message=error_message)

    )
    due_date = timezone.now() + timedelta(days=1)

    # act
    response = api_client.post(
        f'/v2/tasks/{task.id}/due-date',
        data={'due_date_tsp': due_date.timestamp()}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == error_message
    service_init_mock.assert_called_once_with(user=user, instance=task)
    set_due_date_mock.assert_called_once_with(value=due_date)
