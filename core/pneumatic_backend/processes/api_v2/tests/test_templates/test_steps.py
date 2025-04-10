import pytest

from pneumatic_backend.authentication.services import GuestJWTAuthService
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template,
    create_test_workflow,
    create_test_account,
    create_test_group,
    create_test_guest,
    create_test_owner,
    create_test_admin,
    create_test_not_admin,
    create_invited_user,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    TemplateType,
    OwnerType, PerformerType, TaskStatus
)
from pneumatic_backend.processes.models import (
    TemplateOwner,
    TaskPerformer,
)


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'template_type', (TemplateType.CUSTOM, TemplateType.LIBRARY)
)
def test_steps__all_template_tasks__ok(template_type, api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=2,
        type_=template_type,
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert len(response.data) == 2


def test_steps__template_draft__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=False,
        tasks_count=2,
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert len(response.data) == 2


def test_steps__admin__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    template_task = template.tasks.get(number=1)
    request_user = create_test_admin(account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=request_user.id,
        type=OwnerType.USER
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task.id
    assert response.data[0]['api_name'] == template_task.api_name


def test_steps__not_admin__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    template_task = template.tasks.get(number=1)
    request_user = create_test_not_admin(account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=request_user.id,
        type=OwnerType.USER
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task.id
    assert response.data[0]['api_name'] == template_task.api_name


def test_steps__group_is_template_owner__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    template_task = template.tasks.get()
    request_user = create_test_admin(account=account)
    group = create_test_group(user=account_owner, users=[request_user])
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['number'] == template_task.number
    assert response.data[0]['id'] == template_task.id
    assert response.data[0]['api_name'] == template_task.api_name


def test_steps__deleted_template__empty_result(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=False,
        tasks_count=1,
    )
    template.delete()
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__user_not_template_owner__empty_result(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    request_user = create_test_not_admin(account=account)

    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__invited_user__unauthorized(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    request_user = create_invited_user(user=account_owner)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=request_user.id,
        type=OwnerType.USER
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 401


def test_steps__deleted_user__unauthorized(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    request_user = create_test_admin(account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=request_user.id,
        type=OwnerType.USER
    )
    request_user.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 401


def test_steps__user_from_another_acc__empty_result(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    another_account_user = create_test_owner(email='another@pneumatic.app')
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=another_account_user.id,
        type=OwnerType.USER
    )
    api_client.token_authenticate(another_account_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__guest_performer__permission_denied(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.current_task_instance
    guest = create_test_guest(account=account)
    TaskPerformer.objects.create(
        task_id=task.id,
        user_id=guest.id,
    )
    str_token = GuestJWTAuthService.get_str_token(
        task_id=task.id,
        user_id=guest.id,
        account_id=account.id
    )
    # act
    response = api_client.get(
        f'/templates/{template.id}/steps',
        **{'X-Guest-Authorization': str_token}
    )

    # assert
    assert response.status_code == 403


@pytest.mark.parametrize('template_type', TemplateType.TYPES_ONBOARDING)
def test_steps__onboarding_template__empty_result(
    api_client,
    template_type
):

    # arrange
    owner = create_test_owner()
    template = create_test_template(
        owner,
        type_=template_type,
        is_active=True,
        tasks_count=1
    )
    api_client.token_authenticate(owner)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_user_from_another_acc__empty_result(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    another_account_user = create_test_owner(email='another@pneumatic.app')
    workflow = create_test_workflow(
        user=account_owner,
        template=template
    )
    task = workflow.tasks.get()
    TaskPerformer.objects.create(
        task=task,
        user=another_account_user,
        is_completed=True
    )
    api_client.token_authenticate(another_account_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_true_deleted_workflow__empty_result(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
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
        is_completed=False
    )
    workflow.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.parametrize(
    'status', (WorkflowStatus.DONE, WorkflowStatus.DELAYED)
)
def test_steps__with_tasks_in_progress_true_inactive_workflow__empty_result(
    status,
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template
    )
    task = workflow.tasks.get()
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
        is_completed=False
    )
    workflow.status = status
    workflow.save(update_fields=['status'])
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_true__another_task_completed__ok(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=2
    )
    template_task_2 = template.tasks.get(number=2)
    workflow = create_test_workflow(
        user=account_owner,
        template=template
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
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['number'] == template_task_2.number
    assert response.data[0]['id'] == template_task_2.id
    assert response.data[0]['api_name'] == template_task_2.api_name


def test_steps__with_tasks_in_progress_true__not_template_owner__ok(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    template_task = template.tasks.get()
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.current_task_instance
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template_task.id
    assert response.data[0]['number'] == template_task.number
    assert response.data[0]['api_name'] == template_task.api_name


def test_steps__with_tasks_in_progress_true__performer_group__ok(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    template_task_1 = template.tasks.get(number=1)
    workflow = create_test_workflow(
        user=account_owner,
        template=template
    )
    request_user = create_test_admin(account=account)
    group = create_test_group(user=account_owner, users=[request_user])
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task_1.id
    assert response.data[0]['api_name'] == template_task_1.api_name


def test_steps__with_tasks_in_progress_true__deleted_group__empty_list(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template
    )
    request_user = create_test_admin(account=account)
    group = create_test_group(user=account_owner, users=[request_user])
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )
    group.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.parametrize('status', WorkflowStatus.ALL_STATUSES)
def test_steps__with_tasks_in_progress_false__not_completed_task__not_found(
    status,
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template
    )
    workflow.status = status
    workflow.save(update_fields=['status'])
    task = workflow.tasks.get()
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
        is_completed=False
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.parametrize('status', WorkflowStatus.ALL_STATUSES)
def test_steps__with_tasks_in_progress_false__completed_task__ok(
    status,
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    template_task = template.tasks.get()
    workflow = create_test_workflow(
        user=account_owner,
        template=template
    )
    workflow.status = status
    workflow.save(update_fields=['status'])
    task = workflow.tasks.get()
    request_user = create_test_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
        is_completed=True
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )
    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['number'] == template_task.number
    assert response.data[0]['id'] == template_task.id
    assert response.data[0]['api_name'] == template_task.api_name


def test_steps__with_tasks_in_progress_false_deleted_workflow__empty_result(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
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
        is_completed=True
    )
    workflow.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_false__performer_group__ok(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    template_task_1 = template.tasks.get(number=1)
    workflow = create_test_workflow(
        user=account_owner,
        template=template
    )
    request_user = create_test_admin(account=account)
    group = create_test_group(user=account_owner, users=[request_user])
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        is_completed=True,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task_1.id
    assert response.data[0]['api_name'] == template_task_1.api_name


def test_steps__with_tasks_in_progress_false__deleted_group__empty_list(
    api_client
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template
    )
    request_user = create_test_admin(account=account)
    group = create_test_group(user=account_owner, users=[request_user])
    task = workflow.current_task_instance
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
        is_completed=True
    )
    group.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__over_limited_template_id__not_found(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/12345678901/steps')

    # assert
    assert response.status_code == 404
