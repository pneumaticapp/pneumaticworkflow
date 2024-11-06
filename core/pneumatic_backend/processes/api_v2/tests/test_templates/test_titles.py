import pytest

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_account,
    create_test_workflow,
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    FieldType,
    WorkflowStatus,
    WorkflowApiStatus,
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)
from pneumatic_backend.processes.messages import template as messages
from pneumatic_backend.utils.validation import ErrorCode


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


def test_titles__ok(api_client):

    # arrange
    user = create_test_user()
    template_1 = create_test_template(
        user=user,
        name='a template',
        is_active=True
    )
    create_test_workflow(user=user, template=template_1,)
    template_2 = create_test_template(
        user=user,
        name='b template',
        is_active=True
    )
    create_test_workflow(user=user, template=template_2,)
    template_3 = create_test_template(
        user=user,
        name='c template',
        is_active=False
    )
    create_test_workflow(user=user, template=template_3,)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/titles')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == template_1.id
    assert response.data[0]['name'] == template_1.name
    assert response.data[1]['id'] == template_2.id
    assert response.data[1]['name'] == template_2.name
    assert response.data[2]['id'] == template_3.id
    assert response.data[2]['name'] == template_3.name


def test_titles__is_active__ok(api_client):
    # arrange
    user = create_test_user()
    create_test_template(user)
    template = create_test_template(
        user=user,
        is_active=True
    )
    api_client.token_authenticate(user)
    create_test_workflow(user=user, template=template)

    # act
    response = api_client.get(
        path='/templates/titles',
        data={'is_active': True}
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name


def test_titles__with_tasks_in_progress_not_in_template_owners__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    user_2 = create_test_user(account=account, email='test@test.test')
    template = create_test_template(
        name='Template with running workflow task',
        user=user,
        is_active=True,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    task.delete_raw_performers()
    task.add_raw_performer(user_2)
    task.update_performers()

    api_client.token_authenticate(user_2)

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__with_tasks_in_progress_true__running_wf__ok(api_client):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with running workflow task',
        user=user,
        is_active=True,
        tasks_count=1
    )
    create_test_workflow(
        user=user,
        template=template,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__with_tasks_in_progress_true__running_wf_completed_task__ok(
    api_client
):
    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with completed workflow task',
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

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__with_tasks_in_progress_true__another_user_wf__not_found(
    api_client
):
    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    template = create_test_template(
        name='Template with running workflow task',
        user=user_2,
        is_active=True,
        tasks_count=1
    )
    create_test_workflow(
        user=user,
        template=template,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__with_tasks_in_progress_true__completed_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_workflow(
        user=user,
        status=WorkflowStatus.DONE
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__with_tasks_in_progress_true__delayed_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    create_test_workflow(
        user=user,
        status=WorkflowStatus.DELAYED
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__with_tasks_in_progress_true__terminated_wf__not_found(
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
    service = WorkflowActionService(user=user)
    service.terminate_workflow(workflow)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__with_tasks_in_progress_true__ended_wf__not_found(
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
        '/templates/titles?with_tasks_in_progress=true'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__with_tasks_in_progress_false__running_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with running workflow task',
        user=user,
        is_active=True,
        tasks_count=1
    )
    create_test_workflow(
        user=user,
        template=template,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=false'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__with_tasks_in_progress_false__running_wf_completed_task__ok(
    api_client
):
    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with completed workflow task',
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

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=false'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__with_tasks_in_progress_false__another_user_wf__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    template = create_test_template(
        name='Template with running workflow task',
        user=user_2,
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

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=false'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__with_tasks_in_progress_false__completed_wf__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with completed workflow',
        user=user,
        is_active=True,
        tasks_count=1
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
    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=false'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__with_tasks_in_progress_false__delayed_wf__ok(api_client):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='template with delayed workflow',
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
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=false'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__with_tasks_in_progress_false__terminated_wf__not_found(
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
        '/templates/titles?with_tasks_in_progress=false'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__with_tasks_in_progress_false__ended_wf__ok(
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
        f'/workflows/{workflow.id}/task-complete',
        data={'task_id': workflow.current_task_instance.id}
    )
    workflow.refresh_from_db()
    WorkflowActionService().end_process(
        workflow=workflow,
        user=user,
        by_condition=False,
    )

    # act
    response = api_client.get(
        '/templates/titles?with_tasks_in_progress=false'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__user_doesnt_have_tasks_in_progress__not_show(
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    another_user = create_test_user(
        email='anotheruser@pneumatic.app',
        account=account,
    )
    user_without_templates = create_test_user(
        email='userwithouttemplates@pneumatic.app',
        account=account,
    )
    second_running_template = create_test_template(user, is_active=True)

    another_template = create_test_template(another_user, is_active=True)
    another_template.template_owners.remove(user.id)
    api_client.token_authenticate(another_user)
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [another_user.id],
            'is_active': True,
            'kickoff': {
                'fields': [
                    {
                        'type': FieldType.USER,
                        'name': 'Performer',
                        'order': 1,
                        'api_name': 'user-field-1',
                        'is_required': True,
                    }
                ]
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': another_user.id
                        },
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'user-field-1'
                        }
                    ]
                },
                {
                    'number': 2,
                    'name': 'Second step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user_without_templates.id
                        }
                    ]
                }
            ]
        }
    )
    running_id = response.data['id']
    api_client.post(f'/templates/{another_template.id}/run')
    api_client.post(
        f'/templates/{running_id}/run',
        data={
            'kickoff': {
                'user-field-1': user.id,
            }
        }
    )
    api_client.token_authenticate(user)
    api_client.post(f'/templates/{second_running_template.id}/run')

    # act
    api_client.token_authenticate(user_without_templates)
    response = api_client.get(
        '/templates/titles',
        data={
            'with_tasks_in_progress': True
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_running__running_workflow__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    api_client.token_authenticate(user)
    create_test_workflow(
        user=user,
        template=template
    )

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.RUNNING}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__workflows_status_running__delayed_workflow__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='template with delayed workflow',
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
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.DELAYED}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__workflows_status_running__another_user_workflow__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    template = create_test_template(
        name='Template with running workflow task',
        user=user_2,
        is_active=True,
        tasks_count=1
    )
    create_test_workflow(
        user=user,
        template=template,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.RUNNING}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_running__completed_workflow__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with completed workflow',
        user=user,
        is_active=True,
        tasks_count=1
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

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.RUNNING}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_running__terminated_workflow__not_found(
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
    service = WorkflowActionService(user=user)
    service.terminate_workflow(workflow)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.RUNNING}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_running__ended_workflow__not_found(
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
        f'/templates/titles?workflows_status={WorkflowApiStatus.RUNNING}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.parametrize('is_active', (True, False))
def test_titles__workflows_status_running__not_template_owner__not_found(
    api_client,
    is_active
):

    """ Not owner but task performer """

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    user_2 = create_test_user(account=account, email='test@test.test')
    template = create_test_template(
        name='Template with running workflow task',
        user=user,
        is_active=is_active,
        tasks_count=1
    )
    workflow = create_test_workflow(
        user=user,
        template=template,
    )
    task = workflow.tasks.get(number=1)
    task.delete_raw_performers()
    task.add_raw_performer(user_2)
    task.update_performers()

    api_client.token_authenticate(user_2)

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.RUNNING}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_done__running_workflow__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    create_test_template(
        user=user,
        tasks_count=1,
        is_active=True
    )
    api_client.token_authenticate(user)
    create_test_workflow(
        user=user,
        template=template
    )

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.DONE}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_done__delayed_workflow__ok(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='template with delayed workflow',
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
    workflow.status = WorkflowStatus.DELAYED
    workflow.save(update_fields=['status'])

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.DONE}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_done__another_user_workflow__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    template = create_test_template(
        name='Template with running workflow task',
        user=user_2,
        is_active=True,
        tasks_count=1
    )
    create_test_workflow(
        user=user,
        template=template,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.DONE}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_done__completed_workflow__not_found(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(
        name='Template with completed workflow',
        user=user,
        is_active=True,
        tasks_count=1
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

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.DONE}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__workflows_status_done__terminated_workflow__not_found(
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
    service = WorkflowActionService(user=user)
    service.terminate_workflow(workflow)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/templates/titles?workflows_status={WorkflowApiStatus.DONE}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__workflows_status_done__ended_workflow__not_found(
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
        f'/templates/titles?workflows_status={WorkflowApiStatus.DONE}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles__workflows_status_invalid_value__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates/titles?workflows_status=undefined')

    # assert
    assert response.status_code == 400
    message = '"undefined" is not a valid choice.'
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['name'] == 'workflows_status'


def test_titles__workflows_status_and_with_tasks_in_progress__validation_error(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        path='/templates/titles',
        data={
            "workflows_status": WorkflowApiStatus.RUNNING,
            'with_tasks_in_progress': True
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == messages.MSG_PT_0022


def test_titles__not_workflows__not_found(api_client):

    # arrange
    user = create_test_user()
    create_test_template(user=user, is_active=True)
    create_test_template(user=user, is_active=True)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/titles')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__all_statuses__deleted_not_found(api_client):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    api_client.token_authenticate(user)
    workflow.delete()

    # act
    response = api_client.get('/templates/titles')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles__calc_most_popular__by_all_status__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = create_test_template(
        user=user,
        is_active=True,
        name='Ended'
    )
    create_test_workflow(
        user=user,
        template=template_1,
        status=WorkflowStatus.DONE
    )
    create_test_workflow(
        user=user,
        template=template_1,
        status=WorkflowStatus.DONE
    )
    create_test_template(
        user=user,
        is_active=True,
        name='Not workflows'
    )
    template_3 = create_test_template(
        user=user,
        is_active=True,
        name='Delayed'
    )
    create_test_workflow(
        user=user,
        template=template_3,
        status=WorkflowStatus.DELAYED
    )
    create_test_workflow(
        user=user,
        template=template_3,
        status=WorkflowStatus.DELAYED
    )
    template_4 = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template_4)
    workflow.delete()
    template_5 = create_test_template(user=user, is_active=True)
    create_test_workflow(user=user, template=template_5)

    # act
    response = api_client.get('/templates/titles')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == template_3.id
    assert response.data[0]['workflows_count'] == 2
    assert response.data[1]['id'] == template_1.id
    assert response.data[1]['workflows_count'] == 2
    assert response.data[2]['id'] == template_5.id
    assert response.data[2]['workflows_count'] == 1


def test_titles__default_ordering_by_most_popular__ok(api_client):

    # arrange
    user = create_test_user()
    template_1 = create_test_template(user=user, is_active=True)
    create_test_workflow(user=user, template=template_1,)
    template_2 = create_test_template(user=user, is_active=True)
    create_test_workflow(user=user, template=template_2)
    create_test_workflow(user=user, template=template_2)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/titles')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template_2.id
    assert response.data[1]['id'] == template_1.id
