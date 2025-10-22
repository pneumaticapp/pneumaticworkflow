import pytest
from django.contrib.auth import get_user_model

from src.authentication.enums import AuthTokenType
from src.processes.tasks.tasks import complete_tasks
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_complete_tasks__ok(api_client):

    # arrange
    user = create_test_user()
    second_user = create_test_user(
        email='second_user@pneumatic.app',
        account=user.account,
    )
    workflow = create_test_workflow(
        user=user,
    )
    second_workflow = create_test_workflow(
        user=user,
    )
    second_workflow_first_task = second_workflow.tasks.get(number=1)
    second_workflow_first_task.performers.add(second_user)
    second_workflow_first_task.require_completion_by_all = True
    second_workflow_first_task.save()
    first_task = workflow.tasks.get(number=1)
    first_task.require_completion_by_all = True
    first_task.save()
    first_task.taskperformer_set.filter(user=user).update(
        is_completed=True,
    )
    second_workflow_first_task.taskperformer_set.filter(
        user=user,
    ).update(is_completed=True)

    # act
    complete_tasks(
        is_superuser=False,
        auth_type=AuthTokenType.USER,
        user_id=user.id,
    )

    # assert
    first_task.refresh_from_db()
    second_workflow_first_task.refresh_from_db()
    assert first_task.is_completed
    assert second_workflow_first_task.is_completed is False
