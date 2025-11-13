import pytest

from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import (
    PerformerType,
    TaskStatus,
    WorkflowStatus, OwnerType, TemplateType,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_group,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow, create_invited_user, create_test_guest,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_titles__default_status_active__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    request_user = create_test_admin(account=account)
    template = create_test_template(
        user=request_user,
        name='a template',
        is_active=True,
        tasks_count=2,
    )
    create_test_workflow(
        user=request_user,
        template=template,
        active_task_number=2,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 1


def test_titles__one_template_and_two_tasks__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    request_user = create_test_admin(account=account)
    template = create_test_template(
        user=request_user,
        name='a template',
        is_active=True,
        tasks_count=2,
    )
    create_test_workflow(
        user=request_user,
        template=template,
        active_task_number=1,
    )
    create_test_workflow(
        user=request_user,
        template=template,
        active_task_number=2,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 2


def test_titles__one_template_and_two_parallel_tasks__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    request_user = create_test_admin(account=account)
    template = create_test_template(
        user=request_user,
        name='a template',
        is_active=True,
        tasks_count=2,
    )
    workflow = create_test_workflow(
        user=request_user,
        template=template,
    )
    task_2 = workflow.tasks.get(number=2)
    task_2.status = TaskStatus.ACTIVE
    task_2.save()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 2


def test_titles__user_from_another_account__empty_result(api_client):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    another_account_user = create_test_owner(email='another@pneumatic.app')
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get()
    TaskPerformer.objects.create(
        task=task,
        user=another_account_user,
        is_completed=True,
    )
    api_client.token_authenticate(another_account_user)

    # act
    response = api_client.get(
       f'/templates/titles-by-tasks?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__template_without_workflows__empty_list(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    request_user = create_test_admin(account=account)
    create_test_template(
        user=request_user,
        name='template',
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__draft_template__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=False,
        tasks_count=1,
    )
    create_test_workflow(user=account_owner, template=template)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 1


def test_titles__status_active__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    request_user = create_test_not_admin(account=account)
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=request_user.id,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 1


def test_titles__default_ordering_by_most_popular__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template_1 = create_test_template(user=account_owner, is_active=True)
    create_test_workflow(user=account_owner, template=template_1)
    template_2 = create_test_template(user=account_owner, is_active=True)
    create_test_workflow(user=account_owner, template=template_2)
    create_test_workflow(user=account_owner, template=template_2)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template_2.id
    assert response.data[1]['id'] == template_1.id


def test_titles__admin__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=False,
        tasks_count=1,
    )
    create_test_workflow(user=account_owner, template=template)
    request_user = create_test_admin(account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=request_user.id,
        type=OwnerType.USER,
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_titles__not_admin__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=False,
        tasks_count=1,
    )
    create_test_workflow(user=account_owner, template=template)
    request_user = create_test_not_admin(account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=request_user.id,
        type=OwnerType.USER,
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_titles__deleted_template__skip(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=False,
        tasks_count=1,
    )
    create_test_workflow(user=account_owner, template=template)
    template.delete()
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__deleted_workflow__skip(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=False,
        tasks_count=1,
    )
    workflow = create_test_workflow(user=account_owner, template=template)
    workflow.delete()
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__user_not_template_owner__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    request_user = create_test_not_admin(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=request_user.id,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_titles__invited_user__unauthorized(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    request_user = create_invited_user(user=account_owner)
    TaskPerformer.objects.create(
        task=task,
        user_id=request_user.id,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 401


def test_titles__deleted_user__unauthorized(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    request_user = create_invited_user(user=account_owner)
    TaskPerformer.objects.create(
        task=task,
        user_id=request_user.id,
    )
    request_user.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 401


def test_titles__user_from_another_acc__empty_result(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(user=account_owner, template=template)
    task = workflow.tasks.get(number=1)
    another_account_user = create_test_owner(email='another@pneumatic.app')
    TaskPerformer.objects.create(
        task=task,
        user_id=another_account_user.id,
    )
    api_client.token_authenticate(another_account_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__guest_performer__permission_denied(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id,
    )

    # act
    response = api_client.get(
        '/templates/titles-by-tasks',
        **{'X-Guest-Authorization': str_token},
    )

    # assert
    assert response.status_code == 403


@pytest.mark.parametrize('template_type', TemplateType.TYPES_ONBOARDING)
def test_titles__onboarding_template__empty_result(
    api_client,
    template_type,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        account_owner,
        type_=template_type,
        is_active=True,
        tasks_count=1,
    )
    create_test_workflow(
        user=account_owner,
        template=template,
        tasks_count=1,
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_active_and_performer_group__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    request_user = create_test_admin(account=account)
    group = create_test_group(account, users=[request_user])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 1


def test_titles__not_active_tasks__empty_list(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    request_user = create_test_admin(account=account)
    template = create_test_template(
        user=request_user,
        name='a template',
        is_active=True,
        tasks_count=2,
    )
    workflow = create_test_workflow(
        user=request_user,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    task.status = TaskStatus.PENDING
    task.save()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-tasks')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.parametrize(
    'status', (WorkflowStatus.DONE, WorkflowStatus.DELAYED),
)
def test_titles__status_active_and_inactive_workflow__empty_result(
    status,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    create_test_workflow(
        user=account_owner,
        template=template,
        status=status,
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_active_and_another_task_completed__ok(
    api_client,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=2,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    workflow.save()
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.COMPLETED
    task_1.save()
    task_2 = workflow.tasks.get(number=2)
    task_2.status = TaskStatus.ACTIVE
    task_2.save()

    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__status_active_and_deleted_workflow__empty_result(
    api_client,
):
    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get()
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
        is_completed=False,
    )
    workflow.delete()
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_active_and_not_template_owner__ok(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_titles__status_active_and_deleted_group__empty_list(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    request_user = create_test_admin(account=account)
    group = create_test_group(account, users=[request_user])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    group.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.ACTIVE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_completed_and_performer_group__ok(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    request_user = create_test_admin(account=account)
    group = create_test_group(account, users=[request_user])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        is_completed=True,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.COMPLETED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.parametrize('status', WorkflowStatus.ALL_STATUSES)
def test_titles__status_completed_and_completed_task__ok(
    status,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    workflow.status = status
    workflow.save(update_fields=['status'])
    task = workflow.tasks.get()
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
        is_completed=True,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.COMPLETED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


@pytest.mark.parametrize('status', WorkflowStatus.ALL_STATUSES)
def test_titles__status_completed_and_not_completed_task__not_found(
    status,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    workflow.status = status
    workflow.save(update_fields=['status'])
    task = workflow.tasks.get()
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
        is_completed=False,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.COMPLETED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_completed_and_another_user__empty_result(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=2,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    workflow.save()
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.COMPLETED
    task_1.save()
    task_2 = workflow.tasks.get(number=2)
    task_2.status = TaskStatus.ACTIVE
    task_2.save()

    request_user = create_test_admin(account=account)
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.COMPLETED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_completed_and_deleted_workflow__empty_result(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get()
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
        is_completed=True,
    )
    workflow.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
       f'/templates/titles-by-tasks?status={TaskStatus.COMPLETED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_completed_and_deleted_group__empty_list(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    request_user = create_test_admin(account=account)
    group = create_test_group(account, users=[request_user])
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        is_completed=True,
    )
    group.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.COMPLETED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_delayed__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    request_user = create_test_not_admin(account=account)
    template = create_test_template(
        user=request_user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=request_user,
        template=template,
    )
    task_1 = workflow.tasks.get(number=1)
    task_1.status = TaskStatus.DELAYED
    task_1.save()

    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-tasks?status={TaskStatus.DELAYED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 1


def test_titles__status_invalid_value__validation_error(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-tasks?status=undefined')

    # assert
    assert response.status_code == 400
    message = '"undefined" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'status'
