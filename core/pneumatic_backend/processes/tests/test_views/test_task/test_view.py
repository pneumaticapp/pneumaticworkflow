import pytest
from pneumatic_backend.processes.models import (
    FieldTemplate,
    Workflow,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template
)
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.enums import (
    FieldType
)

pytestmark = pytest.mark.django_db


class TestTaskView:

    @staticmethod
    def _create_workflow(user, api_client) -> Workflow:

        """ Create a workflow for testing
            a output field of type "user" in task """

        template = create_test_template(
            user=user,
            is_active=True
        )

        template_first_task = template.tasks.order_by('number').first()
        FieldTemplate.objects.create(
            name='Enter performer for next task',
            type=FieldType.USER,
            is_required=True,
            task=template_first_task,
            template=template,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test name',
                'kickoff': None
            }
        )
        workflow = Workflow.objects.get(pk=response.data['id'])
        return workflow

    def test_complete__validation_error_required_output_user_field(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = self._create_workflow(user=user, api_client=api_client)
        current_task = workflow.current_task_instance
        output_field = current_task.output.first()

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': current_task.id
                # "output is empty"
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0023
        assert response.data['details']['reason'] == messages.MSG_PW_0023
        assert response.data['details']['api_name'] == output_field.api_name

    def test_complete__validation_error_output_user_field_wrong_type(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = self._create_workflow(user=user, api_client=api_client)
        current_task = workflow.current_task_instance
        output_field = current_task.output.first()

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': current_task.id,
                'output': {
                    output_field.api_name: 'incorrect integer'
                }
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0038
        assert response.data['details']['api_name'] == output_field.api_name
        assert response.data['details']['reason'] == messages.MSG_PW_0038

    def test_complete__validation_error_output_user_field_not_exist(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)
        workflow = self._create_workflow(user=user, api_client=api_client)
        current_task = workflow.current_task_instance
        output_field = current_task.output.first()

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': current_task.id,
                'output': {
                    output_field.api_name: '-1'
                }
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0039
        assert response.data['details']['api_name'] == output_field.api_name
        assert response.data['details']['reason'] == messages.MSG_PW_0039

    def test_complete__validation_error_output_user_field_not_exist2(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        another_account_user = create_test_user(email='test2@pneumatic.app')
        api_client.token_authenticate(user)
        workflow = self._create_workflow(user=user, api_client=api_client)
        current_task = workflow.current_task_instance
        output_field = current_task.output.first()

        # act
        response = api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': current_task.id,
                'output': {
                    output_field.api_name: str(another_account_user.id)
                }
            }
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == messages.MSG_PW_0039
        assert response.data['details']['api_name'] == output_field.api_name
        assert response.data['details']['reason'] == messages.MSG_PW_0039

    def test_complete__insert_output_user_through_task__ok(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        user2 = create_test_user(
            email='test2@pneumatic.app',
            account=user.account
        )
        api_client.token_authenticate(user)

        template = create_test_template(
            user=user,
            is_active=True
        )

        template_first_task = template.tasks.order_by('number').first()
        field_template = FieldTemplate.objects.create(
            name='Enter performer for next task',
            type=FieldType.USER,
            is_required=True,
            task=template_first_task,
            template=template,
        )
        template_second_task = template_first_task.next
        template_second_task.description = (
            'Name is {{ %s }}.' % field_template.api_name
        )
        template_second_task.save()
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test name',
            }
        )
        workflow = Workflow.objects.get(pk=response.data['id'])
        current_task = workflow.current_task_instance
        output_field = current_task.output.first()

        # act
        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={
                'task_id': current_task.id,
                'output': {
                    output_field.api_name: str(user2.id)
                }
            }
        )
        workflow.refresh_from_db()
        current_task = workflow.current_task_instance

        # assert
        assert current_task.description == (
            f'Name is {user2.first_name} {user2.last_name}.'
        )


class TestRecentTaskView:

    def test_list__status_completed__return_recent_completed(
        self,
        api_client
    ):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        api_client.token_authenticate(user)

        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': workflow.current_task_instance.id},
        )
        task = workflow.tasks.get(number=2)
        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': task.id},
        )

        # act
        response = api_client.get('/recent-task?status=completed')

        # assert
        assert response.data['results'][0]['id'] == task.id

    def test_list__status_running__return_recent_running(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        create_test_workflow(user)

        api_client.token_authenticate(user)

        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': workflow.current_task_instance.id},
        )

        # act
        response = api_client.get('/recent-task?status=running')

        # assert
        task = workflow.tasks.get(number=2)
        assert response.data['results'][0]['id'] == task.id

    def test_list__default__return_recent_running(
        self,
        api_client
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        create_test_workflow(user)

        api_client.token_authenticate(user)

        api_client.post(
            f'/workflows/{workflow.id}/task-complete',
            data={'task_id': workflow.current_task_instance.id},
        )

        # act
        response = api_client.get('/recent-task')

        # assert
        task = workflow.tasks.get(number=2)
        assert response.data['results'][0]['id'] == task.id
