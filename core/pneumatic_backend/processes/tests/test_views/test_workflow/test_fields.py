# pylint: disable=unnecessary-pass
import pytest
from pneumatic_backend.processes.models import (
    TaskField,
    FieldSelection,
    FileAttachment,
    Workflow,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_test_template,
)
from pneumatic_backend.processes.enums import (
    FieldType,
    WorkflowApiStatus,
    WorkflowStatus,
)
from pneumatic_backend.utils.dates import date_format


pytestmark = pytest.mark.django_db


class TestFields:

    def test_fields__workflow_data__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(
            user,
            tasks_count=1,
            status=WorkflowStatus.DONE,
        )
        date_completed_str = workflow.date_completed.strftime(date_format)
        date_completed_tsp = workflow.date_completed.timestamp()
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/fields',
            data={
                'template_id': workflow.template.id
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        workflow_data = response.data['results'][0]
        assert workflow_data['id'] == workflow.id
        assert workflow_data['name'] == workflow.name
        assert workflow_data['status'] == workflow.status
        assert workflow_data['date_created'] == (
            workflow.date_created.strftime(date_format)
        )
        assert workflow_data['date_created_tsp'] == (
            workflow.date_created.timestamp()
        )
        assert workflow_data['date_completed'] == date_completed_str
        assert workflow_data['date_completed_tsp'] == date_completed_tsp

    def test_fields__type_text__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        field = TaskField.objects.create(
            order=1,
            type=FieldType.TEXT,
            name='text',
            task=task,
            value='text',
            workflow=workflow
        )
        non_selected_workflow = create_test_workflow(user, tasks_count=1)
        non_selected_task = non_selected_workflow.tasks.first()
        TaskField.objects.create(
            order=1,
            type=FieldType.TEXT,
            name='text',
            task=non_selected_task,
            value='text',
            workflow=non_selected_workflow
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/fields',
            data={
                'template_id': workflow.template.id
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        fields_data = response.data['results'][0]['fields']
        assert len(fields_data) == 1
        assert fields_data[0]['id'] == field.id
        assert fields_data[0]['task_id'] == task.id
        assert fields_data[0]['kickoff_id'] is None
        assert fields_data[0]['type'] == FieldType.TEXT
        assert fields_data[0]['api_name'] == field.api_name
        assert fields_data[0]['name'] == field.name
        assert fields_data[0]['value'] == field.value
        assert fields_data[0]['selections'] == []
        assert fields_data[0]['attachments'] == []

    def test_fields__type_dropdown__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        kickoff = workflow._get_kickoff()

        field = TaskField.objects.create(
            order=3,
            type=FieldType.DROPDOWN,
            name='dropdown',
            kickoff=kickoff,
            value='text',
            workflow=workflow
        )
        selection = FieldSelection.objects.create(
            field=field,
            value='my lovely value',
            is_selected=True
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/fields',
            data={
                'template_id': workflow.template.id
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        workflow_data = response.data['results'][0]
        assert workflow_data['id'] == workflow.id
        fields_data = workflow_data['fields']
        assert len(fields_data) == 1
        assert fields_data[0]['id'] == field.id
        assert fields_data[0]['task_id'] is None
        assert fields_data[0]['kickoff_id'] == kickoff.id
        assert fields_data[0]['type'] == FieldType.DROPDOWN
        assert fields_data[0]['api_name'] == field.api_name
        assert fields_data[0]['name'] == field.name
        assert fields_data[0]['value'] == field.value
        selections_data = fields_data[0]['selections']
        assert len(selections_data) == 1
        assert selections_data[0]['id'] == selection.id
        assert selections_data[0]['api_name'] == selection.api_name
        assert selections_data[0]['value'] == selection.value
        assert selections_data[0]['is_selected'] is True

    def test_fields__type_file__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        field = TaskField.objects.create(
            name='file',
            task=task,
            type=FieldType.FILE,
            value='value',
            workflow=workflow
        )
        attach = FileAttachment.objects.create(
            name='file',
            url='https://john.cena/john.cena',
            account_id=user.account_id,
            output=field,
            workflow=workflow
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            '/workflows/fields',
            data={
                'template_id': workflow.template.id
            }

        )

        # assert
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        workflow_data = response.data['results'][0]
        assert workflow_data['id'] == workflow.id
        fields_data = workflow_data['fields']
        attachments_data = fields_data[0]['attachments']
        assert len(attachments_data) == 1
        assert attachments_data[0]['id'] == attach.id
        assert attachments_data[0]['name'] == attach.name
        assert attachments_data[0]['url'] == attach.url

    def test_fields__filter_not_existent_template_id__ok(self, api_client):
        """ returns empty list """
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        task = workflow.tasks.first()
        field = TaskField.objects.create(
            order=1,
            type=FieldType.TEXT,
            name='text',
            task=task,
            value='text',
            api_name='field-1',
            workflow=workflow
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': 123,
                'fields': field.api_name,
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['results'] == []

    def test_fields__not_filter_template_id__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        task = workflow.tasks.first()
        field = TaskField.objects.create(
            order=1,
            type=FieldType.TEXT,
            name='text',
            task=task,
            value='text',
            api_name='field-1',
            workflow=workflow
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'fields': field.api_name,
            }
        )

        # assert
        assert response.status_code == 400

    def test_fields__filter_by_status_running__ok(self, api_client):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user,
            is_active=True,
            finalizable=True,
        )
        workflow = create_test_workflow(user, template=template)

        done_workflow = create_test_workflow(user=user, template=template)
        done_workflow.status = WorkflowStatus.DONE
        done_workflow.save()

        delayed_workflow = create_test_workflow(user, template=template)
        delayed_workflow.status = WorkflowStatus.DELAYED
        delayed_workflow.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': template.id,
                'status': WorkflowApiStatus.RUNNING,
            }
        )

        # assert
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == workflow.id

    def test_fields__filter_by_status_delayed__ok(self, api_client):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user,
            is_active=True,
            finalizable=True,
        )
        create_test_workflow(user, template=template)

        done_workflow = create_test_workflow(user=user, template=template)
        done_workflow.status = WorkflowStatus.DONE
        done_workflow.save()

        delayed_workflow = create_test_workflow(user, template=template)
        delayed_workflow.status = WorkflowStatus.DELAYED
        delayed_workflow.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': template.id,
                'status': WorkflowApiStatus.DELAYED,
            }
        )

        # assert
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == delayed_workflow.id

    def test_fields__filter_by_invalid_status__validation__error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user,
            is_active=True,
            finalizable=True,
        )

        api_client.token_authenticate(user)
        api_client.post(f'/templates/{template.id}/run')
        response = api_client.post(f'/templates/{template.id}/run')
        workflow2_id = response.data['id']
        api_client.post(f'/workflows/{workflow2_id}/finish')

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': template.id,
                'status': 'non-existing-status',
            }
        )

        # assert
        assert response.status_code == 400

    def test_fields__filter_by_status_done__ok(self, api_client):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user,
            is_active=True,
            finalizable=True,
        )

        api_client.token_authenticate(user)
        api_client.post(f'/templates/{template.id}/run')
        response = api_client.post(f'/templates/{template.id}/run')
        workflow2_id = response.data['id']
        api_client.post(f'/workflows/{workflow2_id}/finish')

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': template.id,
                'status': WorkflowApiStatus.DONE,
            }
        )

        # assert
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == workflow2_id

    def test_fields__filter_by_multiple_status__ok(self, api_client):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user,
            with_delay=True,
            is_active=True,
            finalizable=True,
        )
        create_test_workflow(user=user, template=template)
        done_workflow = create_test_workflow(user=user, template=template)
        done_workflow.status = WorkflowStatus.DONE
        done_workflow.save()

        delayed_workflow = create_test_workflow(user=user, template=template)
        delayed_workflow.status = WorkflowStatus.DONE
        delayed_workflow.save()

        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': template.id,
                'status': (
                    f'{WorkflowApiStatus.DONE},'
                    f'{WorkflowApiStatus.RUNNING}'
                ),
            }
        )

        # assert
        assert len(response.data['results']) == 3

    def test_fields__filter_by_fields__ok(self, api_client):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        field = TaskField.objects.create(
            order=1,
            type=FieldType.TEXT,
            name='text',
            task=task,
            value='text',
            api_name='field-1',
            workflow=workflow
        )
        TaskField.objects.create(
            order=2,
            type=FieldType.TEXT,
            name='text 2',
            task=task,
            value='text 2',
            api_name='field-2',
            workflow=workflow
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': workflow.template.id,
                'fields': field.api_name,
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        workflow_data = response.data['results'][0]
        assert workflow_data['id'] == workflow.id
        assert workflow_data['name'] == workflow.name
        assert workflow_data['status'] == workflow.status
        assert workflow_data['date_created'] is not None
        assert workflow_data['date_completed'] is None
        fields_data = workflow_data['fields']
        assert len(fields_data) == 1
        assert fields_data[0]['id'] == field.id

    def test_fields__filter_by_multiple_fields__ok(self, api_client):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)
        workflow_2 = create_test_workflow(
            user,
            template=workflow.template,
        )
        task = workflow.tasks.first()
        field = TaskField.objects.create(
            order=1,
            type=FieldType.TEXT,
            name='text',
            task=task,
            value='text',
            api_name='field-1',
            workflow=workflow
        )
        field_2 = TaskField.objects.create(
            order=2,
            type=FieldType.TEXT,
            name='text 2',
            task=task,
            value='text 2',
            api_name='field-2',
            workflow=workflow
        )
        TaskField.objects.create(
            order=2,
            type=FieldType.TEXT,
            name='text 2',
            task=task,
            value='text 2',
            api_name='field-non-selected',
            workflow=workflow
        )
        task_2 = workflow_2.tasks.last()
        field_3 = TaskField.objects.create(
            order=1,
            type=FieldType.TEXT,
            name='text',
            task=task_2,
            value='text',
            api_name='field-3',
            workflow=workflow_2
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': workflow.template.id,
                'fields': (
                    f'{field.api_name},'
                    f'{field_2.api_name},'
                    f'{field_3.api_name}'
                ),
            }
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['results']) == 2
        workflow_data = response.data['results'][1]
        assert workflow_data['id'] == workflow.id
        assert workflow_data['name'] == workflow.name
        assert workflow_data['status'] == workflow.status
        assert workflow_data['date_created'] is not None
        assert workflow_data['date_completed'] is None
        fields_data = workflow_data['fields']
        assert len(fields_data) == 2
        assert fields_data[0]['id'] == field_2.id
        assert fields_data[1]['id'] == field.id
        workflow_2_data = response.data['results'][0]
        assert workflow_2_data['id'] == workflow_2.id
        assert workflow_2_data['name'] == workflow_2.name
        assert workflow_2_data['status'] == workflow_2.status
        assert workflow_2_data['date_created'] is not None
        assert workflow_2_data['date_completed'] is None
        fields_2_data = workflow_2_data['fields']
        assert len(fields_2_data) == 1
        assert fields_2_data[0]['id'] == field_3.id

    def test_fields__filter_by_invalid_fields__ok(self, api_client):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.tasks.first()
        TaskField.objects.create(
            order=1,
            type=FieldType.TEXT,
            name='text',
            task=task,
            value='text',
            api_name='field-1',
            workflow=workflow
        )
        TaskField.objects.create(
            order=2,
            type=FieldType.TEXT,
            name='text 2',
            task=task,
            value='text 2',
            api_name='field-2',
            workflow=workflow
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': workflow.template.id,
                'fields': 'field-non-existing',
            }
        )

        # assert
        assert response.status_code == 200
        assert response.data['results'] == []

    def test_fields__pagination__ok(self, api_client):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user,
            with_delay=True,
            is_active=True,
            finalizable=True,
        )
        task = template.tasks.all()[1]
        task.delay = '00:10:00'
        task.save()

        api_client.token_authenticate(user)
        api_client.post(f'/templates/{template.id}/run')
        response = api_client.post(f'/templates/{template.id}/run')
        workflow2_id = response.data['id']
        response = api_client.post(f'/templates/{template.id}/run')
        workflow3_id = response.data['id']
        workflow3 = Workflow.objects.get(id=workflow3_id)
        api_client.post(f'/workflows/{workflow2_id}/finish')
        api_client.post(
            f'/workflows/{workflow3_id}/task-complete',
            data={
                'task_id': workflow3.tasks.first().id,
            }
        )

        # act
        response = api_client.get(
            f'/workflows/fields',
            data={
                'template_id': template.id,
                'limit': 1,
                'offset': 0
            }
        )

        # assert
        assert len(response.data['results']) == 1
