from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.models import (
    Workflow,
    Template,
)
from pneumatic_backend.reports.tasks import (
    send_tasks_digest,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    get_workflow_create_data,
    create_test_template,
    create_test_account
)
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.processes.enums import TemplateType


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
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        user = create_test_user(is_account_owner=True)
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        mocker.patch(
            'pneumatic_backend.reports.services.tasks.timezone.now',
            return_value=now
        )
        api_client.token_authenticate(user)

        first_template = api_client.post('/templates', data=template_data)
        first_template = Template.objects.get(id=first_template.data['id'])
        second_template = api_client.post('/templates', data=template_data)
        second_template = Template.objects.get(id=second_template.data['id'])
        system_template = api_client.post('/templates', data=template_data)
        system_template = Template.objects.get(id=system_template.data['id'])
        system_template.type = TemplateType.ONBOARDING_NON_ADMIN
        system_template.save()

        api_client.post(
            f'/templates/{first_template.id}/run',
            data={
                'name': 'First workflow'
            }
        )
        second_workflow = api_client.post(
            f'/templates/{second_template.id}/run',
            data={
                'name': 'Second workflow'
            }
        )
        api_client.post(
            f'/templates/{system_template.id}/run',
            data={
                'name': 'Onboarding'
            }
        )
        second_workflow = Workflow.objects.get(id=second_workflow.data['id'])
        api_client.post(
            f'/templates/{second_template.id}/run',
            data={
                'name': 'Third workflow'
            }
        )

        for task in second_workflow.tasks.order_by('number').all():
            api_client.post(
                f'/workflows/{second_workflow.id}/task-complete', data={
                    'task_id': task.id
                }
            )

        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        second_workflow.refresh_from_db()
        second_workflow.status_updated = date_from + timedelta(days=2)
        second_workflow.date_completed = date_to - timedelta(days=1)
        second_workflow.save()
        email_service_tasks_digest = mocker.patch(
            'pneumatic_backend.services.email.EmailService.'
            'send_tasks_digest_email'
        )

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        ft_first_task = first_template.tasks.get(number=1)
        st_first_task = second_template.tasks.get(number=1)
        st_second_task = second_template.tasks.get(number=2)
        st_third_task = second_template.tasks.get(number=3)
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
                        'template_name': second_template.name,
                        'template_id': second_template.id,
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
                            }
                        ]
                    },
                    {
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'template_name': first_template.name,
                        'template_id': first_template.id,
                        'tasks': [
                            {
                                'task_id': ft_first_task.id,
                                'task_name': 'First Test',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 0,
                            }
                        ],
                    },
                ]
            },
            logo_lg=None,
        )

    def test_send__deleted_performer__no_sent(
        self,
        mocker,
        api_client,
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        template_owner = create_test_user(account=account)
        user_performer = create_test_user(
            email='test@test.test',
            account=account
        )
        api_client.token_authenticate(template_owner)
        template = create_test_template(
            user=template_owner,
            tasks_count=1,
            is_active=True
        )
        task_template = template.tasks.first()
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        datetime_patch = mocker.patch(
            'pneumatic_backend.reports.services.tasks.timezone.now',
            return_value=now
        )
        workflow = create_test_workflow(
            user=template_owner,
            template=template
        )
        workflow.date_created = date_from + timedelta(days=2)
        workflow.save()

        task = workflow.current_task_instance
        task.performers.add(user_performer)
        TaskPerformersService.delete_performer(
            task=task,
            request_user=template_owner,
            user_key=user_performer.id,
            run_actions=False
        )
        email_service_tasks_digest = mocker.patch(
            'pneumatic_backend.services.email.EmailService.'
            'send_tasks_digest_email'
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
                                'completed': 0
                            }
                        ]
                    }
                ]
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
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
        )
        now = timezone.now()
        user = create_test_user()
        user.is_account_owner = True
        user.last_tasks_digest_send_time = now - timedelta(days=1)
        user.save()
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        mocker.patch(
            'pneumatic_backend.reports.services.tasks.timezone.now',
            return_value=now
        )

        api_client.token_authenticate(user)

        first_template = api_client.post('/templates', data=template_data)
        first_template = Template.objects.get(id=first_template.data['id'])
        second_template = api_client.post('/templates', data=template_data)
        second_template = Template.objects.get(id=second_template.data['id'])

        api_client.post(
            f'/templates/{first_template.id}/run',
            data={
                'name': 'First workflow'
            }
        )
        second_workflow = api_client.post(
            f'/templates/{second_template.id}/run',
            data={
                'name': 'Second workflow'
            }
        )
        second_workflow = Workflow.objects.get(id=second_workflow.data['id'])
        api_client.post(
            f'/templates/{second_template.id}/run',
            data={
                'name': 'Third workflow'
            }
        )
        Workflow.objects.on_account(user.account_id).update(
            date_created=F('date_created') - timedelta(weeks=1)
        )

        for task in second_workflow.tasks.order_by('number').all():
            api_client.post(
                f'/workflows/{second_workflow.id}/task-complete',
                data={
                    'task_id': task.id
                }
            )
        email_service_tasks_digest = mocker.patch(
            'pneumatic_backend.services.email.EmailService.'
            'send_tasks_digest_email'
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
            'pneumatic_backend.reports.services.tasks.timezone.now',
            return_value=now
        )
        api_client.token_authenticate(user)

        api_client.post('/templates', data=template_data)
        template_data['is_active'] = True
        second_template = api_client.post('/templates', data=template_data)
        second_template = Template.objects.get(id=second_template.data['id'])

        api_client.post(
            f'/templates/{second_template.id}/run',
            data={
                'name': 'Second workflow'
            }
        )
        second_template.is_active = False
        second_template.save()

        third_template = api_client.post('/templates', data=template_data)
        Template.objects.get(id=third_template.data['id'])

        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        email_service_tasks_digest = mocker.patch(
            'pneumatic_backend.services.email.EmailService.'
            'send_tasks_digest_email'
        )

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        first_task = second_template.tasks.get(number=1)
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
                        'template_name': second_template.name,
                        'template_id': second_template.id,
                        'tasks': [
                            {
                                'task_id': first_task.id,
                                'task_name': 'First Test',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 0,
                            }
                        ]
                    },
                ]
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
            'pneumatic_backend.services.email.EmailService.'
            'send_tasks_digest_email'
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
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'pneumatic_backend.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay'
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
            'pneumatic_backend.reports.services.tasks.timezone.now',
            return_value=now
        )
        api_client.token_authenticate(another_user)

        first_template = api_client.post(
            '/templates',
            data=another_template_data,
        )
        first_template = Template.objects.get(id=first_template.data['id'])
        api_client.post(
            f'/templates/{first_template.id}/run',
            data={
                'name': 'First workflow',
                'kickoff': {
                    'string-field-1': 'Test',
                }
            }
        )

        api_client.token_authenticate(user)
        second_template = api_client.post('/templates', data=template_data)
        second_template = Template.objects.get(id=second_template.data['id'])
        system_template = api_client.post('/templates', data=template_data)
        system_template = Template.objects.get(id=system_template.data['id'])
        system_template.type = TemplateType.ONBOARDING_NON_ADMIN
        system_template.save()

        second_workflow = api_client.post(
            f'/templates/{second_template.id}/run',
            data={
                'name': 'Second workflow'
            }
        )
        api_client.post(
            f'/templates/{system_template.id}/run',
            data={
                'name': 'Onboarding'
            }
        )
        second_workflow = Workflow.objects.get(id=second_workflow.data['id'])
        api_client.post(
            f'/templates/{second_template.id}/run',
            data={
                'name': 'Third workflow'
            }
        )

        for task in second_workflow.tasks.order_by('number').all():
            api_client.post(
                f'/workflows/{second_workflow.id}/task-complete',
                data={
                    'task_id': task.id
                }
            )

        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        second_workflow.refresh_from_db()
        second_workflow.status_updated = date_from + timedelta(days=2)
        second_workflow.date_completed = date_to - timedelta(days=1)
        second_workflow.save()
        email_service_tasks_digest = mocker.patch(
            'pneumatic_backend.services.email.EmailService.'
            'send_tasks_digest_email'
        )

        # act
        send_tasks_digest(user_id=user.id, fetch_size=1)

        # assert
        first_task = second_template.tasks.get(number=1)
        second_task = second_template.tasks.get(number=2)
        third_task = second_template.tasks.get(number=3)
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
                        'template_name': second_template.name,
                        'template_id': second_template.id,
                        'tasks': [
                            {
                                'task_id': first_task.id,
                                'task_name': 'First Test',
                                'started': 2,
                                'in_progress': 2,
                                'overdue': 0,
                                'completed': 1,
                            },
                            {
                                'task_id': second_task.id,
                                'task_name': 'Second',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 1,
                            },
                            {
                                'task_id': third_task.id,
                                'task_name': 'Third',
                                'started': 1,
                                'in_progress': 1,
                                'overdue': 0,
                                'completed': 1,
                            },
                        ]
                    },
                ]
            },
            logo_lg=None,
        )

    def test_send__same_task_api_name_in_different_templates__ok(
        self,
        mocker,
        api_client
    ):

        """ Bug case when template task api name is same
            in different templates """

        # arrange
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        mocker.patch(
            'pneumatic_backend.reports.services.tasks.timezone.now',
            return_value=now
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
            'pneumatic_backend.services.email.EmailService.'
            'send_tasks_digest_email'
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
                            }
                        ]
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
                            }
                        ]
                    },
                ]
            },
            logo_lg=None,
        )
