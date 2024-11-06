# pylint:disable=redefined-outer-name
# pylint:disable=unused-argument
from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.db.models import F
from django.utils import timezone

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.tasks.tasks import complete_tasks
from pneumatic_backend.processes.models import (
    Workflow,
    Template,
)
from pneumatic_backend.processes.services.versioning.schemas import (
    TemplateSchemaV1,
)
from pneumatic_backend.processes.services.versioning.versioning import (
    TemplateVersioningService,
)
from pneumatic_backend.processes.tasks.delay import (
    continue_delayed_workflows,
)
from pneumatic_backend.processes.tasks.digest import (
    send_digest,
    send_tasks_digest,
)
from pneumatic_backend.processes.tasks.update_workflow import (
    update_workflows,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    get_workflow_create_data,
    create_test_template,
    create_test_account
)
from pneumatic_backend.processes.enums import (
    PerformerType,
)
from pneumatic_backend.processes.api_v2.services.task.performers import (
    TaskPerformersService
)
from pneumatic_backend.processes.enums import TemplateType
from pneumatic_backend.processes.utils.workflows import (
    resume_delayed_workflows
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


@pytest.fixture
def email_service_digest(mocker):
    return mocker.patch(
        'pneumatic_backend.services.email.EmailService.'
        'send_workflows_digest_email'
    )


@pytest.fixture
def email_service_tasks_digest(mocker):
    return mocker.patch(
        'pneumatic_backend.services.email.EmailService.'
        'send_tasks_digest_email'
    )


class TestContinueDelayedWorkflows:

    def test_continue_delayed_workflows__ok(self, mocker):

        # arrange
        periodic_lock_mock = mocker.patch(
            'pneumatic_backend.celery.periodic_lock'
        )
        periodic_lock_mock.__enter__.return_value = True
        resume_delayed_workflows_mock = mocker.patch(
            'pneumatic_backend.processes.tasks.delay.resume_delayed_workflows'
        )

        # act
        continue_delayed_workflows()

        # assert
        resume_delayed_workflows_mock.assert_called_once()

    def test_resume_delayed_workflows__delay_expired__resume(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'template_owners': [user.id],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'delay': '01:00:00',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    }
                ]
            }
        )

        template_id = response_create.data['id']
        response_run = api_client.post(
            path=f'/templates/{template_id}/run',
            data={'name': 'Test template'}
        )
        workflow_id = response_run.data['id']
        workflow = Workflow.objects.get(id=workflow_id)

        response_complete = api_client.post(
            path=f'/workflows/{workflow_id}/task-complete',
            data={'task_id': workflow.current_task_instance.id}
        )
        workflow.refresh_from_db()
        current_task = workflow.tasks.get(number=2)
        delay = current_task.get_active_delay()
        delay.start_date = (timezone.now() - timedelta(days=2))
        delay.save()

        service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None
        )
        resume_workflow_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.WorkflowActionService.resume_workflow'
        )
        workflow.refresh_from_db()

        # act
        resume_delayed_workflows()

        # assert
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        workflow.refresh_from_db()
        service_init_mock.assert_called_once_with(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER
        )
        resume_workflow_mock.assert_called_once_with(workflow)

    def test_resume_delayed_workflows__delay_not_expired__not_resume(
        self,
        mocker,
        api_client
    ):

        # arrange
        user = create_test_user()
        api_client.token_authenticate(user)

        # act
        response_create = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'template_owners': [user.id],
                'kickoff': {},
                'is_active': True,
                'tasks': [
                    {
                        'number': 1,
                        'name': 'First step',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    },
                    {
                        'number': 2,
                        'name': 'Second step',
                        'delay': '01:00:00',
                        'raw_performers': [
                            {
                                'type': PerformerType.USER,
                                'source_id': user.id
                            }
                        ]
                    }
                ]
            }
        )

        template_id = response_create.data['id']
        response_run = api_client.post(
            path=f'/templates/{template_id}/run',
            data={'name': 'Test template'}
        )
        workflow_id = response_run.data['id']
        workflow = Workflow.objects.get(id=workflow_id)

        response_complete = api_client.post(
            path=f'/workflows/{workflow_id}/task-complete',
            data={'task_id': workflow.current_task_instance.id}
        )
        workflow.refresh_from_db()

        service_init_mock = mocker.patch.object(
            WorkflowActionService,
            attribute='__init__',
            return_value=None
        )
        resume_workflow_mock = mocker.patch(
            'pneumatic_backend.processes.services.'
            'workflow_action.WorkflowActionService.resume_workflow'
        )
        workflow.refresh_from_db()

        # act
        resume_delayed_workflows()

        # assert
        assert response_run.status_code == 200
        assert response_complete.status_code == 204
        workflow.refresh_from_db()
        service_init_mock.assert_not_called()
        resume_workflow_mock.assert_not_called()


