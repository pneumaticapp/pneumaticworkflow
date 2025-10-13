import pytest

from src.processes.models.workflows.task import TaskPerformer
from src.processes.models.templates.owner import TemplateOwner
from src.processes.enums import (
    OwnerType,
    PerformerType,
)
from src.processes.tests.fixtures import (
    create_test_template,
    create_test_workflow,
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_group,
)


pytestmark = pytest.mark.django_db


def test_count_templates__group_in_template_owner__ok(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    TemplateOwner.objects.create(
        template=template,
        account=user.account,
        type=OwnerType.GROUP,
        group_id=group.id,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__group_in_raw_performer__ok(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    template_task = template.tasks.get(number=1)
    template_task.add_raw_performer(
        performer_type=PerformerType.GROUP,
        group=group,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__group_in_task_performer__ok(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    workflow = create_test_workflow(user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    TaskPerformer.objects.create(
        task_id=task.id,
        type=PerformerType.GROUP,
        group_id=group.id,
    )

    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 1


def test_count_templates__non_existent_group__not_found(api_client):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/groups/99999/count-workflows',
    )

    # assert
    assert response.status_code == 404


def test_count_templates__empty_result(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 0


def test_count_templates__raw_performer_in_multiple_templates__ok(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    template1 = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    template2 = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    template1.tasks.get(number=1).add_raw_performer(
        performer_type=PerformerType.GROUP,
        group=group,
    )
    template2.tasks.get(number=1).add_raw_performer(
        performer_type=PerformerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 2


def test_count_templates__performer_in_multiple_workflows__ok(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])

    workflow1 = create_test_workflow(user)
    workflow2 = create_test_workflow(user)

    TaskPerformer.objects.create(
        task=workflow1.tasks.get(number=1),
        type=PerformerType.GROUP,
        group=group,
    )
    TaskPerformer.objects.create(
        task=workflow2.tasks.get(number=1),
        type=PerformerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 2


def test_count_templates__inactive_templates_not_counted__ok(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    inactive_template = create_test_template(
        user=user,
        is_active=False,
        tasks_count=1,
    )
    inactive_template.tasks.get(number=1).add_raw_performer(
        performer_type=PerformerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(user)
    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 0


def test_count_templates__deleted_workflows_not_counted__ok(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    deleted_workflow = create_test_workflow(user)
    deleted_workflow.is_deleted = True
    deleted_workflow.save()
    TaskPerformer.objects.create(
        task=deleted_workflow.tasks.get(number=1),
        type=PerformerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 0


def test_count_templates__another_account_group__not_found(
    api_client,
):
    # arrange
    another_account = create_test_account(name="Acc 1")
    account = create_test_account(name="Acc 2")
    another_account_user = create_test_user(account=another_account)
    user = create_test_user(account=account, email="user2@test.com")
    group = create_test_group(another_account, users=[another_account_user])
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 404


def test_count_templates__template_and_workflow_task_performer__ok(api_client):
    # arrange
    user = create_test_user()
    group = create_test_group(user.account, users=[user])
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    workflow = create_test_workflow(user)
    template.tasks.get(number=1).add_raw_performer(
        performer_type=PerformerType.GROUP,
        group=group,
    )

    TaskPerformer.objects.create(
        task=workflow.tasks.get(number=1),
        type=PerformerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/groups/{group.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 2
