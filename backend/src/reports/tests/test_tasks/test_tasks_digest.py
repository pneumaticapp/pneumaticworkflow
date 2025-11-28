from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.authentication.enums import AuthTokenType
from src.processes.enums import TemplateType
from src.processes.models.templates.template import Template
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.tasks.performers import (
    TaskPerformersService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
    create_test_user,
    create_test_workflow,
    get_workflow_create_data,
)
from src.reports.tasks import (
    send_tasks_digest,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


class TestSendTasksDigest:

    def test_send(self, mocker, api_client):

        # arrange
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        user = create_test_user(is_account_owner=True)
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        mocker.patch(
            'src.reports.services.tasks.timezone.now',
            return_value=now,
        )
        api_client.token_authenticate(user)

        template_1 = api_client.post('/templates', data=template_data)
        template_1 = Template.objects.get(id=template_1.data['id'])
        template_2 = api_client.post('/templates', data=template_data)
        template_2 = Template.objects.get(id=template_2.data['id'])
        system_template = api_client.post('/templates', data=template_data)
        system_template = Template.objects.get(id=system_template.data['id'])
        system_template.type = TemplateType.ONBOARDING_NON_ADMIN
        system_template.save()

        api_client.post(
            f'/templates/{template_1.id}/run',
            data={
                'name': 'First workflow',
            },
        )
        second_workflow = api_client.post(
            f'/templates/{template_2.id}/run',
            data={
                'name': 'Second workflow',
            },
        )
        api_client.post(
            f'/templates/{system_template.id}/run',
            data={
                'name': 'Onboarding',
            },
        )
        second_workflow = Workflow.objects.get(id=second_workflow.data['id'])
        api_client.post(
            f'/templates/{template_2.id}/run',
            data={
                'name': 'Third workflow',
            },
        )

        for task in second_workflow.tasks.order_by('number').all():
            api_client.post(
                f'/workflows/{second_workflow.id}/task-complete', data={
                    'task_id': task.id,
                },
            )

        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        second_workflow.refresh_from_db()
        second_workflow.status_updated = date_from + timedelta(days=2)
        second_workflow.date_completed = date_to - timedelta(days=1)
        second_workflow.save()
        email_service_tasks_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_tasks_digest_email',
        )

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        ft_first_task = template_1.tasks.get(number=1)
        st_first_task = template_2.tasks.get(number=1)
        st_second_task = template_2.tasks.get(number=2)
        st_third_task = template_2.tasks.get(number=3)
        email_service_tasks_digest.assert_called_with(
            user=user,
            date_to=date_to - timedelta(days=1),
            date_from=date_from,
            digest={
                'started': 5,
                'in_progress': 5,
                'overdue': 0,
                'completed': 3,
                'templates': [
                    {
                        'started': 4,
                        'in_progress': 4,
                        'overdue': 0,
                        'completed': 3,
                        'template_name': template_2.name,
                        'template_id': template_2.id,
                        'tasks': [
                            {
                                'task_id': st_first_task.id,
                                'task_name': 'First Test',
                                'started': 2,
                                'in_progress': 2,
                                'overdue': 0,
                                'completed': 1,
                            },
                            {
                                'task_id': st_second_task.id,
                                'task_name': 'Second',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 1,
                            },
                            {
                                'task_id': st_third_task.id,
                                'task_name': 'Third',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 1,
                            },
                        ],
                    },
                    {
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'template_name': template_1.name,
                        'template_id': template_1.id,
                        'tasks': [
                            {
                                'task_id': ft_first_task.id,
                                'task_name': 'First Test',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 0,
                            },
                        ],
                    },
                ],
            },
            logo_lg=None,
        )

    def test_send__deleted_performer__no_sent(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account()
        template_owner = create_test_user(account=account)
        user_performer = create_test_user(
            email='test@test.test',
            account=account,
        )
        api_client.token_authenticate(template_owner)
        template = create_test_template(
            user=template_owner,
            tasks_count=1,
            is_active=True,
        )
        task_template = template.tasks.first()
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        datetime_patch = mocker.patch(
            'src.reports.services.tasks.timezone.now',
            return_value=now,
        )
        workflow = create_test_workflow(
            user=template_owner,
            template=template,
        )
        workflow.date_created = date_from + timedelta(days=2)
        workflow.save()

        task = workflow.tasks.get(number=1)
        task.performers.add(user_performer)
        TaskPerformersService.delete_performer(
            task=task,
            request_user=template_owner,
            user_key=user_performer.id,
            run_actions=False,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
        )
        email_service_tasks_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_tasks_digest_email',
        )

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        datetime_patch.assert_called()
        email_service_tasks_digest.assert_called_once_with(
            user=template_owner,
            date_to=date_to - timedelta(days=1),
            date_from=date_from,
            digest={
                'started': 1,
                'in_progress': 1,
                'overdue': 0,
                'completed': 0,
                'templates': [
                    {
                        'template_id': template.id,
                        'template_name': template.name,
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'tasks': [
                            {
                                'task_id': task_template.id,
                                'task_name': task_template.name,
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 0,
                            },
                        ],
                    },
                ],
            },
            logo_lg=None,
        )

    def test_send__already_sent__not_sent_again(
        self,
        api_client,
        mocker,
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
        now = timezone.now()
        user = create_test_user()
        user.is_account_owner = True
        user.last_tasks_digest_send_time = now - timedelta(days=1)
        user.save()
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        mocker.patch(
            'src.reports.services.tasks.timezone.now',
            return_value=now,
        )

        api_client.token_authenticate(user)

        template_1 = api_client.post('/templates', data=template_data)
        template_1 = Template.objects.get(id=template_1.data['id'])
        template_2 = api_client.post('/templates', data=template_data)
        template_2 = Template.objects.get(id=template_2.data['id'])

        api_client.post(
            f'/templates/{template_1.id}/run',
            data={
                'name': 'First workflow',
            },
        )
        second_workflow = api_client.post(
            f'/templates/{template_2.id}/run',
            data={
                'name': 'Second workflow',
            },
        )
        second_workflow = Workflow.objects.get(id=second_workflow.data['id'])
        api_client.post(
            f'/templates/{template_2.id}/run',
            data={
                'name': 'Third workflow',
            },
        )
        Workflow.objects.on_account(user.account_id).update(
            date_created=F('date_created') - timedelta(weeks=1),
        )

        for task in second_workflow.tasks.order_by('number').all():
            api_client.post(
                f'/workflows/{second_workflow.id}/task-complete',
                data={
                    'task_id': task.id,
                },
            )
        email_service_tasks_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_tasks_digest_email',
        )

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        email_service_tasks_digest.assert_not_called()

    def test_send__active_temp_has_not_in_progress__not_include_in_digest(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        user.is_account_owner = True
        user.save()
        template_data = get_workflow_create_data(user)
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        mocker.patch(
            'src.reports.services.tasks.timezone.now',
            return_value=now,
        )
        api_client.token_authenticate(user)

        api_client.post('/templates', data=template_data)
        template_data['is_active'] = True
        template_2 = api_client.post('/templates', data=template_data)
        template_2 = Template.objects.get(id=template_2.data['id'])

        api_client.post(
            f'/templates/{template_2.id}/run',
            data={
                'name': 'Second workflow',
            },
        )
        template_2.is_active = False
        template_2.save()

        template_3 = api_client.post('/templates', data=template_data)
        Template.objects.get(id=template_3.data['id'])

        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        email_service_tasks_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_tasks_digest_email',
        )

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        task_1 = template_2.tasks.get(number=1)
        email_service_tasks_digest.assert_called_with(
            user=user,
            date_to=date_to - timedelta(days=1),
            date_from=date_from,
            digest={
                'started': 1,
                'in_progress': 1,
                'overdue': 0,
                'completed': 0,
                'templates': [
                    {
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'template_name': template_2.name,
                        'template_id': template_2.id,
                        'tasks': [
                            {
                                'task_id': task_1.id,
                                'task_name': 'First Test',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 0,
                            },
                        ],
                    },
                ],
            },
            logo_lg=None,
        )

    def test_send__total_in_progress_is_nil__not_sent(
        self,
        mocker,
        api_client,
    ):
        # arrange

        user = create_test_user()
        user.is_account_owner = True
        user.save()
        template_data = get_workflow_create_data(user)
        api_client.token_authenticate(user)

        api_client.post('/templates', data=template_data)
        api_client.post('/templates', data=template_data)
        template_data['is_active'] = True
        api_client.post('/templates', data=template_data)
        email_service_tasks_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_tasks_digest_email',
        )

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        email_service_tasks_digest.assert_not_called()

    def test_send__specified_user__send_only_for(
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
        user = create_test_user()
        user.account.billing_plan = BillingPlanType.PREMIUM
        user.account.save()
        another_user = create_test_user(
            account=user.account,
            email='anothertest@pneumatic.app',
        )
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        another_template_data = get_workflow_create_data(another_user)
        another_template_data['is_active'] = True
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        mocker.patch(
            'src.reports.services.tasks.timezone.now',
            return_value=now,
        )
        api_client.token_authenticate(another_user)

        template_1 = api_client.post(
            '/templates',
            data=another_template_data,
        )
        template_1 = Template.objects.get(id=template_1.data['id'])
        api_client.post(
            f'/templates/{template_1.id}/run',
            data={
                'name': 'First workflow',
                'kickoff': {
                    'string-field-1': 'Test',
                },
            },
        )

        api_client.token_authenticate(user)
        template_2 = api_client.post('/templates', data=template_data)
        template_2 = Template.objects.get(id=template_2.data['id'])
        system_template = api_client.post('/templates', data=template_data)
        system_template = Template.objects.get(id=system_template.data['id'])
        system_template.type = TemplateType.ONBOARDING_NON_ADMIN
        system_template.save()

        second_workflow = api_client.post(
            f'/templates/{template_2.id}/run',
            data={
                'name': 'Second workflow',
            },
        )
        api_client.post(
            f'/templates/{system_template.id}/run',
            data={
                'name': 'Onboarding',
            },
        )
        second_workflow = Workflow.objects.get(id=second_workflow.data['id'])
        api_client.post(
            f'/templates/{template_2.id}/run',
            data={
                'name': 'Third workflow',
            },
        )

        for task in second_workflow.tasks.order_by('number').all():
            api_client.post(
                f'/workflows/{second_workflow.id}/task-complete',
                data={
                    'task_id': task.id,
                },
            )

        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        second_workflow.refresh_from_db()
        second_workflow.status_updated = date_from + timedelta(days=2)
        second_workflow.date_completed = date_to - timedelta(days=1)
        second_workflow.save()
        email_service_tasks_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_tasks_digest_email',
        )

        # act
        send_tasks_digest(user_id=user.id, fetch_size=1)

        # assert
        task_1 = template_2.tasks.get(number=1)
        task_2 = template_2.tasks.get(number=2)
        task_3 = template_2.tasks.get(number=3)
        email_service_tasks_digest.assert_called_with(
            user=user,
            date_to=date_to - timedelta(days=1),
            date_from=date_from,
            digest={
                'started': 4,
                'in_progress': 4,
                'overdue': 0,
                'completed': 3,
                'templates': [
                    {
                        'started': 4,
                        'in_progress': 4,
                        'overdue': 0,
                        'completed': 3,
                        'template_name': template_2.name,
                        'template_id': template_2.id,
                        'tasks': [
                            {
                                'task_id': task_1.id,
                                'task_name': 'First Test',
                                'started': 2,
                                'in_progress': 2,
                                'overdue': 0,
                                'completed': 1,
                            },
                            {
                                'task_id': task_2.id,
                                'task_name': 'Second',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 1,
                            },
                            {
                                'task_id': task_3.id,
                                'task_name': 'Third',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 1,
                            },
                        ],
                    },
                ],
            },
            logo_lg=None,
        )

    def test_send__same_task_api_name_in_different_templates__ok(
        self,
        mocker,
        api_client,
    ):

        """ Bug case when template task api name is same
            in different templates """

        # arrange
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        mocker.patch(
            'src.reports.services.tasks.timezone.now',
            return_value=now,
        )

        user = create_test_user()
        template = create_test_template(user=user, tasks_count=1)
        task = template.tasks.first()
        template_2 = create_test_template(user, tasks_count=1)
        task_2 = template_2.tasks.first()
        task_2.api_name = task.api_name
        task_2.save()
        create_test_workflow(user, template=template)
        create_test_workflow(user, template=template_2)
        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        email_service_tasks_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_tasks_digest_email',
        )
        api_client.token_authenticate(user)

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        email_service_tasks_digest.assert_called_with(
            user=user,
            date_to=date_to - timedelta(days=1),
            date_from=date_from,
            digest={
                'started': 2,
                'in_progress': 2,
                'overdue': 0,
                'completed': 0,
                'templates': [
                    {
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'template_name': template.name,
                        'template_id': template.id,
                        'tasks': [
                            {
                                'task_id': task.id,
                                'task_name': task.name,
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 0,
                            },
                        ],
                    },
                    {
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'template_name': template_2.name,
                        'template_id': template_2.id,
                        'tasks': [
                            {
                                'task_id': task_2.id,
                                'task_name': task_2.name,
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 0,
                            },
                        ],
                    },
                ],
            },
            logo_lg=None,
        )
