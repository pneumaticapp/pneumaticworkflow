import pytest

from src.authentication.services.guest_auth import GuestJWTAuthService
from src.processes.enums import (
    OwnerType,
    TemplateType,
    WorkflowApiStatus,
    WorkflowStatus,
)
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.workflows.task import TaskPerformer
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_admin,
    create_test_guest,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


def test_titles__many_templates__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template_1 = create_test_template(
        user=account_owner,
        name='a template',
        is_active=True,
        tasks_count=1,
    )
    create_test_workflow(
        user=account_owner,
        template=template_1,
    )
    template_2 = create_test_template(
        user=account_owner,
        name='b template',
        is_active=True,
        tasks_count=1,
    )
    create_test_workflow(
        user=account_owner,
        template=template_2,
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_1.id
    assert response.data[0]['name'] == template_1.name
    assert response.data[0]['count'] == 1
    assert response.data[1]['id'] == template_2.id
    assert response.data[1]['name'] == template_2.name
    assert response.data[1]['count'] == 1


def test_titles__template_without_workflows__ok(api_client):

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    request_user = create_test_admin(account=account)
    template = create_test_template(
        user=request_user,
        name='template',
        is_active=True,
        tasks_count=1,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 0


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
    response = api_client.get('/templates/titles-by-workflows')

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
    response = api_client.get('/templates/titles-by-workflows')

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
    response = api_client.get('/templates/titles-by-workflows')

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
    response = api_client.get('/templates/titles-by-workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1


def test_titles__not_workflows__ok(api_client):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(user=account_owner, is_active=True)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get('/templates/titles-by-workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 0


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
    response = api_client.get('/templates/titles-by-workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__deleted_workflow__ok(api_client):

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
    response = api_client.get('/templates/titles-by-workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 0


def test_titles__user_not_template_owner__empty_result__ok(api_client):

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
    )
    request_user = create_test_not_admin(account=account)
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-workflows')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__invited_user__unauthorized(api_client):

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
    )
    request_user = create_invited_user(user=account_owner)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=request_user.id,
        type=OwnerType.USER,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-workflows')

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
    create_test_workflow(
        user=account_owner,
        template=template,
    )
    request_user = create_test_admin(account=account)
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=request_user.id,
        type=OwnerType.USER,
    )
    request_user.delete()
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get('/templates/titles-by-workflows')

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
    create_test_workflow(user=account_owner, template=template)
    another_account_user = create_test_owner(email='another@pneumatic.app')
    TemplateOwner.objects.create(
        template=template,
        account=account,
        user_id=another_account_user.id,
        type=OwnerType.USER,
    )
    api_client.token_authenticate(another_account_user)

    # act
    response = api_client.get('/templates/titles-by-workflows')

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
        '/templates/titles-by-workflows',
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
    response = api_client.get(
        '/templates/titles-by-workflows',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_running__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    api_client.token_authenticate(user)
    create_test_workflow(
        user=user,
        template=template,
    )

    # act
    response = api_client.get(
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.RUNNING}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__status_delayed__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DELAYED,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.DELAYED}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__status__user_not_owner__empty_result(
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
    )
    request_user = create_test_not_admin(account=account)
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.RUNNING}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.parametrize(
    'status', (WorkflowStatus.DONE, WorkflowStatus.DELAYED),
)
def test_titles__status_running__not_running_workflow__ok(
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
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.RUNNING}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 0


def test_titles__status_running__deleted_workflow__ok(
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
    workflow.delete()
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.RUNNING}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 0


def test_titles__status_running__not_template_owner__empty_result(
    api_client,
):

    """ Not owner but task performer """

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        tasks_count=1,
    )
    workflow = create_test_workflow(
        user=account_owner,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    request_user = create_test_not_admin(account=account)
    TaskPerformer.objects.create(
        task=task,
        user=request_user,
        is_completed=False,
    )
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.RUNNING}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_done__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DONE,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.DONE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


@pytest.mark.parametrize(
    'status', (WorkflowStatus.RUNNING, WorkflowStatus.DELAYED),
)
def test_titles__status_done__not_done_workflow__ok(
    status,
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
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
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.DONE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 0


def test_titles__status_done__another_user__not_found(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    template = create_test_template(
        user=account_owner,
        tasks_count=1,
    )
    create_test_workflow(
        user=account_owner,
        template=template,
        status=WorkflowStatus.DONE,
    )
    request_user = create_test_not_admin(account=account)
    api_client.token_authenticate(request_user)

    # act
    response = api_client.get(
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.DONE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__status_done__deleted_workflow__ok(
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
    workflow.delete()
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(
        f'/templates/titles-by-workflows?status={WorkflowApiStatus.DONE}',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['count'] == 0


def test_titles__status_invalid_value__validation_error(
    api_client,
):

    # arrange
    account = create_test_account()
    account_owner = create_test_owner(account=account)
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.get(
        '/templates/titles-by-workflows?status=undefined',
    )

    # assert
    assert response.status_code == 400
    message = '"undefined" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'status'
