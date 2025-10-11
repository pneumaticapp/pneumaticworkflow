import pytest
from django.contrib.auth import get_user_model
from src.processes.models import (
    Workflow,
    Task,
)
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)


UserModel = get_user_model()


pytestmark = pytest.mark.django_db


class TestWorkflow:
    @pytest.fixture
    def workflow_sql(self):
        return """
          SELECT
            id,
            is_deleted,
            template_id
          FROM processes_workflow
          WHERE id = %(workflow_id)s
        """

    @pytest.fixture
    def task_sql(self):
        return """
          SELECT
            id,
            is_deleted
          FROM processes_task
          WHERE workflow_id = %(workflow_id)s
        """

    def test_delete(
        self,
        workflow_sql,
        task_sql,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)

        # act
        workflow.delete()

        # assert
        assert Workflow.objects.raw(
            workflow_sql,
            {'workflow_id': workflow.id},
        )[0].is_deleted is True
        task_list = Task.objects.raw(
            task_sql,
            {'workflow_id': workflow.id},
        )
        assert task_list[0].is_deleted is True
        assert task_list[1].is_deleted is True
        assert task_list[2].is_deleted is True

    def test_get_kickoff_fields_values__ok(self, mocker):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user=user)
        field_mock = mocker.Mock(
            api_name='field-template',
            markdown_value='test',
        )
        kickoff_output_fields_mock = mocker.patch(
            'src.processes.models.Workflow.'
            'get_kickoff_output_fields',
            return_value=[field_mock],
        )

        # act
        workflow.get_kickoff_fields_values()

        # assert
        kickoff_output_fields_mock.assert_called_once()
