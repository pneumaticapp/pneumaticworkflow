import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.consumers import PneumaticBaseConsumer
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)
from pneumatic_backend.processes.services.websocket import WSSender
from pneumatic_backend.processes.api_v2.serializers.workflow.task import (
    TaskSerializer
)


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestWSSender:

    class TestConsumer(PneumaticBaseConsumer):
        classname = 'test'

    def test__send_task_notification__ok(
        self,
        mocker
    ):

        # arrange
        template_owner = create_test_user()
        workflow = create_test_workflow(
            user=template_owner,
            is_urgent=True
        )
        task = workflow.current_task_instance
        task.due_date = task.date_first_started + timedelta(hours=1)
        task.save(update_fields=['due_date'])

        send_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.send'
        )
        consumer_cls = self.TestConsumer
        task_data = TaskSerializer(
            instance=task,
            context={'user': template_owner}
        ).data

        # act
        WSSender._send_task_notification(
            task=task,
            consumer_cls=consumer_cls,
            sync=False
        )

        # assert
        send_mock.assert_called_once_with(
            group_name=f'{consumer_cls.classname}_{template_owner.id}',
            data={
                'id': task.id,
                'name': task.name,
                'workflow_name': workflow.name,
                'due_date': task_data['due_date'],
                'due_date_tsp': task_data['due_date_tsp'],
                'date_started': task_data['date_started'],
                'date_started_tsp': task_data['date_started_tsp'],
                'date_completed': None,
                'date_completed_tsp': None,
                'template_id': workflow.template_id,
                'template_task_id': task.template_id,
                'is_urgent': True,
            }
        )

    def test__send_task_notification__deleted_performer__ok(
        self,
        mocker
    ):

        # arrange
        template_owner = create_test_user()
        user_performer = create_test_user(
            email='test@test.test',
            account=template_owner.account
        )
        workflow = create_test_workflow(template_owner)
        task = workflow.current_task_instance
        task.performers.add(user_performer)
        TaskPerformersService.delete_performer(
            task=task,
            request_user=template_owner,
            user_key=user_performer.id
        )

        send_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.send'
        )
        slz_data_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.serializers.workflow.task'
            '.TaskListSerializer.data',
        )
        consumer_cls = self.TestConsumer

        # act
        WSSender._send_task_notification(
            task=task,
            consumer_cls=consumer_cls,
            sync=False
        )

        # assert
        send_mock.assert_called_once_with(
            group_name=f'{consumer_cls.classname}_{template_owner.id}',
            data=slz_data_mock
        )

    def test__send_task_notification__specified_user_ids__ok(
        self,
        mocker
    ):

        # arrange
        template_owner = create_test_user()
        workflow = create_test_workflow(template_owner)
        task = workflow.current_task_instance
        user_performer = create_test_user(
            email='test@test.test',
            account=template_owner.account
        )

        send_mock = mocker.patch(
            'pneumatic_backend.processes.services.websocket.WSSender.send'
        )
        consumer_cls = self.TestConsumer
        task_data = TaskSerializer(
            instance=task,
            context={'user': template_owner}
        ).data

        # act
        WSSender._send_task_notification(
            task=task,
            consumer_cls=consumer_cls,
            sync=False,
            user_ids=(user_performer.id,)
        )

        # assert
        send_mock.assert_called_once_with(
            group_name=f'{consumer_cls.classname}_{user_performer.id}',
            data={
                'id': task.id,
                'name': task.name,
                'workflow_name': workflow.name,
                'due_date': None,
                'due_date_tsp': None,
                'date_started': task_data['date_started'],
                'date_started_tsp': task_data['date_started_tsp'],
                'date_completed': None,
                'date_completed_tsp': None,
                'template_id': workflow.template_id,
                'template_task_id': task.template_id,
                'is_urgent': False,
            }
        )