class TestSendDigest:

    def test_send(self, mocker, api_client, email_service_digest):
        # arrange
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
            'pneumatic_backend.accounts.tokens.UnsubscribeEmailToken.'
            'create_token'
        )
        token_patch.return_value = '12345'
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
        second_workflow = Workflow.objects.get(
            id=second_workflow.data['id']
        )
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
                        'template_name': second_template.name,
                        'template_id': second_template.id,
                    },
                    {
                        'started': 1,
                        'in_progress': 1,
                        'overdue': 0,
                        'completed': 0,
                        'template_name': first_template.name,
                        'template_id': first_template.id,
                    },
                ]
            },
            logo_lg=None,
        )

    def test_send__already_sent__not_sent_again(
        self,
        api_client,
        mocker,
        email_service_digest,
    ):
        # arrange
        user = create_test_user()
        user.is_account_owner = True
        user.last_digest_send_time = timezone.now()
        user.save()
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        now = timezone.now()
        datetime_patch = mocker.patch(
            'pneumatic_backend.processes.tasks.digest.'
            'timezone.now'
        )
        datetime_patch.return_value = now

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
                f'/workflows/{second_workflow.id}/task-complete', data={
                    'task_id': task.id
                }
            )

        # act
        send_digest()

        # assert
        email_service_digest.assert_not_called()

    def test_send__active_temp_has_not_in_progress__not_include_in_digest(
        self,
        mocker,
        api_client,
        email_service_digest,
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
            'pneumatic_backend.accounts.tokens.UnsubscribeEmailToken.'
            'create_token'
        )
        token_patch.return_value = '12345'

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
                        'template_name': second_template.name,
                        'template_id': second_template.id,
                    },
                ]
            },
            logo_lg=account.logo_lg,
        )

    def test_send__total_in_progress_is_nil__not_sent(
        self,
        mocker,
        api_client,
        email_service_digest,
    ):
        # arrange
        user = create_test_user()
        user.is_account_owner = True
        user.save()
        template_data = get_workflow_create_data(user)
        token_patch = mocker.patch(
            'pneumatic_backend.accounts.tokens.UnsubscribeEmailToken.'
            'create_token'
        )
        token_patch.return_value = '12345'

        api_client.token_authenticate(user)

        api_client.post('/templates', data=template_data)
        api_client.post('/templates', data=template_data)
        template_data['is_active'] = True
        api_client.post('/templates', data=template_data)

        # act
        send_digest()

        # assert
        email_service_digest.assert_not_called()

    def test_send__specified_user__send_only_for(
        self,
        mocker,
        api_client,
        email_service_digest,
    ):
        # arrange
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
        current_week_monday = (now - timedelta(days=now.weekday())).date()
        date_from = current_week_monday - timedelta(days=7)
        date_to = current_week_monday
        token_patch = mocker.patch(
            'pneumatic_backend.accounts.tokens.UnsubscribeEmailToken.'
            'create_token'
        )
        token_patch.return_value = '12345'
        api_client.token_authenticate(another_user)

        first_template = api_client.post(
            '/templates',
            data=another_template_data,
        )
        first_template = Template.objects.get(id=first_template.data['id'])
        api_client.post(
            f'/templates/{first_template.id}/run',
            data={
                'name': 'First workflow'
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
                        'template_name': second_template.name,
                        'template_id': second_template.id,
                    },
                ]
            },
            logo_lg=None,
        )

    def test_send__payment_card_not_provided__not_sent(
        self,
        mocker,
        api_client,
        email_service_digest
    ):
        # arrange
        account = create_test_account(
            payment_card_provided=False
        )
        user = create_test_user(
            is_account_owner=True,
            account=account
        )

        now = timezone.now()
        current_week_monday = (now - timedelta(days=now.weekday())).date()
        date_from = current_week_monday - timedelta(days=7)
        date_to = current_week_monday
        token_patch = mocker.patch(
            'pneumatic_backend.accounts.tokens.UnsubscribeEmailToken.'
            'create_token'
        )
        token_patch.return_value = '12345'
        api_client.token_authenticate(user)
        second_workflow = create_test_workflow(user=user)
        Workflow.objects.on_account(user.account_id).update(
            date_created=date_from + timedelta(days=2),
        )
        second_workflow.refresh_from_db()
        second_workflow.status_updated = date_from + timedelta(days=2)
        second_workflow.date_completed = date_to - timedelta(days=1)
        second_workflow.save()

        # act
        send_digest()

        # assert
        email_service_digest.assert_not_called()


