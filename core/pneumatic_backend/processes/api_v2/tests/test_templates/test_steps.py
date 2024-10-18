import pytest

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    TemplateType
)
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0022,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)


pytestmark = pytest.mark.django_db


def test_steps__all_tasks__ok(api_client):
    # arrange
    user = create_test_user()
    template = create_test_template(user, is_active=True)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.data[0]['number'] == 1
    assert response.data[0]['id']
    assert response.data[0]['name']
    assert response.data[1]['number'] == 2
    assert response.data[1]['id']
    assert response.data[1]['name']
    assert response.data[2]['number'] == 3
    assert response.data[2]['id']
    assert response.data[2]['name']


def test_steps__user_is_template_owner__ok(api_client):
    # arrange
    user = create_test_user()
    regular_user = create_test_user(
        email='regular_user@pneumatic.app',
        account=user.account,
        is_admin=False,
    )
    template = create_test_template(user, is_active=True)
    first_task = template.tasks.get(number=1)
    first_task.add_raw_performer(regular_user)
    api_client.token_authenticate(regular_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.data[0]['number'] == 1
    assert response.data[0]['id']
    assert response.data[0]['name']
    assert response.data[1]['number'] == 2
    assert response.data[1]['id']
    assert response.data[1]['name']
    assert response.data[2]['number'] == 3
    assert response.data[2]['id']
    assert response.data[2]['name']


def test_steps__user_not_template_owner__empty_result(api_client):

    # arrange
    user = create_test_user()
    user.account.billing_plan = BillingPlanType.PREMIUM
    user.account.save()
    regular_user = create_test_user(
        email='regular_user@pneumatic.app',
        account=user.account,
        is_admin=False,
    )
    template = create_test_template(user, is_active=True)
    template.template_owners.remove(regular_user)
    api_client.token_authenticate(regular_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__user_from_another_acc__empty_result(api_client):
    # arrange
    user = create_test_user()
    template = create_test_template(user, is_active=True)
    another_user = create_test_user(email='another@pneumatic.app')
    api_client.token_authenticate(another_user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_false__running_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    create_test_workflow(
        user=user,
        template=template
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__filter_with_tasks_in_progress_false__delayed_wf__ok(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    workflow = create_test_workflow(
        name='delayed workflow',
        user=user,
        template=template
    )
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.tasks.get(number=1).id},
    )
    workflow.refresh_from_db()
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    template_task_1 = template.tasks.get(number=1)
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task_1.id


def test_steps__with_tasks_in_progress_false__running_wf_completed_task__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    workflow = create_test_workflow(
        user=user,
        template=template
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    template_task_1 = template.tasks.get(number=1)
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task_1.id


def test_steps__filter_with_tasks_in_progress_false__done_wf__ok(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=user,
        template=template
    )
    api_client.token_authenticate(user)
    api_client.post(
        path=f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    template_task_1 = template.tasks.get(number=1)
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task_1.id


def test_steps__with_tasks_in_progress_false__another_user_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    template = create_test_template(
        user=user_2,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=user_2,
        template=template
    )
    api_client.token_authenticate(user_2)
    api_client.post(
        path=f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps_with_tasks_in_progress_false__terminated_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with terminated workflow',
        user=user,
        is_active=True,
        tasks_count=2
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()
    service = WorkflowActionService(user=user)
    service.terminate_workflow(workflow)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_false__ended_wf__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with ended workflow',
        user=user,
        is_active=True,
        tasks_count=2
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    api_client.token_authenticate(user)
    api_client.post(
        path=f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )
    WorkflowActionService().end_process(
        workflow=workflow,
        user=user,
        by_condition=False,
    )

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=false',
    )

    # assert
    assert response.status_code == 200
    template_task_1 = template.tasks.get(number=1)
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task_1.id


def test_steps__with_tasks_in_progress_true__running_wf__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    create_test_workflow(
        user=user,
        template=template
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    template_task_1 = template.tasks.get(number=1)
    assert len(response.data) == 1
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task_1.id


def test_steps__filter_with_tasks_in_progress_true__delayed_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    workflow = create_test_workflow(
        name='delayed workflow',
        user=user,
        template=template
    )
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.tasks.get(number=1).id},
    )
    workflow.refresh_from_db()
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_true__running_wf_completed_task__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    workflow = create_test_workflow(
        user=user,
        template=template
    )
    api_client.token_authenticate(user)
    api_client.post(
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    template_task_1 = template.tasks.get(number=2)
    assert len(response.data) == 1
    assert response.data[0]['number'] == 2
    assert response.data[0]['id'] == template_task_1.id


def test_steps__filter_with_tasks_in_progress_true__done_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=user,
        template=template
    )
    api_client.token_authenticate(user)
    api_client.post(
        path=f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id},
    )

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_true__another_user_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    template = create_test_template(
        user=user_2,
        is_active=True,
        tasks_count=1
    )
    create_test_workflow(
        user=user_2,
        template=template
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps_with_tasks_in_progress_true__terminated_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with terminated workflow',
        user=user,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    api_client.token_authenticate(user)
    workflow.refresh_from_db()
    service = WorkflowActionService(user=user)
    service.terminate_workflow(workflow)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__with_tasks_in_progress_true__ended_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with ended workflow',
        user=user,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    WorkflowActionService().end_process(
        workflow=workflow,
        user=user,
        by_condition=False,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps?with_tasks_in_progress=true',
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_steps__is_running_workflows__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        finalizable=True,
        tasks_count=4
    )
    template_task_1 = template.tasks.get(number=1)
    template_task_3 = template.tasks.get(number=3)

    create_test_workflow(
        name='first step workflow',
        template=template,
        user=user
    )

    delay_workflow = create_test_workflow(
        name='second step workflow',
        user=user,
        template=template
    )
    api_client.post(
        f'/workflows/{delay_workflow.id}/task-complete',
        data={'task_id': delay_workflow.current_task_instance.id},
    )
    delay_workflow.refresh_from_db()
    delay_workflow.status = WorkflowStatus.DELAYED
    delay_workflow.save()

    third_task_workflow = create_test_workflow(
        name='third step workflow',
        user=user,
        template=template
    )
    api_client.post(
        f'/workflows/{third_task_workflow.id}/task-complete',
        data={'task_id': third_task_workflow.current_task_instance.id},
    )
    third_task_workflow.refresh_from_db()
    api_client.post(
        f'/workflows/{third_task_workflow.id}/task-complete',
        data={'task_id': third_task_workflow.current_task_instance.id},
    )

    done_workflow = create_test_workflow(
        name='fourth step workflow',
        user=user,
        template=template
    )
    api_client.post(
        f'/workflows/{done_workflow.id}/task-complete',
        data={'task_id': done_workflow.current_task_instance.id},
    )
    done_workflow.refresh_from_db()
    api_client.post(
        f'/workflows/{done_workflow.id}/task-complete',
        data={'task_id': done_workflow.current_task_instance.id},
    )
    done_workflow.refresh_from_db()
    api_client.post(
        f'/workflows/{done_workflow.id}/task-complete',
        data={'task_id': done_workflow.current_task_instance.id},
    )
    done_workflow.refresh_from_db()
    done_workflow.status = WorkflowStatus.DONE
    done_workflow.save()

    # act
    response = api_client.get(
        f'/templates/{template.id}/steps',
        data={'is_running_workflows': True}
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['number'] == 1
    assert response.data[0]['id'] == template_task_1.id
    assert response.data[0]['name'] == template_task_1.name
    assert response.data[1]['number'] == 3
    assert response.data[1]['id'] == template_task_3.id
    assert response.data[1]['name'] == template_task_3.name


def test__step__incompatible_filters__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1
    )

    response = api_client.get(
        f'/templates/{template.id}/steps',
        data={
            'is_running_workflows': True,
            'with_tasks_in_progress': True
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_PW_0022


def test_steps__onboarding_admin_template__empty_result(api_client):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user,
        type_=TemplateType.ONBOARDING_ADMIN,
        is_active=True
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates/{template.id}/steps')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0
