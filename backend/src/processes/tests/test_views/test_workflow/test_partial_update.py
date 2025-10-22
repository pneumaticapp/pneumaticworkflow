# ruff: noqa: UP031
from datetime import timedelta

import pytest
import pytz
from django.utils import timezone

from src.accounts.enums import (
    NotificationType,
    SourceType,
)
from src.accounts.models import Notification
from src.accounts.services.user_invite import UserInviteService
from src.analysis.actions import (
    WorkflowActions,
)
from src.authentication.enums import AuthTokenType
from src.generics.messages import MSG_GE_0007
from src.processes.enums import (
    DueDateRule,
    FieldType,
    PerformerType,
    TaskStatus,
    WorkflowEventType,
)
from src.processes.messages.workflow import (
    MSG_PW_0023,
    MSG_PW_0032,
    MSG_PW_0051,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.templates.raw_due_date import RawDueDateTemplate
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.task import (
    TaskPerformer,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.events import (
    WorkflowEventService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)
from src.utils.dates import date_format
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


class TestPartialUpdateWorkflow:

    def test_partial_update__name__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user)
        api_client.token_authenticate(user)
        name = f'{workflow.name} edited'
        analysis_mock = mocker.patch(
            'src.analysis.services.AnalyticService.'
            'workflows_updated',
        )

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={'name': name},
        )

        # assert
        assert response.status_code == 200
        assert response.data['name'] == name
        analysis_mock.assert_called_once_with(
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
            user=user,
        )

    def test_update__all_fields__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        template = create_test_template(user, tasks_count=1, is_active=True)
        field = FieldTemplate.objects.create(
            name='User',
            type=FieldType.TEXT,
            is_required=False,
            kickoff=template.kickoff_instance,
            template=template,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'text 1',
                'kickoff': {
                    field.api_name: 'text 2',
                },
                'is_urgent': False,
            },
        )
        workflow = Workflow.objects.get(pk=response.data['id'])
        name = 'edited text 1'
        field_value = 'edited text 2'
        is_urgent = True
        due_date = timezone.now() + timedelta(days=1)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'name': name,
                'kickoff': {
                    field.api_name: field_value,
                },
                'is_urgent': is_urgent,
                'due_date_tsp': due_date.timestamp(),
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert workflow.due_date == due_date
        assert response.data['name'] == name
        assert response.data['is_urgent'] == is_urgent
        assert response.data['kickoff']['output'][0]['value'] == field_value
        assert response.data['due_date_tsp'] == due_date.timestamp()

    def test_update__task_markdown_description__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        template = create_test_template(user, tasks_count=1, is_active=True)
        kickoff_template = template.kickoff_instance
        field = FieldTemplate.objects.create(
            name='Text',
            type=FieldType.TEXT,
            is_required=False,
            kickoff=kickoff_template,
            template=template,
        )
        template_task = template.tasks.get(number=1)
        template_task.description = '**Bold {{ %s }} text**' % (field.api_name)
        template_task.save()
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Workflow name',
                'kickoff': {
                    field.api_name: '**some[link](https://some.site)**',
                },
            },
        )
        workflow = Workflow.objects.get(pk=response.data['id'])
        field_value = '*Italic [link](https://some.site)*'

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'kickoff': {
                    field.api_name: field_value,
                },
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert response.data['kickoff']['output'][0]['value'] == field_value
        task = workflow.tasks.get(number=1)
        assert task.description == (
            '**Bold *Italic [link](https://some.site)* text**'
        )
        assert task.clear_description == 'Bold Italic link text'
        kickoff_field = workflow.kickoff_instance.output.get(
            api_name=field.api_name,
        )
        assert kickoff_field.value == '*Italic [link](https://some.site)*'
        assert kickoff_field.clear_value == 'Italic link'

    def test_update__kickoff__not_change_due_date__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        template = create_test_template(user, tasks_count=1, is_active=True)
        field = FieldTemplate.objects.create(
            name='User',
            type=FieldType.TEXT,
            is_required=False,
            kickoff=template.kickoff_instance,
            template=template,
        )

        due_date = timezone.now() + timedelta(days=1)
        due_date_str = due_date.strftime(date_format)

        workflow = create_test_workflow(
            user=user,
            template=template,
            due_date=due_date_str,
        )
        field_value = 'edited text 2'

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'name': 'new name',
                'is_urgent': True,
                'kickoff': {
                    field.api_name: field_value,
                },
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert workflow.due_date == due_date
        assert response.data['due_date_tsp'] == due_date.timestamp()

    def test_partial_update__kickoff__ok(
        self,
        api_client,
    ):

        # arrange
        user = create_test_owner()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        kickoff_field = FieldTemplate.objects.create(
            name='User name',
            type=FieldType.STRING,
            is_required=False,
            kickoff=template.kickoff_instance,
            order=0,
            template=template,
        )
        kickoff_field_2 = FieldTemplate.objects.create(
            name='User url',
            type=FieldType.CHECKBOX,
            is_required=True,
            kickoff=template.kickoff_instance,
            order=4,
            template=template,
        )
        kickoff_field_2_select_1 = FieldTemplateSelection.objects.create(
            field_template=kickoff_field_2,
            value='CHECKBOX 1',
            template=template,
        )
        FieldTemplateSelection.objects.create(
            field_template=kickoff_field_2,
            value='CHECKBOX 2',
            template=template,
        )
        kickoff_field_3 = FieldTemplate.objects.create(
            name='User date',
            type=FieldType.RADIO,
            is_required=True,
            kickoff=template.kickoff_instance,
            order=5,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            field_template=kickoff_field_3,
            value='RADIO 1',
            template=template,
        )
        kickoff_field_3_select_2 = FieldTemplateSelection.objects.create(
            field_template=kickoff_field_3,
            value='RADIO 2',
            template=template,
        )
        kickoff_field_4 = FieldTemplate.objects.create(
            name='Date field',
            type=FieldType.DATE,
            is_required=False,
            kickoff=template.kickoff_instance,
            order=9,
            template=template,
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_1.description = (
            '{{ %s }}His name is... {{%s}}{{%s}}!!!' %
            (
                kickoff_field_2.api_name,
                kickoff_field.api_name,
                kickoff_field_3.api_name,
            )
        )
        template_task_1.save()
        template_task_2 = template.tasks.get(number=2)
        template_task_2.description = (
            'His name is... {{%s}}!!!' % kickoff_field.api_name
        )
        template_task_2.save()
        api_client.token_authenticate(user)
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    kickoff_field.api_name: 'JOHN CENA',
                    kickoff_field_2.api_name: [
                        kickoff_field_2_select_1.api_name,
                    ],
                    kickoff_field_3.api_name: (
                        kickoff_field_3_select_2.api_name
                    ),
                    kickoff_field_4.api_name: 1726012800,
                },
            },
        )
        workflow_id = response.data['id']
        workflow = Workflow.objects.get(pk=workflow_id)
        kickoff_output_2 = workflow.kickoff_instance.output.get(
            type=FieldType.CHECKBOX,
        )
        kickoff_output_2_selections = list(
            kickoff_output_2.selections
            .all()
            .values_list('api_name', flat=True),
        )
        kickoff_output_3 = workflow.kickoff_instance.output.get(
            type=FieldType.RADIO,
        )
        kickoff_output_3_selections = list(
            kickoff_output_3.selections
            .all()
            .values_list('api_name', flat=True),
        )

        # act
        response = api_client.patch(
            f'/workflows/{workflow_id}',
            data={
                'kickoff': {
                    kickoff_field.api_name: 'DWAYNE THE ROCK JOHNSON',
                    kickoff_field_2.api_name: [kickoff_output_2_selections[0]],
                    kickoff_field_3.api_name: kickoff_output_3_selections[1],
                    kickoff_field_4.api_name: 1726020000,
                },
            },
        )

        # assert
        assert response.status_code == 200
        first_output = response.data['kickoff']['output'][0]
        second_output = response.data['kickoff']['output'][1]
        third_output = response.data['kickoff']['output'][2]
        fourth_output = response.data['kickoff']['output'][3]
        assert first_output['value'] == '1726020000'
        assert second_output['selections'][0]['is_selected'] is False
        assert second_output['selections'][1]['is_selected'] is True
        assert third_output['selections'][0]['is_selected'] is True
        assert third_output['selections'][1]['is_selected'] is False
        assert fourth_output['value'] == 'DWAYNE THE ROCK JOHNSON'

    def test_partial_update__field__not_update_completed_task_due_date__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        user = create_test_owner()
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=2,
        )
        date_field = FieldTemplate.objects.create(
            name='First task due date',
            type=FieldType.DATE,
            kickoff=template.kickoff_instance,
            template=template,
            api_name='api-name-2',
        )
        template_task = template.tasks.get(number=1)
        duration = timedelta(hours=1, milliseconds=1)
        RawDueDateTemplate.objects.create(
            template=template,
            task=template_task,
            duration=duration,
            duration_months=0,
            rule=DueDateRule.AFTER_FIELD,
            source_id=date_field.api_name,
        )
        field_value = timezone.now() + timedelta(days=1, milliseconds=1)
        api_client.token_authenticate(user)
        field_value_tsp = field_value.timestamp()
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    date_field.api_name: field_value_tsp,
                },
            },
        )
        workflow_id = response.data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        task_1 = workflow.tasks.get(number=1)
        api_client.post(f'/v2/tasks/{task_1.id}/complete')

        new_field_value = timezone.now() + timedelta(days=2)
        tsp_new_field_value = new_field_value.timestamp()
        prev_due_date = task_1.due_date

        # act
        response = api_client.patch(
            f'/workflows/{workflow_id}',
            data={
                'kickoff': {
                    date_field.api_name: tsp_new_field_value,
                },
            },
        )

        # assert
        assert response.status_code == 200
        task_1.refresh_from_db()
        assert task_1.is_completed
        assert task_1.due_date == prev_due_date

    @pytest.mark.parametrize(
        'kickoff_data', (' ', '136166546'),
    )
    def test_partial_update__invalid_kickoff_data_value__validation_error(
        self,
        api_client,
        kickoff_data,
    ):
        # arrange
        user = create_test_owner()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        kickoff_field = FieldTemplate.objects.create(
            name='Date field',
            type=FieldType.DATE,
            is_required=False,
            kickoff=template.kickoff_instance,
            order=9,
            template=template,
        )

        api_client.token_authenticate(user)
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    kickoff_field.api_name: 1726012800,
                },
            },
        )
        workflow_id = response.data['id']

        # act
        response = api_client.patch(
            f'/workflows/{workflow_id}',
            data={
                'kickoff': {
                    kickoff_field.api_name: kickoff_data,
                },
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_PW_0032
        assert response.data['details']['reason'] == MSG_PW_0032
        assert response.data['details']['api_name'] == kickoff_field.api_name

    def test_partial_update__required_field__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        not_required_field = FieldTemplate.objects.create(
            name='text',
            type=FieldType.STRING,
            is_required=False,
            kickoff=template.kickoff_instance,
            template=template,
        )
        required_field = FieldTemplate.objects.create(
            name='User',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )

        api_client.token_authenticate(user)
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    not_required_field.api_name: 'text',
                    required_field.api_name: str(user.id),
                },
            },
        )
        workflow_id = response.data['id']

        # act
        response = api_client.patch(
            f'/workflows/{workflow_id}',
            data={
                'kickoff': {
                    not_required_field.api_name: 'text',
                    required_field.api_name: None,
                },
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_PW_0023
        assert response.data['details']['reason'] == MSG_PW_0023
        assert response.data['details']['api_name'] == required_field.api_name

    def test_partial_update__file_field__ok(self, api_client):

        # arrange
        user = create_test_owner()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        file_field = FieldTemplate.objects.create(
            name='File field',
            type=FieldType.FILE,
            is_required=False,
            kickoff=template.kickoff_instance,
            order=0,
            template=template,
        )

        template_task_1 = template.tasks.get(number=1)
        template_task_1.description = (
            'His name is... {{%s}}!!!' % file_field.api_name
        )
        template_task_1.save()
        template_task_2 = template.tasks.get(number=2)
        template_task_2.description = (
            '{{%s}} His name is...!!!' % file_field.api_name
        )
        template_task_2.save()

        first_attach = FileAttachment.objects.create(
            name='ce.na',
            size=133734,
            url='https://jo.hn/ce.na',
            account_id=user.account_id,
        )

        second_attach = FileAttachment.objects.create(
            name='nh.oj',
            size=133734,
            url='https://an.ec/nh.oj',
            account_id=user.account_id,
        )

        api_client.token_authenticate(user)
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test name',
                'kickoff': {
                    file_field.api_name: [first_attach.id],
                },
            },
        )
        workflow_id = response.data['id']
        workflow = Workflow.objects.get(pk=workflow_id)

        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)
        assert task_1.description == (
            f'His name is... [{first_attach.name}]'
            f'({first_attach.url})!!!'
        )
        assert task_2.description == (
            '{{%s}} His name is...!!!' % file_field.api_name
        )
        first_attach.delete()

        # act
        response = api_client.patch(
            f'/workflows/{workflow_id}',
            data={
                'kickoff': {
                    file_field.api_name: [second_attach.id],
                },
            },
        )

        task_1.refresh_from_db()
        task_2.refresh_from_db()

        # assert
        assert response.status_code == 200
        assert task_1.description == (
            f'His name is... [{second_attach.name}]({second_attach.url})!!!'
        )
        assert task_2.description == (
            '{{%s}} His name is...!!!' % file_field.api_name
        )

    def test_partial_update__attach_one_more_with_all_in_list__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        template = create_test_template(
            user=user,
            is_active=True,
        )
        file_field = FieldTemplate.objects.create(
            name='File field',
            type=FieldType.FILE,
            is_required=False,
            kickoff=template.kickoff_instance,
            order=0,
            template=template,
        )

        template_task_1 = template.tasks.get(number=1)
        template_task_1.description = (
            'His name is... {{%s}}!!!' % file_field.api_name
        )
        template_task_1.save()
        template_task_2 = template.tasks.get(number=2)
        template_task_2.description = (
            '{{%s}} His name is...!!!' % file_field.api_name
        )
        template_task_2.save()

        first_attach = FileAttachment.objects.create(
            name='ce.na',
            size=133734,
            url='https://jo.hn/first.txt',
            account_id=user.account_id,
        )

        second_attach = FileAttachment.objects.create(
            name='nh.oj',
            size=133734,
            url='https://an.ec/second.txt',
            account_id=user.account_id,
        )

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    file_field.api_name: [first_attach.id],
                },
            },
        )
        workflow_id = response.data['id']
        workflow = Workflow.objects.get(pk=workflow_id)

        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)
        assert task_1.description == (
            f'His name is... [{first_attach.name}]'
            f'({first_attach.url})!!!'
        )
        assert task_2.description == (
            '{{%s}} His name is...!!!' % file_field.api_name
        )

        # act
        response = api_client.patch(
            f'/workflows/{workflow_id}',
            data={
                'kickoff': {
                    file_field.api_name: [first_attach.id, second_attach.id],
                },
            },
        )

        task_1.refresh_from_db()
        task_2.refresh_from_db()

        # assert
        assert response.status_code == 200
        assert task_1.description == (
            'His name is... '
            f'[{first_attach.name}]({first_attach.url}), '
            f'[{second_attach.name}]({second_attach.url})!!!'
        )
        assert task_2.description == (
            '{{%s}} His name is...!!!' % file_field.api_name
        )

    def test_partial_update__task_body_with_self_output__ok(
        self,
        mocker,
        api_client,
    ):

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        user = create_test_owner()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        kickoff = template.kickoff_instance
        template_task_1 = template.tasks.get(number=1)
        task_field = FieldTemplate.objects.create(
            name='Task field',
            type=FieldType.STRING,
            is_required=False,
            task=template_task_1,
            template=template,
        )
        kickoff_field = FieldTemplate.objects.create(
            name='User name',
            type=FieldType.STRING,
            is_required=False,
            kickoff=kickoff,
            order=0,
            template=template,
        )
        kickoff_field_2 = FieldTemplate.objects.create(
            name='User url',
            type=FieldType.CHECKBOX,
            is_required=True,
            kickoff=kickoff,
            order=4,
            template=template,
        )
        kickoff_field_2_select_1 = FieldTemplateSelection.objects.create(
            field_template=kickoff_field_2,
            value='CHECKBOX 1',
            template=template,
        )
        FieldTemplateSelection.objects.create(
            field_template=kickoff_field_2,
            value='CHECKBOX 2',
            template=template,
        )
        kickoff_field_3 = FieldTemplate.objects.create(
            name='User date',
            type=FieldType.RADIO,
            is_required=True,
            kickoff=kickoff,
            order=5,
            template=template,
        )
        FieldTemplateSelection.objects.create(
            field_template=kickoff_field_3,
            value='RADIO 1',
            template=template,
        )
        kickoff_field_3_select_2 = FieldTemplateSelection.objects.create(
            field_template=kickoff_field_3,
            value='RADIO 2',
            template=template,
        )
        template_task_1.description = (
            '{{ %s }}His name is... {{%s}}{{%s}}!!!' %
            (
                kickoff_field_2.api_name,
                kickoff_field.api_name,
                kickoff_field_3.api_name,
            )
        )
        template_task_1.save()
        template_task_2 = template.tasks.get(number=2)
        template_task_2.description = (
            'His name is... {{%s}}!!! Or maybe {{%s}}' % (
                kickoff_field.api_name,
                task_field.api_name,
            )
        )
        template_task_2.save()

        api_client.token_authenticate(user)
        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test name',
                'kickoff': {
                    kickoff_field.api_name: 'JOHN CENA',
                    kickoff_field_2.api_name: [
                        kickoff_field_2_select_1.api_name,
                    ],
                    kickoff_field_3.api_name: (
                        kickoff_field_3_select_2.api_name
                    ),
                },
            },
        )
        workflow_id = response.data['id']
        workflow = Workflow.objects.get(pk=workflow_id)
        task_1 = workflow.tasks.get(number=1)

        # act
        api_client.post(
            f'/v2/tasks/{task_1.id}/complete',
            data={
                'output': {
                    task_field.api_name: 'RAMZAN',
                },
            },
        )

        kickoff_output_2 = workflow.kickoff_instance.output.get(
            type=FieldType.CHECKBOX,
        )
        kickoff_output_2_selections = list(
            kickoff_output_2.selections
            .all()
            .values_list('api_name', flat=True),
        )
        kickoff_output_3 = workflow.kickoff_instance.output.get(
            type=FieldType.RADIO,
        )
        kickoff_output_3_selections = list(
            kickoff_output_3.selections
            .all()
            .values_list('api_name', flat=True),
        )

        # act
        response = api_client.patch(
            f'/workflows/{workflow_id}',
            data={
                'name': 'Edited Name',
                'kickoff': {
                    kickoff_field.api_name: 'DWAYNE THE ROCK JOHNSON',
                    kickoff_field_2.api_name: [kickoff_output_2_selections[0]],
                    kickoff_field_3.api_name: kickoff_output_3_selections[1],
                },
            },
        )

        # assert
        assert response.status_code == 200
        first_output = response.data['kickoff']['output'][0]
        second_output = response.data['kickoff']['output'][1]
        third_output = response.data['kickoff']['output'][2]
        assert first_output['selections'][0]['is_selected'] is False
        assert first_output['selections'][1]['is_selected'] is True
        assert second_output['selections'][0]['is_selected'] is True
        assert second_output['selections'][1]['is_selected'] is False
        assert third_output['value'] == 'DWAYNE THE ROCK JOHNSON'
        assert response.data['name'] == 'Edited Name'
        task_2 = workflow.tasks.get(number=2)
        assert task_2.description == (
            'His name is... DWAYNE THE ROCK JOHNSON!!! Or maybe RAMZAN'
        )

    def test_partial_update__mark_is_urgent__ok(
        self,
        api_client,
        mocker,
    ):
        # arrange
        workflow_urgent_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.workflow_urgent_event',
        )
        send_urgent_task_notification_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_urgent_notification.delay',
        )
        analysis_mock = mocker.patch(
            'src.analysis.services.AnalyticService.'
            'workflows_updated',
        )
        analysis_urgent_mock = mocker.patch(
            'src.analysis.services.AnalyticService.'
            'workflows_urgent',
        )
        user = create_test_owner()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(
            user,
            is_urgent=False,
            tasks_count=1,
        )

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={'is_urgent': True},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 200
        assert response.data['is_urgent'] is True
        assert workflow.is_urgent is True
        task = workflow.tasks.get(number=1)
        assert task.is_urgent is True
        analysis_mock.assert_called_once_with(
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
            user=user,
        )
        analysis_urgent_mock.assert_called_once_with(
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
            user=user,
            action=WorkflowActions.marked,
        )
        workflow_urgent_event_mock.assert_called_once_with(
            user=user,
            event_type=WorkflowEventType.URGENT,
            workflow=workflow,
        )
        send_urgent_task_notification_mock.assert_called_once_with(
            logging=user.account.log_api_requests,
            author_id=user.id,
            task_ids=[task.id],
            account_id=user.account_id,
            logo_lg=user.account.logo_lg,
        )

    def test_partial_update__unmark_is_urgent__ok(
        self,
        api_client,
        mocker,
    ):
        # arrange
        workflow_urgent_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.workflow_urgent_event',
        )
        send_not_urgent_task_notification_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_not_urgent_notification.delay',
        )
        analysis_mock = mocker.patch(
            'src.analysis.services.AnalyticService.'
            'workflows_updated',
        )
        analysis_urgent_mock = mocker.patch(
            'src.analysis.services.AnalyticService.'
            'workflows_urgent',
        )
        user = create_test_owner()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user, is_urgent=True, tasks_count=1)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={'is_urgent': False},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 200
        assert response.data['is_urgent'] is False
        assert workflow.is_urgent is False
        task = workflow.tasks.get(number=1)
        assert task.is_urgent is False
        analysis_mock.assert_called_once_with(
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
            user=user,
        )
        analysis_urgent_mock.assert_called_once_with(
            workflow=workflow,
            auth_type=AuthTokenType.USER,
            is_superuser=False,
            user=user,
            action=WorkflowActions.unmarked,
        )
        workflow_urgent_event_mock.assert_called_once_with(
            user=user,
            event_type=WorkflowEventType.NOT_URGENT,
            workflow=workflow,
        )
        send_not_urgent_task_notification_mock.assert_called_once_with(
            logging=user.account.log_api_requests,
            author_id=user.id,
            task_ids=[task.id],
            account_id=user.account_id,
            logo_lg=user.account.logo_lg,
        )

    def test_partial_update__is_urgent_not_changed__analytic_not_called(
        self,
        api_client,
        mocker,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(user, is_urgent=False)
        workflow_urgent_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.workflow_urgent_event',
        )
        send_urgent_task_notification_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_urgent_notification.delay',
        )
        analysis_urgent_mock = mocker.patch(
            'src.analysis.services.AnalyticService.'
            'workflows_urgent',
        )

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={'is_urgent': False},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 200
        assert response.data['is_urgent'] is False
        assert workflow.is_urgent is False
        analysis_urgent_mock.assert_not_called()
        workflow_urgent_event_mock.assert_not_called()
        send_urgent_task_notification_mock.assert_not_called()

    def test_partial_update__delete_recently_urgent_pair_event__ok(
        self,
        api_client,
        mocker,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(
            user,
            is_urgent=True,
            tasks_count=1,
        )
        task = workflow.tasks.get(number=1)
        other_event_1 = WorkflowEventService.workflow_run_event(workflow)
        urgent_event = WorkflowEventService.workflow_urgent_event(
            event_type=WorkflowEventType.URGENT,
            workflow=workflow,
            user=user,
            after_create_actions=False,
        )
        other_event_2 = WorkflowEventService.task_started_event(
            task=task,
            after_create_actions=False,
        )
        workflow_urgent_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.workflow_urgent_event',
        )
        task = workflow.tasks.get(number=1)
        urgent_notification = Notification.objects.create(
            task=task,
            user=user,
            account=workflow.account,
            type=NotificationType.URGENT,
        )

        send_urgent_task_notification_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_urgent_notification.delay',
        )

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={'is_urgent': False},
        )

        # assert
        assert response.status_code == 200
        urgent_notification.refresh_from_db()
        other_event_1.refresh_from_db()
        urgent_event.refresh_from_db()
        other_event_2.refresh_from_db()
        assert urgent_notification.is_deleted is True
        assert other_event_1.is_deleted is False
        assert urgent_event.is_deleted is True
        assert other_event_2.is_deleted is False

        workflow_urgent_event_mock.assert_not_called()
        send_urgent_task_notification_mock.assert_not_called()

    def test_partial_update__urgent_event_duplicate__not_create(
        self,
        api_client,
        mocker,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        workflow = create_test_workflow(
            user,
            is_urgent=True,
            tasks_count=1,
        )
        prev_urgent_event = WorkflowEventService.workflow_urgent_event(
            event_type=WorkflowEventType.URGENT,
            workflow=workflow,
            user=user,
        )
        workflow_urgent_event_mock = mocker.patch(
            'src.processes.services.events.'
            'WorkflowEventService.workflow_urgent_event',
        )
        send_urgent_task_notification_mock = mocker.patch(
            'src.notifications.tasks.'
            'send_urgent_notification.delay',
        )

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={'is_urgent': True},
        )
        workflow.refresh_from_db()

        # assert
        assert response.status_code == 200
        prev_urgent_event.refresh_from_db()
        assert prev_urgent_event.is_deleted is False
        workflow_urgent_event_mock.assert_not_called()
        send_urgent_task_notification_mock.assert_not_called()

    def test_partial__not_admin_user_update_data__ok(self, api_client):

        # arrange
        account = create_test_account()
        create_test_owner(account=account)
        user = create_test_admin(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        field_value = 'edited text 2'
        api_client.token_authenticate(user)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'name': field_value,
                'is_urgent': True,
            },
        )

        # assert
        assert response.status_code == 200
        assert response.data['name'] == field_value
        assert response.data['is_urgent'] is True

    def test_partial__not_template_owner__permission_denided(
        self,
        api_client,
    ):
        # arrange
        acciunt = create_test_account()
        owner = create_test_owner(account=acciunt)
        user = create_test_admin()
        template = create_test_template(owner, tasks_count=1, is_active=True)
        workflow = create_test_workflow(user=owner, template=template)
        field_value = 'edited text 2'
        api_client.token_authenticate(user)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={'name': field_value},
        )

        # assert
        assert response.status_code == 403

    def test_partial__not_template_owner_and_account_owner__ok(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        owner = create_test_owner(account=account)
        user = create_test_admin(account=account)
        template = create_test_template(user, tasks_count=1, is_active=True)
        workflow = create_test_workflow(user=user, template=template)
        field_value = 'edited text 2'
        api_client.token_authenticate(owner)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={'name': field_value},
        )

        # assert
        assert response.status_code == 200

    def test_update__due_date_to_null__remove_due_date(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        due_date = timezone.now() + timedelta(days=1)
        workflow = create_test_workflow(
            user=user,
            tasks_count=1,
            due_date=due_date,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'due_date_tsp': None,
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert workflow.due_date is None
        assert response.data['due_date_tsp'] is None

    def test_update__due_date_tsp_to_null__remove_due_date(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        due_date = timezone.now() + timedelta(days=1)
        workflow = create_test_workflow(
            user=user,
            tasks_count=1,
            due_date=due_date,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'due_date_tsp': None,
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert workflow.due_date is None
        assert response.data['due_date_tsp'] is None

    def test_update__due_date_tsp__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        due_date = timezone.now() + timedelta(days=1)
        workflow = create_test_workflow(
            user=user,
            tasks_count=1,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'due_date_tsp': due_date.timestamp(),
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert workflow.due_date == due_date
        assert response.data['due_date_tsp'] == due_date.timestamp()

    def test_update__due_date_tsp_to_null__ok(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        due_date = timezone.now() + timedelta(days=1)
        workflow = create_test_workflow(
            user=user,
            tasks_count=1,
            due_date=due_date,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'due_date_tsp': None,
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert workflow.due_date is None
        assert response.data['due_date_tsp'] is None

    def test_update__due_date_tsp_invalid_type__validation_error(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(
            user=user,
            tasks_count=1,
        )

        api_client.token_authenticate(user)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'due_date_tsp': 'undefined',
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_GE_0007
        assert response.data['details']['name'] == 'due_date_tsp'
        assert response.data['details']['reason'] == MSG_GE_0007

    def test_update__date_tsp_less_than_current__validation_error(
        self,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        due_date = timezone.now() - timedelta(hours=1)

        workflow = create_test_workflow(
            user=user,
            tasks_count=1,
        )
        api_client.token_authenticate(user)

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'due_date_tsp': due_date.timestamp(),
            },
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_PW_0051
        assert response.data['details']['name'] == 'due_date_tsp'
        assert response.data['details']['reason'] == MSG_PW_0051

    def test_update__change_name_directly__disable_template_name(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        template_name = 'New'
        wf_name_template = '{{ template-name }} {{ date }}'
        template = create_test_template(
            user=user,
            name=template_name,
            tasks_count=1,
            is_active=True,
            wf_name_template=wf_name_template,
        )

        date = timezone.now()
        mocker.patch('django.utils.timezone.now', return_value=date)

        response = api_client.post(f'/templates/{template.id}/run')
        workflow = Workflow.objects.get(pk=response.data['id'])
        new_workflow_name = 'New name'

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'name': new_workflow_name,
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert workflow.name == new_workflow_name
        assert workflow.name_template == new_workflow_name

    def test_update__name_with_system_vars_only__not_update_name(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_owner()
        api_client.token_authenticate(user)
        template_name = 'New'
        wf_name_template = '{{ template-name }} {{ date }}'
        template = create_test_template(
            user=user,
            name=template_name,
            tasks_count=1,
            is_active=True,
            wf_name_template=wf_name_template,
        )

        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC'),
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        response = api_client.post(f'/templates/{template.id}/run')
        workflow = Workflow.objects.get(pk=response.data['id'])

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'is_urgent': True,
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'{template.name} {formatted_date}'
        assert workflow.name_template == f'{template.name} {formatted_date}'

    def test_update__name_with_system_and_kickoff_vars__update_name(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        user_2 = create_test_admin(
            account=account,
            first_name='Feed',
            last_name='Back',
        )
        api_client.token_authenticate(user)
        template = create_test_template(user, tasks_count=1, is_active=True)
        field_api_name = 'field-123'
        field = FieldTemplate.objects.create(
            name='User',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name,
        )
        wf_name_template = 'Feedback from {{%s}} {{ date }}' % field_api_name
        template.wf_name_template = wf_name_template
        template.save()

        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC'),
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    field.api_name: str(user.id),
                },
            },
        )
        workflow = Workflow.objects.get(pk=response.data['id'])

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'kickoff': {
                    field.api_name: str(user_2.id),
                },
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'Feedback from {user_2.name} {formatted_date}'
        assert workflow.name_template == (
            "Feedback from {{%s}} %s" % (field_api_name, formatted_date)
        )

    def test_update__name_with_kickoff_vars_only__ok(
        self,
        api_client,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        user_2 = create_test_admin(
            account=account,
            first_name='Feed',
            last_name='Back',
        )
        api_client.token_authenticate(user)
        template = create_test_template(user, tasks_count=1, is_active=True)
        field_api_name_1 = 'field-1'
        field_api_name_2 = 'field-2'
        field_api_name_3 = 'field-3'
        FieldTemplate.objects.create(
            name='Text',
            type=FieldType.TEXT,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_1,
        )
        FieldTemplate.objects.create(
            name='User',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_2,
        )
        FieldTemplate.objects.create(
            name='Url',
            type=FieldType.URL,
            is_required=False,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_3,
        )
        wf_name_template = 'Feedback: {{%s}} from {{ %s }} Url: {{%s}}' % (
            field_api_name_1,
            field_api_name_2,
            field_api_name_3,
        )
        template.wf_name_template = wf_name_template
        template.save()

        feedback = 'Some shit!'

        response = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    field_api_name_1: feedback,
                    field_api_name_2: str(user.id),
                },
            },
        )
        workflow = Workflow.objects.get(pk=response.data['id'])
        feedback_2 = 'Good thing!'

        # act
        response = api_client.patch(
            f'/workflows/{workflow.id}',
            data={
                'kickoff': {
                    field_api_name_1: feedback_2,
                    field_api_name_2: str(user_2.id),
                },
            },
        )

        # assert
        assert response.status_code == 200
        workflow.refresh_from_db()
        assert workflow.name == (
            f'Feedback: {feedback_2} from {user_2.name} Url: '
        )
        assert workflow.name_template == wf_name_template


class TestUpdatePerformer:

    def test_update__user_field__not_completed_tasks_performers_updated__ok(
        self,
        mocker,
        api_client,
    ):
        """ More about case in https://trello.com/c/9ahwuoL0 """

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        user2 = create_test_admin(account=account)

        field_api_name = 'user-field-1'
        template = create_test_template(
            user=user,
            tasks_count=3,
            is_active=True,
        )
        field = FieldTemplate.objects.create(
            name='Performer',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name,
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_1.raw_performers.all().delete()
        template_task_1.add_raw_performer(
            field=field,
            performer_type=PerformerType.FIELD,
        )
        template_task_2 = template.tasks.get(number=2)
        template_task_2.raw_performers.all().delete()
        template_task_2.add_raw_performer(
            field=field,
            performer_type=PerformerType.FIELD,
        )
        template_task_3 = template.tasks.get(number=3)
        template_task_3.raw_performers.all().delete()
        template_task_3.add_raw_performer(
            field=field,
            performer_type=PerformerType.FIELD,
        )
        api_client.token_authenticate(user)

        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    field_api_name: user.id,
                },
            },
        )
        workflow = Workflow.objects.get(pk=response_run.data['id'])
        task_1 = workflow.tasks.get(number=1)
        response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')

        # act
        response_update = api_client.patch(
            path=f'/workflows/{workflow.id}',
            data={
                'kickoff': {
                    field_api_name: user2.id,
                },
            },
        )
        workflow.refresh_from_db()

        # assert
        assert response_run.status_code == 200
        assert response_complete.status_code == 200
        assert response_update.status_code == 200

        task_1.refresh_from_db()
        assert task_1.is_completed
        assert task_1.raw_performers.count() == 1
        assert task_1.raw_performers.get(
            field__api_name=field_api_name,
            type=PerformerType.FIELD,
        )
        assert task_1.performers.count() == 1
        assert task_1.performers.first().id == user.id

        task_2 = workflow.tasks.get(number=2)
        assert task_2.is_active
        assert task_2.raw_performers.count() == 1
        assert task_2.raw_performers.get(
            field__api_name=field_api_name,
            type=PerformerType.FIELD,
        )
        assert task_2.performers.count() == 1
        assert task_2.performers.first().id == user2.id

        task_3 = workflow.tasks.get(number=3)
        assert task_3.is_pending
        assert task_3.raw_performers.count() == 1
        assert task_3.raw_performers.get(
            field__api_name=field_api_name,
            type=PerformerType.FIELD,
        )
        assert task_3.performers.count() == 0

    def test_update__user_field__next_task_performer_updated(
        self,
        mocker,
        api_client,
    ):
        """ More about case in https://trello.com/c/9ahwuoL0 """

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        account = create_test_account()
        user = create_test_owner(account=account, first_name='First')
        user2 = create_test_admin(account=account, first_name='Last')
        field_api_name = 'user-field-1'
        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        field = FieldTemplate.objects.create(
            name='Performer',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name,
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_1.raw_performers.all().delete()
        template_task_1.add_raw_performer(
            field=field,
            performer_type=PerformerType.FIELD,
        )
        template_task_2 = template.tasks.get(number=2)
        template_task_2.raw_performers.all().delete()
        template_task_2.add_raw_performer(
            field=field,
            performer_type=PerformerType.FIELD,
        )
        api_client.token_authenticate(user)

        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    field_api_name: user.id,
                },
            },
        )
        workflow = Workflow.objects.get(pk=response_run.data['id'])
        response_update = api_client.patch(
            path=f'/workflows/{workflow.id}',
            data={
                'kickoff': {
                    field_api_name: user2.id,
                },
            },
        )
        workflow.refresh_from_db()
        task_1 = workflow.tasks.get(number=1)
        api_client.token_authenticate(user2)

        # act
        response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')

        # assert
        assert response_run.status_code == 200
        assert response_update.status_code == 200
        assert response_complete.status_code == 200

        task_1.refresh_from_db()
        assert task_1.status == TaskStatus.COMPLETED

        task_2 = workflow.tasks.get(number=2)
        assert task_2.status == TaskStatus.ACTIVE
        assert task_2.raw_performers.count() == 1
        assert task_2.raw_performers.get(
            field__api_name=field_api_name,
            type=PerformerType.FIELD,
        )
        assert task_2.performers.count() == 1
        assert task_2.performers.first().id == user2.id

    def test_update__user_field_in_reverted_task__performer_updated(
        self,
        mocker,
        api_client,
    ):
        """ More about case in https://trello.com/c/9ahwuoL0 """

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_returned_webhook.delay',
        )
        account = create_test_account()
        user = create_test_owner(account=account)
        user2 = create_test_admin(account=account)
        field_api_name = 'user-field-1'
        template = create_test_template(
            user=user,
            tasks_count=2,
            is_active=True,
        )
        field = FieldTemplate.objects.create(
            name='Performer',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name,
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_1.raw_performers.all().delete()
        template_task_1.add_raw_performer(
            field=field,
            performer_type=PerformerType.FIELD,
        )
        template_task_2 = template.tasks.get(number=2)
        template_task_2.raw_performers.all().delete()
        template_task_2.add_raw_performer(
            field=field,
            performer_type=PerformerType.FIELD,
        )
        api_client.token_authenticate(user)
        response_run = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    field_api_name: user.id,
                },
            },
        )
        workflow = Workflow.objects.get(pk=response_run.data['id'])
        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)
        response_complete = api_client.post(f'/v2/tasks/{task_1.id}/complete')

        response_update = api_client.patch(
            path=f'/workflows/{workflow.id}',
            data={
                'kickoff': {
                    field_api_name: user2.id,
                },
            },
        )
        text_comment = 'text_comment'
        api_client.token_authenticate(user2)

        # act
        response_revert = api_client.post(
            f'/v2/tasks/{task_2.id}/revert',
            data={
                'comment': text_comment,
            },
        )

        # assert
        assert response_run.status_code == 200
        assert response_update.status_code == 200
        assert response_complete.status_code == 200
        assert response_revert.status_code == 204

        task_1.refresh_from_db()
        assert task_1.raw_performers.count() == 1
        assert task_1.raw_performers.get(
            field__api_name=field_api_name,
            type=PerformerType.FIELD,
        )
        assert task_1.performers.count() == 1
        assert task_1.performers.first().id == user2.id

    def test_update__user_field_invited_transfer__ok(
        self,
        api_client,
    ):

        # arrange
        account_1 = create_test_account(name='invite to')
        account_1_owner = create_test_owner(account=account_1)
        user_to_transfer = create_test_owner(email='transfer@test.test')
        field_api_name = 'user-field-1'
        template = create_test_template(
            user=account_1_owner,
            tasks_count=2,
            is_active=True,
        )
        field = FieldTemplate.objects.create(
            name='Performer',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name,
        )
        template_task_1 = template.tasks.get(number=1)
        template_task_1.raw_performers.all().delete()
        template_task_1.add_raw_performer(
            field=field,
            performer_type=PerformerType.FIELD,
        )
        api_client.token_authenticate(account_1_owner)

        response_run = api_client.post(
            path=f'/templates/{template.id}/run',
            data={
                'kickoff': {
                    'user-field-1': str(account_1_owner.id),
                },
            },
        )
        workflow = Workflow.objects.get(id=response_run.data['id'])
        current_url = 'some_url'
        service = UserInviteService(
            request_user=account_1_owner,
            current_url=current_url,
        )
        service.invite_user(
            email=user_to_transfer.email,
            invited_from=SourceType.EMAIL,
        )
        account_1_new_user = account_1.users.get(email=user_to_transfer.email)

        # act
        response = api_client.patch(
            path=f'/workflows/{workflow.id}',
            data={
                'kickoff': {
                    'user-field-1': str(account_1_new_user.id),
                },
            },
        )

        # assert
        assert response_run.status_code == 200
        assert response.status_code == 200
        task = workflow.tasks.get(number=1)
        assert TaskPerformer.objects.filter(
            user_id=account_1_new_user.id,
            task_id=task.id,
        ).exclude_directly_deleted().exists()