class TestSendTasksDigest:

    def test_send(self, mocker, api_client, email_service_tasks_digest):
        # arrange
        user = create_test_user(is_account_owner=True)
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now

        datetime_patch = mocker.patch(
            'pneumatic_backend.processes.tasks.digest.'
            'timezone.now'
        )
        datetime_patch.return_value = now
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
        email_service_tasks_digest
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
            'pneumatic_backend.processes.tasks.digest.'
            'timezone.now',
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
        email_service_tasks_digest,
    ):
        # arrange
        now = timezone.now()
        user = create_test_user()
        user.is_account_owner = True
        user.last_tasks_digest_send_time = now - timedelta(days=1)
        user.save()
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        datetime_patch = mocker.patch(
            'pneumatic_backend.processes.tasks.digest.'
            'timezone.now'
        )
        datetime_patch.return_value = now

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
                f'/workflows/{second_workflow.id}/task-complete', data={
                    'task_id': task.id
                }
            )

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        email_service_tasks_digest.assert_not_called()

    def test_send__active_temp_has_not_in_progress__not_include_in_digest(
        self,
        mocker,
        api_client,
        email_service_tasks_digest,
    ):
        # arrange
        user = create_test_user()
        user.is_account_owner = True
        user.save()
        template_data = get_workflow_create_data(user)
        now = timezone.now()
        date_from = now.date() - timedelta(days=7)
        date_to = now
        datetime_patch = mocker.patch(
            'pneumatic_backend.processes.tasks.digest.'
            'timezone.now'
        )
        datetime_patch.return_value = now
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
        api_client,
        email_service_tasks_digest,
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

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        email_service_tasks_digest.assert_not_called()

    def test_send__specified_user__send_only_for(
        self,
        mocker,
        api_client,
        email_service_tasks_digest,
    ):
        # arrange
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
        datetime_patch = mocker.patch(
            'pneumatic_backend.processes.tasks.digest.'
            'timezone.now'
        )
        datetime_patch.return_value = now
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

    def test_send__payment_card_not_provided__not_sent(
        self,
        api_client,
        email_service_tasks_digest,
    ):
        # arrange
        account = create_test_account(
            payment_card_provided=False
        )
        user = create_test_user(
            account=account,
            is_account_owner=True
        )
        template_data = get_workflow_create_data(user)
        template_data['is_active'] = True
        create_test_workflow(user=user)
        api_client.token_authenticate(user)

        # act
        send_tasks_digest(fetch_size=1)

        # assert
        email_service_tasks_digest.assert_not_called()


class TestUpdateWorkflow:

    def test_update(self, api_client):

        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True
        )
        api_client.token_authenticate(user)
        workflow_id = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow'
            }
        ).data['id']
        first_task = template.tasks.get(number=1)
        first_task.name = 'New task name'
        first_task.save()
        template.version += 1
        template.save()
        TemplateVersioningService(TemplateSchemaV1).save(template)

        update_workflows(
            template_id=template.id,
            version=template.version,
            updated_by=user.id,
            auth_type=AuthTokenType.USER,
            is_superuser=True
        )

        workflow = Workflow.objects.get(id=workflow_id)

        assert workflow.version == template.version
        assert workflow.current_task_instance.name == 'New task name'

    def test_update__template_version_difference(self, api_client):
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True
        )
        api_client.token_authenticate(user)
        workflow_id = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow'
            }
        ).data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        version = workflow.version
        task_name = workflow.current_task_instance.name

        first_task = template.tasks.get(number=1)
        first_task.name = 'New task name'
        first_task.save()
        template.version += 1
        template.save()
        TemplateVersioningService(TemplateSchemaV1).save(template)

        update_workflows(
            template_id=template.id,
            version=template.version-1,
            updated_by=user.id,
            auth_type=AuthTokenType.USER,
            is_superuser=True
        )
        workflow.refresh_from_db()

        assert workflow.version == version
        assert workflow.current_task_instance.name == task_name

    def test_update__process_version_difference(self, api_client):
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True
        )
        api_client.token_authenticate(user)
        workflow_id = api_client.post(
            f'/templates/{template.id}/run',
            data={
                'name': 'Test workflow'
            }
        ).data['id']
        workflow = Workflow.objects.get(id=workflow_id)
        workflow.version += 5
        workflow.save()
        version = workflow.version
        task_name = workflow.current_task_instance.name

        first_task = template.tasks.get(number=1)
        first_task.name = 'New task name'
        first_task.save()
        template.version += 1
        template.save()
        TemplateVersioningService(TemplateSchemaV1).save(template)

        update_workflows(
            template_id=template.id,
            version=template.version,
            updated_by=user.id,
            auth_type=AuthTokenType.USER,
            is_superuser=True
        )
        workflow.refresh_from_db()

        assert workflow.version == version
        assert workflow.current_task_instance.name == task_name


class TestCompleteTasks:

    def test_call(self, api_client):

        # arrange
        user = create_test_user()
        second_user = create_test_user(
            email='second_user@pneumatic.app',
            account=user.account,
        )
        workflow = create_test_workflow(
            user=user
        )
        second_workflow = create_test_workflow(
            user=user
        )
        second_workflow_first_task = second_workflow.current_task_instance
        second_workflow_first_task.performers.add(second_user)
        second_workflow_first_task.require_completion_by_all = True
        second_workflow_first_task.save()
        first_task = workflow.current_task_instance
        first_task.require_completion_by_all = True
        first_task.save()
        first_task.taskperformer_set.filter(user=user).update(
            is_completed=True,
        )
        second_workflow_first_task.taskperformer_set.filter(
            user=user
        ).update(is_completed=True)

        # act
        complete_tasks(
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            user_id=user.id
        )

        # assert
        first_task.refresh_from_db()
        second_workflow_first_task.refresh_from_db()
        assert first_task.is_completed
        assert second_workflow_first_task.is_completed is False
