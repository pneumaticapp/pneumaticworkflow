import pytz
import pytest
from django.utils import timezone
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_account,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0023,
)
from pneumatic_backend.processes.models import (
    Workflow,
    FieldTemplate,
    ConditionTemplate,
    RuleTemplate,
    PredicateTemplate,
    WorkflowEvent,
)
from pneumatic_backend.processes.enums import (
    PredicateOperator,
    FieldType,
    WorkflowEventType,
    WorkflowStatus,
)
from pneumatic_backend.authentication.tokens import (
    PublicToken,
    EmbedToken,
)
from pneumatic_backend.processes.consts import WORKFLOW_NAME_LENGTH


pytestmark = pytest.mark.django_db


class TestRunPublicTemplate:

    def test_run__kickoff_fields__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        text_field_template = FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
        )
        user_field_template = FieldTemplate.objects.create(
            order=2,
            name='User',
            type=FieldType.USER,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
        )
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}
        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    text_field_template.api_name: 'text',
                    user_field_template.api_name: str(user.id)
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        assert response.data['redirect_url'] is None
        workflow = Workflow.objects.get(template=template)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'{formatted_date} — {template.name}'
        assert workflow.is_external is True
        assert workflow.is_urgent is False
        assert workflow.workflow_starter is None
        assert workflow.kickoff_instance.output.all().count() == 2
        assert workflow.tasks.count() == template.tasks_count

        field = workflow.kickoff_instance.output.all().order_by(
            'order'
        ).first()
        text_field_template.refresh_from_db()
        assert field.name == text_field_template.name
        assert field.api_name == text_field_template.api_name
        assert field.value == 'text'
        assert field.is_required is True
        first_task = workflow.current_task_instance

        assert WorkflowEvent.objects.filter(
            account_id=user.account.id,
            type=WorkflowEventType.RUN,
        ).count() == 1

        assert WorkflowEvent.objects.filter(
            account_id=user.account.id,
            task_json__id=first_task.id,
            type=WorkflowEventType.TASK_START,
        ).count() == 1

        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__string_abbreviation_after_insert_fields_vars__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        field_api_name = 'field-1'
        FieldTemplate.objects.create(
            name='Text',
            type=FieldType.TEXT,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name
        )
        wf_name_template = 'a' * (WORKFLOW_NAME_LENGTH - 4)
        wf_name_template += '{{%s}}' % field_api_name
        template.wf_name_template = wf_name_template
        template.save()

        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_api_name: 'Some shit!',
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        name = (
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaSom…'
        )
        workflow = Workflow.objects.get(template=template)
        assert workflow.name == name
        assert workflow.name_template == wf_name_template

    def test_run__task_fields__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        template_task = template.tasks.first()
        text_field_template = FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            task=template_task,
            is_required=True,
            template=template,
        )
        user_field_template = FieldTemplate.objects.create(
            order=2,
            name='User',
            type=FieldType.USER,
            task=template_task,
            is_required=True,
            template=template,
        )
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}
        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        assert response.data['redirect_url'] is None
        workflow = Workflow.objects.get(template=template)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'{formatted_date} — {template.name}'
        assert workflow.is_external is True
        assert workflow.is_urgent is False
        assert workflow.workflow_starter is None
        assert workflow.current_task_instance.output.all().count() == 2
        assert workflow.tasks.count() == template.tasks_count

        text_field = workflow.current_task_instance.output.all().order_by(
            'order'
        ).first()
        text_field_template.refresh_from_db()
        assert text_field.name == text_field_template.name
        assert text_field.api_name == text_field_template.api_name
        assert text_field.value == ''
        assert text_field.is_required is True

        user_field = workflow.current_task_instance.output.all().order_by(
            'order'
        ).last()
        user_field_template.refresh_from_db()
        assert user_field.name == user_field_template.name
        assert user_field.api_name == user_field_template.api_name
        assert user_field.value == ''
        assert user_field.user_id is None
        assert user_field.is_required is True

        first_task = workflow.current_task_instance
        assert WorkflowEvent.objects.filter(
            account_id=user.account.id,
            type=WorkflowEventType.RUN,
        ).count() == 1

        assert WorkflowEvent.objects.filter(
            account_id=user.account.id,
            task_json__id=first_task.id,
            type=WorkflowEventType.TASK_START,
        ).count() == 1
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__not_authorized__permission_denied(
        self,
        api_client,
        mocker
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=None
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__redirect_url_on_premium__ok(
        self,
        mocker,
        api_client,
        session_mock,
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        redirect_url = 'example.org'
        template.public_success_url = redirect_url
        template.save()
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {}
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        assert response.data['redirect_url'] == redirect_url
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__redirect_url_on_freemium__is_none(
        self,
        mocker,
        api_client,
        session_mock,
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        redirect_url = 'example.org'
        template.public_success_url = redirect_url
        template.save()
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {}
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        assert response.data['redirect_url'] is None
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__not_fields__ok(self, mocker, api_client, session_mock):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}
        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'{formatted_date} — {template.name}'
        assert workflow.is_external is True
        assert workflow.kickoff_instance.output.all().count() == 0
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__null_fields__ok(self, mocker, api_client, session_mock):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': None
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        assert workflow.kickoff_instance.output.all().count() == 0
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__fields_not_required__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        field_template = FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            is_required=False,
            api_name='text-field-1',
            template=template,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}
        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {},
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'{formatted_date} — {template.name}'
        assert workflow.is_external is True
        assert workflow.kickoff_instance.output.all().count() == 1

        field = workflow.kickoff_instance.output.first()
        field_template.refresh_from_db()
        assert field.name == field_template.name
        assert field.api_name == field_template.api_name
        assert field.value == ''
        assert field.is_required == field_template.is_required
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__skip_required_field__validation_error(
        self,
        mocker,
        api_client,
        session_mock,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        field_template = FieldTemplate.objects.create(
            order=1,
            name='Text',
            type=FieldType.TEXT,
            kickoff=template.kickoff_instance,
            is_required=True,
            template=template,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {},
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == MSG_PW_0023
        assert response.data['details']['reason'] == MSG_PW_0023
        assert response.data['details']['api_name'] == field_template.api_name
        assert not Workflow.objects.filter(template=template).exists()
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__skip_first_task__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=2
        )
        field_template = FieldTemplate.objects.create(
            order=1,
            name='Skip task field',
            type=FieldType.STRING,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )

        condition_template = ConditionTemplate.objects.create(
            task=template.tasks.first(),
            action=ConditionTemplate.SKIP_TASK,
            order=0,
            template=template,
        )
        rule_1 = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_1,
            operator=PredicateOperator.EQUAL,
            field_type=FieldType.STRING,
            field=field_template.api_name,
            value='skip first task',
            template=template,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_template.api_name: 'skip first task',
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        assert workflow.current_task == 2
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__first_task_end_workflow__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        account = create_test_account(plan=BillingPlanType.PREMIUM)
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=2
        )
        field_template = FieldTemplate.objects.create(
            order=1,
            name='Skip task field',
            type=FieldType.STRING,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
        )

        condition_template = ConditionTemplate.objects.create(
            task=template.tasks.first(),
            action=ConditionTemplate.END_WORKFLOW,
            order=0,
            template=template,
        )
        rule_1 = RuleTemplate.objects.create(
            condition=condition_template,
            template=template,
        )
        PredicateTemplate.objects.create(
            rule=rule_1,
            operator=PredicateOperator.EQUAL,
            field_type=FieldType.STRING,
            field=field_template.api_name,
            value='end workflow',
            template=template,
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_template.api_name: 'end workflow',
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        assert workflow.status == WorkflowStatus.DONE
        assert workflow.date_completed
        assert WorkflowEvent.objects.filter(
            account_id=user.account.id,
            type=WorkflowEventType.ENDED_BY_CONDITION,
        ).count() == 1
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__skip_captcha__validation_error(
        self,
        mocker,
        api_client,
        session_mock,
    ):

        # arrange
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True,
        )
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={'fields': {}},
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == 'This field is required.'
        assert response.data['details']['name'] == 'captcha'
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__name_with_system_vars__only__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template_name = 'New'
        wf_name_template = '{{ template-name }} {{ date }}'
        template = create_test_template(
            user=user,
            name=template_name,
            is_active=True,
            is_public=True,
            tasks_count=1,
            wf_name_template=wf_name_template,
        )
        date = timezone.now()
        mocker.patch('django.utils.timezone.now', return_value=date)

        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}
        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip'
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'{template_name} {formatted_date}'
        assert workflow.name_template == f'{template_name} {formatted_date}'

    def test_run__name_with_system_and_kickoff_vars__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        field_api_name = 'field-123'
        FieldTemplate.objects.create(
            name='User',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name
        )
        wf_name_template = 'Feedback from {{%s}} {{ date }}' % field_api_name
        template.wf_name_template = wf_name_template
        template.save()

        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}
        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_api_name: str(user.id)
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'Feedback from {user.name} {formatted_date}'
        assert workflow.name_template == (
            'Feedback from {{%s}} %s' % (field_api_name, formatted_date)
        )

    def test_run__name_with_kickoff_vars_only__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template_name = 'New'
        template = create_test_template(
            user=user,
            name=template_name,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        field_api_name_1 = 'field-1'
        field_api_name_2 = 'field-2'
        field_api_name_3 = 'field-3'
        FieldTemplate.objects.create(
            name='Text',
            type=FieldType.TEXT,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_1
        )
        FieldTemplate.objects.create(
            name='User',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_2
        )
        FieldTemplate.objects.create(
            name='Url',
            type=FieldType.URL,
            is_required=False,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_3
        )
        wf_name_template = 'Feedback: {{%s}} from {{ %s }} Url: {{%s}}' % (
            field_api_name_1,
            field_api_name_2,
            field_api_name_3,
        )
        template.wf_name_template = wf_name_template
        template.save()

        feedback = 'Some shit!'

        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_api_name_1: feedback,
                    field_api_name_2: str(user.id)
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        assert workflow.name == f'Feedback: {feedback} from {user.name} Url: '
        assert workflow.name_template == wf_name_template

    def test_run__wf_template_is_not_active__set_default_wf_name(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1,
        )
        field_api_name = 'field-1'
        FieldTemplate.objects.create(
            name='Text',
            type=FieldType.TEXT,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name
        )
        wf_name_template = None
        template.wf_name_template = wf_name_template
        template.save()

        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        default_wf_name = f'{formatted_date} — {template.name}'

        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_api_name: 'Some shit!',
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        workflow = Workflow.objects.get(template=template)
        assert workflow.name == default_wf_name
        assert workflow.name_template == default_wf_name

    def test_run__disable_captcha__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        auth_header_value = f'Token {template.public_id}'
        token = PublicToken(template.public_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        anonymous_user_workflow_exists_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True,
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': False}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': '',
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 200
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)
        anonymous_user_workflow_exists_mock.assert_called_once()


class TestRunEmbedTemplate:

    def test_run__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1
        )
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {}
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 204
        workflow = Workflow.objects.get(template=template)
        first_task = workflow.tasks.first()
        assert workflow.is_external is True
        assert workflow.workflow_starter is None

        assert WorkflowEvent.objects.filter(
            account_id=user.account.id,
            type=WorkflowEventType.RUN,
        ).count() == 1

        assert WorkflowEvent.objects.filter(
            account_id=user.account.id,
            task_json__id=first_task.id,
            type=WorkflowEventType.TASK_START,
        ).count() == 1

        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__string_abbreviation_after_insert_fields_vars__ok(
        self,
        mocker,
        api_client,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_public=True,
            tasks_count=1
        )
        field_api_name = 'field-1'
        FieldTemplate.objects.create(
            name='Text',
            type=FieldType.TEXT,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name
        )
        wf_name_template = 'a' * (WORKFLOW_NAME_LENGTH - 4)
        wf_name_template += '{{%s}}' % field_api_name
        template.wf_name_template = wf_name_template
        template.save()

        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_api_name: 'Some shit!',
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 204
        name = (
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaSom…'
        )
        workflow = Workflow.objects.get(template=template)
        assert workflow.name == name
        assert workflow.name_template == wf_name_template

    def test_run__not_authorized__permission_denied(
        self,
        api_client,
        mocker
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=None
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.get(
            path=f'/templates/public',
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 401
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__skip_captcha__validation_error(
        self,
        mocker,
        api_client,
        session_mock,
    ):

        # arrange
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True,
        )
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={'fields': {}},
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 400
        assert response.data['code'] == ErrorCode.VALIDATION_ERROR
        assert response.data['message'] == 'This field is required.'
        assert response.data['details']['name'] == 'captcha'
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)

    def test_run__name_with_system_vars__only__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template_name = 'New'
        wf_name_template = '{{ template-name }} {{ date }}'
        template = create_test_template(
            user=user,
            name=template_name,
            is_active=True,
            is_embedded=True,
            tasks_count=1,
            wf_name_template=wf_name_template,
        )
        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip'
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 204
        workflow = Workflow.objects.get(template=template)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'{template_name} {formatted_date}'
        assert workflow.name_template == f'{template_name} {formatted_date}'

    def test_run__name_with_system_and_kickoff_vars__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1,
        )
        field_api_name = 'field-123'
        FieldTemplate.objects.create(
            name='User',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name
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
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)

        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_api_name: str(user.id)
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 204
        workflow = Workflow.objects.get(template=template)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        assert workflow.name == f'Feedback from {user.name} {formatted_date}'
        assert workflow.name_template == (
            'Feedback from {{%s}} %s' % (field_api_name, formatted_date)
        )

    def test_run__name_with_kickoff_vars_only__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template_name = 'New'
        template = create_test_template(
            user=user,
            name=template_name,
            is_active=True,
            is_embedded=True,
            tasks_count=1,
        )
        field_api_name_1 = 'field-1'
        field_api_name_2 = 'field-2'
        field_api_name_3 = 'field-3'
        FieldTemplate.objects.create(
            name='Text',
            type=FieldType.TEXT,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_1
        )
        FieldTemplate.objects.create(
            name='User',
            type=FieldType.USER,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_2
        )
        FieldTemplate.objects.create(
            name='Url',
            type=FieldType.URL,
            is_required=False,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name_3
        )
        wf_name_template = 'Feedback: {{%s}} from {{ %s }} Url: {{%s}}' % (
            field_api_name_1,
            field_api_name_2,
            field_api_name_3,
        )
        template.wf_name_template = wf_name_template
        template.save()

        feedback = 'Some shit!'

        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_api_name_1: feedback,
                    field_api_name_2: str(user.id)
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 204
        workflow = Workflow.objects.get(template=template)
        assert workflow.name == f'Feedback: {feedback} from {user.name} Url: '
        assert workflow.name_template == wf_name_template

    def test_run__wf_template_is_not_active__set_default_wf_name(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1,
            wf_name_template=None
        )
        field_api_name = 'field-1'
        FieldTemplate.objects.create(
            name='Text',
            type=FieldType.TEXT,
            is_required=True,
            kickoff=template.kickoff_instance,
            template=template,
            api_name=field_api_name
        )
        date = timezone.datetime(
            year=2024,
            month=8,
            day=28,
            hour=10,
            minute=41,
            tzinfo=pytz.timezone('UTC')
        )
        mocker.patch('django.utils.timezone.now', return_value=date)
        formatted_date = 'Aug 28, 2024, 10:41AM'
        default_wf_name = f'{formatted_date} — {template.name}'

        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService.'
            'workflows_started'
        )
        mocker.patch(
            'pneumatic_backend.processes.api_v2.services.templates.'
            'integrations.TemplateIntegrationsService.public_api_request',
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': True}

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={
                'captcha': 'skip',
                'fields': {
                    field_api_name: 'Some shit!',
                }
            },
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 204
        workflow = Workflow.objects.get(template=template)
        assert workflow.name == default_wf_name
        assert workflow.name_template == default_wf_name

    def test_run__disable_captcha__ok(
        self,
        mocker,
        api_client,
        session_mock
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
            is_embedded=True,
            tasks_count=1
        )
        user_ip = '127.0.0.1'
        mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.get_user_ip',
            return_value=user_ip
        )
        auth_header_value = f'Token {template.embed_id}'
        token = EmbedToken(template.embed_id)
        get_token_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_token',
            return_value=token
        )
        get_template_mock = mocker.patch(
            'pneumatic_backend.authentication.services.public_auth.'
            'PublicAuthService.get_template',
            return_value=template
        )
        settings_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.settings'
        )
        settings_mock.PROJECT_CONF = {'CAPTCHA': False}
        anonymous_user_workflow_exists_mock = mocker.patch(
            'pneumatic_backend.processes.api_v2.views.public.template.'
            'PublicTemplateViewSet.anonymous_user_workflow_exists',
            return_value=True,
        )

        # act
        response = api_client.post(
            path=f'/templates/public/run',
            data={},
            **{'X-Public-Authorization': auth_header_value}
        )

        # assert
        assert response.status_code == 204
        get_token_mock.assert_called_once()
        get_template_mock.assert_called_once_with(token)
        anonymous_user_workflow_exists_mock.assert_called_once()
