from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone

from src.processes.enums import TemplateType
from src.processes.models.templates.template import Template
from src.processes.models.workflows.workflow import Workflow
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
    create_test_user,
    create_test_workflow,
    get_workflow_create_data,
)
from src.reports.tasks import (
    send_digest,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


class TestSendDigest:

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
        user = create_test_user()
        user.is_account_owner = True
        user.save()
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        now = timezone.now()
        current_week_monday = (now - timedelta(days=now.weekday())).date()
        date_from = current_week_monday - timedelta(days=7)
        date_to = current_week_monday
        token_patch = mocker.patch(
            'src.accounts.tokens.UnsubscribeEmailToken.'
            'create_token',
        )
        token_patch.return_value = '12345'
        api_client.token_authenticate(user)

        create_1_response = api_client.post('/templates', data=template_data)
        template_1 = Template.objects.get(id=create_1_response.data['id'])
        create_2_response = api_client.post('/templates', data=template_data)
        template_2 = Template.objects.get(id=create_2_response.data['id'])
        create_3_response = api_client.post('/templates', data=template_data)
        system_template = Template.objects.get(id=create_3_response.data['id'])
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
        second_workflow = Workflow.objects.get(
            id=second_workflow.data['id'],
        )
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
        email_service_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_workflows_digest_email',
        )

        # act
        send_digest()

        # assert
        email_service_digest.assert_called_with(
            user=user,
            date_to=date_to - timedelta(days=1),
            date_from=date_from,
            digest={
                'started': 3,
                'in_progress': 3,
                'overdue': 0,
                'completed': 1,
                'templates': [
                    {
                        'started': 2,
                        'in_progress': 2,
                        'overdue': 0,
                        'completed': 1,
                        'template_name': template_2.name,
                        'template_id': template_2.id,
                    },
                    {
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'template_name': template_1.name,
                        'template_id': template_1.id,
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
        user = create_test_user()
        user.is_account_owner = True
        user.last_digest_send_time = timezone.now()
        user.save()
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        now = timezone.now()
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_workflow_started_webhook.delay',
        )
        mocker.patch(
            'src.processes.tasks.webhooks.'
            'send_task_completed_webhook.delay',
        )
        mocker.patch(
            'src.reports.services.workflows.timezone.now',
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
                f'/workflows/{second_workflow.id}/task-complete', data={
                    'task_id': task.id,
                },
            )
        email_service_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_workflows_digest_email',
        )

        # act
        send_digest()

        # assert
        email_service_digest.assert_not_called()

    def test_send__active_temp_has_not_in_progress__not_include_in_digest(
        self,
        mocker,
        api_client,
    ):
        # arrange
        account = create_test_account(logo_lg='https://site.com/logo.jpg')
        user = create_test_user(account=account)
        template_data = get_workflow_create_data(user)
        now = timezone.now()
        current_week_monday = (now - timedelta(days=now.weekday())).date()
        date_from = current_week_monday - timedelta(days=7)
        date_to = current_week_monday
        token_patch = mocker.patch(
            'src.accounts.tokens.UnsubscribeEmailToken.'
            'create_token',
        )
        token_patch.return_value = '12345'

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

        third_template = api_client.post('/templates', data=template_data)
        Template.objects.get(id=third_template.data['id'])

        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        email_service_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_workflows_digest_email',
        )

        # act
        send_digest()

        # assert
        email_service_digest.assert_called_with(
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
                    },
                ],
            },
            logo_lg=account.logo_lg,
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
        token_patch = mocker.patch(
            'src.accounts.tokens.UnsubscribeEmailToken.'
            'create_token',
        )
        token_patch.return_value = '12345'

        api_client.token_authenticate(user)

        api_client.post('/templates', data=template_data)
        api_client.post('/templates', data=template_data)
        template_data['is_active'] = True
        api_client.post('/templates', data=template_data)
        email_service_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_workflows_digest_email',
        )

        # act
        send_digest()

        # assert
        email_service_digest.assert_not_called()

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
        another_user = create_test_user(
            account=user.account,
            email='anothertest@pneumatic.app',
        )
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        another_template_data = get_workflow_create_data(another_user)
        another_template_data['is_active'] = True
        now = timezone.now()
        current_week_monday = (now - timedelta(days=now.weekday())).date()
        date_from = current_week_monday - timedelta(days=7)
        date_to = current_week_monday
        token_patch = mocker.patch(
            'src.accounts.tokens.UnsubscribeEmailToken.'
            'create_token',
        )
        token_patch.return_value = '12345'
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
        email_service_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_workflows_digest_email',
        )

        # act
        send_digest(user_id=user.id)

        # assert
        email_service_digest.assert_called_with(
            user=user,
            date_to=date_to - timedelta(days=1),
            date_from=date_from,
            digest={
                'started': 2,
                'in_progress': 2,
                'overdue': 0,
                'completed': 1,
                'templates': [
                    {
                        'started': 2,
                        'in_progress': 2,
                        'overdue': 0,
                        'completed': 1,
                        'template_name': template_2.name,
                        'template_id': template_2.id,
                    },
                ],
            },
            logo_lg=None,
        )

    def test_send__in_progress__ok(self, mocker):

        """ Bug case when template task api name is same
            in different templates """

        # arrange
        now = timezone.now()
        current_week_monday = (now - timedelta(days=now.weekday())).date()
        date_from = current_week_monday - timedelta(days=7)
        date_to = current_week_monday

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
        email_service_digest = mocker.patch(
            'src.notifications.services.email.EmailService.'
            'send_workflows_digest_email',
        )
        token_patch = mocker.patch(
            'src.accounts.tokens.UnsubscribeEmailToken.'
            'create_token',
        )
        token_patch.return_value = '12345'

        # act
        send_digest(user_id=user.id)

        # assert
        email_service_digest.assert_called_with(
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
                    },
                    {
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'template_name': template.name,
                        'template_id': template_2.id,
                    },
                ],
            },
            logo_lg=None,
        )
