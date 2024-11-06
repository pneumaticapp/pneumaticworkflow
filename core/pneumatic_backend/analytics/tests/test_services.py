import pytest
from datetime import timedelta
from django.contrib.auth.models import AnonymousUser
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.analytics.events import (
    UserAnalyticsEvent,
    EventCategory,
    TemplateAnalyticsEvent,
    WorkflowAnalyticsEvent,
    SubscriptionAnalyticsEvent,
    SearchAnalyticsEvent,
    AttachmentAnalyticsEvent,
    AccountAnalyticsEvent,
    TaskAnalyticsEvent,
    LibraryTemplateAnalyticsEvent,
    TenantsAnalyticsEvent,
    CommentAnalyticsEvent,
    MentionsAnalyticsEvent,
)
from pneumatic_backend.analytics.services import (
    AnalyticService
)
from pneumatic_backend.accounts.enums import SourceType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_account,
    create_test_user,
    create_invited_user,
    create_test_template,
    create_test_workflow,
    create_test_attachment,
)
from pneumatic_backend.processes.enums import (
    TemplateIntegrationType,
    SysTemplateType,
)
from pneumatic_backend.analytics import messages
from pneumatic_backend.analytics.labels import Label
from pneumatic_backend.analytics.actions import (
    WorkflowActions
)
from pneumatic_backend.analytics.services import exceptions
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.models import (
    SystemTemplate,
    SystemTemplateCategory,
)

pytestmark = pytest.mark.django_db


class TestAnalyticService:

    def test__skip__is_not_superuser__ok(self, mocker):

        # arrange
        data = {'is_superuser': False}
        settings_mock = mocker.patch(
            'pneumatic_backend.analytics.services.settings'
        )
        settings_mock.PROJECT_CONF = {'ANALYTICS': True}

        # act
        result = AnalyticService._skip(**data)

        # assert
        assert result is False

    def test__skip__is_superuser__skip(self, mocker):

        # arrange
        data = {'is_superuser': True}
        settings_mock = mocker.patch(
            'pneumatic_backend.analytics.services.settings'
        )
        settings_mock.PROJECT_CONF = {'ANALYTICS': True}

        # act
        result = AnalyticService._skip(**data)

        # assert
        assert result is True

    def test__skip__disable_project_analytics__skip(self, mocker):

        # arrange
        settings_mock = mocker.patch(
            'pneumatic_backend.analytics.services.settings'
        )
        settings_mock.PROJECT_CONF = {
            'ANALYTICS': False
        }

        # act
        result = AnalyticService._skip()

        # assert
        assert result is True

    def test__skip__enable_project_analytics__ok(self, mocker):

        # arrange
        settings_mock = mocker.patch(
            'pneumatic_backend.analytics.services.settings'
        )
        settings_mock.PROJECT_CONF = {
            'ANALYTICS': True
        }

        # act
        result = AnalyticService._skip()

        # assert
        assert result is False

    def test__private_track__sent(self, mocker):

        # arrange
        data = {'value': 'test'}
        skip_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._skip',
            return_value=False
        )
        track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.analytics.track',
        )

        # act
        result = AnalyticService._track(**data)

        # assert
        assert result is True
        skip_mock.assert_called_once_with(**data)
        track_mock.assert_called_once_with(**data)

    def test__private_track__skip_condition__not_sent(
        self,
        mocker,
    ):

        # arrange
        data = {'value': 'test'}
        skip_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._skip',
            return_value=True
        )
        track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.analytics.track',
        )

        # act
        result = AnalyticService._track(**data)

        # assert
        assert result is False
        skip_mock.assert_called_once_with(**data)
        track_mock.assert_not_called()

    def test__public_track__ok(self, mocker):

        # arrange
        data = {'value': 'test'}
        value = 'value'
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=value
        )

        # act
        result = AnalyticService.track(**data)

        # assert
        assert result == value
        private_track_mock.assert_called_once_with(**data)

    def test__users_invite_sent__ok(self, mocker):

        # arrange
        invite_from = create_test_user()
        invite_to = create_test_user(
            email='t@t.t',
            account=invite_from.account
        )
        value = 'value'
        current_url = 'url'
        is_superuser = False

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=value
        )

        # act
        result = AnalyticService.users_invite_sent(
            invite_from=invite_from,
            invite_to=invite_to,
            current_url=current_url,
            is_superuser=is_superuser
        )

        # assert
        assert result == value
        private_track_mock.assert_called_once_with(
            user_id=invite_from.id,
            event=UserAnalyticsEvent.invite_sent,
            properties={
                'invitee_email': invite_to.email,
                'account_id': invite_from.account_id,
                'category': EventCategory.users,
                'current_url': current_url,
            },
            is_superuser=is_superuser
        )

    def test__users_invited__ok(self, mocker):

        # arrange
        invite_to = create_test_user()
        value = 'value'
        is_superuser = True
        invite_token = '123'

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=value
        )

        # act
        result = AnalyticService.users_invited(
            invite_to=invite_to,
            is_superuser=is_superuser,
            invite_token=invite_token,
        )

        # assert
        assert result == value
        private_track_mock.assert_called_once_with(
            user_id=invite_to.id,
            event=UserAnalyticsEvent.invited,
            properties={
                'email': invite_to.email,
                'account_id': invite_to.account_id,
                'category': EventCategory.users,
                'invite_token': invite_token,
            },
            is_superuser=False
        )

    def test__users_logged_in__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = False
        auth_type = AuthTokenType.USER
        return_value = True
        source = SourceType.GOOGLE
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.users_logged_in(
            user=user,
            is_superuser=is_superuser,
            auth_type=auth_type,
            source=source
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=UserAnalyticsEvent.logged_in,
            is_superuser=is_superuser,
            properties={
                'email': user.email,
                'account_id': user.account_id,
                'category': EventCategory.users,
                'auth_type': auth_type,
                'source': source
            },
        )

    def test__templates_created__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        is_superuser = False
        auth_type = AuthTokenType.USER
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )
        kickoff_fields_count = 1
        tasks_count = 2
        tasks_fields_count = 3
        delays_count = 4
        due_in_count = 5
        conditions_count = 6

        # act
        result = AnalyticService.templates_created(
            user=user,
            template=template,
            is_superuser=is_superuser,
            auth_type=auth_type,
            kickoff_fields_count=kickoff_fields_count,
            tasks_count=tasks_count,
            tasks_fields_count=tasks_fields_count,
            delays_count=delays_count,
            due_in_count=due_in_count,
            conditions_count=conditions_count,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.created,
            is_superuser=is_superuser,
            properties={
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'is_active': template.is_active,
                'is_public': template.is_public,
                'account_id': template.account_id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
                'kickoff_fields_count': kickoff_fields_count,
                'tasks_count': tasks_count,
                'tasks_fields_count': tasks_fields_count,
                'delays_count': delays_count,
                'due_in_count': due_in_count,
                'conditions_count': conditions_count,
            },
        )

    def test__templates_updated__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        is_superuser = False
        auth_type = AuthTokenType.USER
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )
        kickoff_fields_count = 1
        tasks_count = 2
        tasks_fields_count = 3
        delays_count = 4
        due_in_count = 5
        conditions_count = 6

        # act
        result = AnalyticService.templates_updated(
            user=user,
            template=template,
            is_superuser=is_superuser,
            auth_type=auth_type,
            kickoff_fields_count=kickoff_fields_count,
            tasks_count=tasks_count,
            tasks_fields_count=tasks_fields_count,
            delays_count=delays_count,
            due_in_count=due_in_count,
            conditions_count=conditions_count,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.updated,
            is_superuser=is_superuser,
            properties={
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'is_active': template.is_active,
                'is_public': template.is_public,
                'account_id': template.account_id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
                'kickoff_fields_count': kickoff_fields_count,
                'tasks_count': tasks_count,
                'tasks_fields_count': tasks_fields_count,
                'delays_count': delays_count,
                'due_in_count': due_in_count,
                'conditions_count': conditions_count,
            },
        )

    def test__templates_deleted__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        is_superuser = False
        auth_type = AuthTokenType.USER
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.templates_deleted(
            user=user,
            template=template,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.deleted,
            is_superuser=is_superuser,
            properties={
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'account_id': template.account_id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    def test__templates_task_due_date_created__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=1)
        task = template.tasks.first()
        is_superuser = False
        auth_type = AuthTokenType.USER
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.templates_task_due_date_created(
            user=user,
            template=template,
            task=task,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.due_date_created,
            is_superuser=is_superuser,
            properties={
                'template_id': template.id,
                'template_name': template.name,
                'task_number': task.number,
                'account_id': template.account_id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            }
        )

    def test__templates_task_condition_created__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user, tasks_count=1)
        task = template.tasks.first()
        is_superuser = False
        auth_type = AuthTokenType.USER
        return_value = True
        cond_id = 123
        condition = mocker.Mock(id=cond_id)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.templates_task_condition_created(
            user=user,
            template=template,
            task=task,
            condition=condition,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.condition_created,
            is_superuser=is_superuser,
            properties={
                'template_id': template.id,
                'template_name': template.name,
                'task_number': task.number,
                'condition_id': condition.id,
                'account_id': template.account_id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            }
        )

    def test__templates_kickoff_created__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        is_superuser = False
        auth_type = AuthTokenType.USER
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.templates_kickoff_created(
            user=user,
            template=template,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.kickoff_created,
            is_superuser=is_superuser,
            properties={
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'account_id': template.account_id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    def test__templates_kickoff_updated__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        is_superuser = False
        auth_type = AuthTokenType.USER
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.templates_kickoff_updated(
            user=user,
            template=template,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.kickoff_edited,
            is_superuser=is_superuser,
            properties={
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'account_id': template.account_id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    def test__workflows_terminated__ok(self, mocker):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        is_superuser = False
        auth_type = AuthTokenType.API
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.workflows_terminated(
            user=user,
            workflow=workflow,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.terminated,
            is_superuser=is_superuser,
            properties={
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'account_id': workflow.account_id,
                'category': EventCategory.workflows,
                'auth_type': auth_type
            }
        )

    def test__workflows_ended__ok(self, mocker):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        is_superuser = False
        auth_type = AuthTokenType.API
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.workflows_ended(
            user=user,
            workflow=workflow,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.ended,
            properties={
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'account_id': workflow.account_id,
                'category': EventCategory.workflows,
                'auth_type': auth_type
            },
            is_superuser=is_superuser
        )

    def test__users_guest_invite_sent__ok(self, mocker):

        # arrange
        invite_from = create_test_user()
        invite_to = create_test_user(
            email='t@t.t',
            account=invite_from.account
        )
        value = 'value'
        current_url = 'url'
        is_superuser = False

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=value
        )

        # act
        result = AnalyticService.users_guest_invite_sent(
            invite_from=invite_from,
            invite_to=invite_to,
            current_url=current_url,
            is_superuser=is_superuser
        )

        # assert
        assert result == value
        private_track_mock.assert_called_once_with(
            user_id=invite_from.id,
            event=UserAnalyticsEvent.guest_invite_sent,
            properties={
                'invitee_email': invite_to.email,
                'account_id': invite_from.account_id,
                'category': EventCategory.users,
                'current_url': current_url,
            },
            is_superuser=is_superuser
        )

    def test_invite_accepted__ok(self, mocker):

        # arrange
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=True
        )
        user = create_test_user()
        invited_user = create_invited_user(user=user)

        # act
        result = AnalyticService.users_invite_accepted(
            user_id=user.id,
            invited_user=invited_user,
            is_superuser=False,
        )

        # assert
        assert result is True
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=UserAnalyticsEvent.invite_accepted,
            properties={
                'category': EventCategory.users,
                'account_id': invited_user.account_id,
                'invitee': {
                    'email': invited_user.email,
                    'full_name': invited_user.get_full_name(),
                },
            },
            is_superuser=False,
        )

    def test__users_digest__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = False
        auth_type = AuthTokenType.GUEST
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.users_digest(
            user=user,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=UserAnalyticsEvent.digest,
            is_superuser=is_superuser,
            properties={
                'email': user.email,
                'category': EventCategory.users,
                'auth_type': auth_type,
            },
        )

    def test__workflows_started__authenticated_user__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        label = Label.external_workflow
        workflow = create_test_workflow(user, tasks_count=1)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.workflows_started(
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,
            user_id=user.id,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.started,
            is_superuser=is_superuser,
            properties={
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'account_id': workflow.account_id,
                'category': EventCategory.workflows,
                'auth_type': auth_type,
                'label': label,
            }
        )

    def test__workflows_started__anonymous_user__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = False
        return_value = True
        anonymous_id = '192.168.0.1'
        auth_type = AuthTokenType.GUEST
        label = Label.internal_workflow
        workflow = create_test_workflow(user, tasks_count=1, is_external=True)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.workflows_started(
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,
            anonymous_id=anonymous_id,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            anonymous_id=anonymous_id,
            event=WorkflowAnalyticsEvent.started,
            is_superuser=is_superuser,
            properties={
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'account_id': workflow.account_id,
                'category': EventCategory.workflows,
                'auth_type': auth_type,
                'label': label,
            }
        )

    def test__workflows_started__not_anonymous_and_user__raise_exception(
        self,
        mocker
    ):

        # arrange
        user = create_test_user()
        is_superuser = False
        auth_type = AuthTokenType.GUEST
        workflow = create_test_workflow(user, tasks_count=1, is_external=True)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track'
        )

        # act
        with pytest.raises(Exception) as ex:
            AnalyticService.workflows_started(
                workflow=workflow,
                auth_type=auth_type,
                is_superuser=is_superuser,
            )

        # assert
        assert ex.value.message == messages.MSG_AS_0001
        private_track_mock.assert_not_called()

    def test__workflows_urgent__authenticated_user__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = False
        return_value = True
        action = WorkflowActions.unmarked
        auth_type = AuthTokenType.API
        workflow = create_test_workflow(user, tasks_count=1)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.workflows_urgent(
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,
            user_id=user.id,
            action=action
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.urgent,
            is_superuser=is_superuser,
            properties={
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'category': EventCategory.workflows,
                'account_id': workflow.account_id,
                'auth_type': auth_type,
                'label': Label.urgent,
                'action': action
            }
        )

    def test__search_search__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = False
        token_type = AuthTokenType.GUEST
        return_value = True
        search_text = 'text'
        page = 'some page'

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.search_search(
            user_id=user.id,
            page=page,
            search_text=search_text,
            is_superuser=is_superuser,
            auth_type=token_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=SearchAnalyticsEvent.search,
            is_superuser=is_superuser,
            properties={
                'page': page,
                'search_text': search_text,
                'category': EventCategory.search,
                'auth_type': token_type,
            },
        )

    def test__attachments_uploaded__authenticated_user__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = True
        token_type = AuthTokenType.API
        return_value = True
        attachment = create_test_attachment(account=user.account)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.attachments_uploaded(
            user=user,
            attachment=attachment,
            is_superuser=is_superuser,
            auth_type=token_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=AttachmentAnalyticsEvent.uploaded,
            is_superuser=is_superuser,
            properties={
                'auth_type': token_type,
                'id': attachment.id,
                'size': attachment.humanize_size,
                'account_id': user.account_id,
                'category': EventCategory.attachments,
                'type': attachment.extension,
            }
        )

    def test__attachments_uploaded__anonymous_user__ok(self, mocker):

        # arrange
        account = create_test_account()
        is_superuser = True
        token_type = AuthTokenType.API
        return_value = True
        anonymous_id = '168.192.0.1'
        attachment = create_test_attachment(account=account)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.attachments_uploaded(
            user=AnonymousUser(),
            anonymous_id=anonymous_id,
            attachment=attachment,
            is_superuser=is_superuser,
            auth_type=token_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            anonymous_id=anonymous_id,
            event=AttachmentAnalyticsEvent.uploaded,
            is_superuser=is_superuser,
            properties={
                'auth_type': token_type,
                'id': attachment.id,
                'size': attachment.humanize_size,
                'account_id': account.id,
                'category': EventCategory.attachments,
                'type': attachment.extension,
            }
        )

    def test__attachments_uploaded__not_user__raise_exception(self, mocker):

        # arrange
        account = create_test_account()
        is_superuser = True
        token_type = AuthTokenType.API
        attachment = create_test_attachment(account=account)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
        )

        # act
        with pytest.raises(exceptions.InvalidUserCredentials):
            AnalyticService.attachments_uploaded(
                attachment=attachment,
                is_superuser=is_superuser,
                auth_type=token_type,
                user=AnonymousUser()
            )

        # assert
        private_track_mock.assert_not_called()

    def test__templates_integrated__user_id__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.templates_integrated(
            template_id=template.id,
            account_id=user.account_id,
            integration_type=TemplateIntegrationType.ZAPIER,
            user_id=user.id,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            is_superuser=False,
            event=TemplateAnalyticsEvent.integrated,
            properties={
                'template_id': template.id,
                'integration_type': TemplateIntegrationType.ZAPIER,
                'account_id': user.account_id,
                'category': EventCategory.templates,
            }
        )

    def test__templates_integrated__anonymous_id__ok(self, mocker):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        return_value = True
        anonymous_id = '192.168.0.1'

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.templates_integrated(
            template_id=template.id,
            account_id=user.account_id,
            integration_type=TemplateIntegrationType.ZAPIER,
            anonymous_id=anonymous_id,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            anonymous_id=anonymous_id,
            is_superuser=False,
            event=TemplateAnalyticsEvent.integrated,
            properties={
                'template_id': template.id,
                'integration_type': TemplateIntegrationType.ZAPIER,
                'account_id': user.account_id,
                'category': EventCategory.templates,
            }
        )

    def test__templates_integrated__anonymous_and_user__raise_exception(
        self,
        mocker
    ):

        # arrange
        user = create_test_user()
        template = create_test_template(user)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track'
        )

        # act
        with pytest.raises(Exception) as ex:
            AnalyticService.templates_integrated(
                template_id=template.id,
                account_id=user.account_id,
                integration_type=TemplateIntegrationType.ZAPIER,
            )

        # assert
        assert ex.value.message == messages.MSG_AS_0001
        private_track_mock.assert_not_called()

    def test__accounts_webhooks_subscribed__ok(self, mocker):

        # arrange
        user = create_test_user()
        return_value = True

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.accounts_webhooks_subscribed(
            user=user,
            is_superuser=True
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            is_superuser=True,
            event=AccountAnalyticsEvent.webhooks_subscribed,
            properties={
                'account_id': user.account_id,
                'category': EventCategory.accounts,
            }
        )

    def test__workflows_delayed__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        workflow = create_test_workflow(user, tasks_count=1)
        task = workflow.current_task_instance
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )
        duration = timedelta(days=10)

        # act
        result = AnalyticService.workflow_delayed(
            user=user,
            duration=duration,
            workflow=workflow,
            task=task,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.delayed,
            is_superuser=is_superuser,
            properties={
                'id': workflow.id,
                'duration': 10,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'account_id': workflow.account_id,
                'task_number': task.number,
                'category': EventCategory.workflows,
                'auth_type': auth_type,
                'label': Label.delayed,
                'action': WorkflowActions.delayed,
            }
        )

    def test__workflows_delayed__legacy_template__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        workflow = create_test_workflow(user, tasks_count=1)
        workflow.template.delete()
        workflow.legacy_template_name = 'Legacy name'
        workflow.is_legacy_template = True
        workflow.save(
            update_fields=['legacy_template_name', 'is_legacy_template']
        )
        workflow.refresh_from_db()
        task = workflow.current_task_instance
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )
        duration = timedelta(days=10)

        # act
        result = AnalyticService.workflow_delayed(
            user=user,
            duration=duration,
            workflow=workflow,
            task=task,
            is_superuser=is_superuser,
            auth_type=auth_type,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.delayed,
            is_superuser=is_superuser,
            properties={
                'id': workflow.id,
                'duration': 10,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.legacy_template_name,
                'account_id': workflow.account_id,
                'task_number': task.number,
                'category': EventCategory.workflows,
                'auth_type': auth_type,
                'label': Label.delayed,
                'action': WorkflowActions.delayed,
            }
        )

    def test__subscription_created__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        max_users = 100
        plan = BillingPlanType.PREMIUM
        account = create_test_account(max_users=max_users, plan=plan)
        user = create_test_user(account=account)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.subscription_created(
            is_superuser=is_superuser,
            user=user
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.created,
            is_superuser=is_superuser,
            properties={
                'category': EventCategory.subscriptions,
                'account_id': user.account_id,
                'email': user.email,
                'quantity': user.account.max_users,
                'plan_code': user.account.billing_plan,
            }
        )

    def test__subscription_updated__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        max_users = 100
        plan = BillingPlanType.PREMIUM
        account = create_test_account(max_users=max_users, plan=plan)
        user = create_test_user(account=account)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.subscription_updated(
            is_superuser=is_superuser,
            user=user
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.updated,
            is_superuser=is_superuser,
            properties={
                'category': EventCategory.subscriptions,
                'account_id': user.account_id,
                'email': user.email,
                'quantity': user.account.max_users,
                'plan_code': user.account.billing_plan,
            }
        )

    def test__subscription_converted__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        max_users = 100
        plan = BillingPlanType.PREMIUM
        account = create_test_account(max_users=max_users, plan=plan)
        user = create_test_user(account=account)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.subscription_converted(
            is_superuser=is_superuser,
            user=user
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.converted,
            is_superuser=is_superuser,
            properties={
                'category': EventCategory.subscriptions,
                'account_id': user.account_id,
                'email': user.email,
                'quantity': user.account.max_users,
                'plan_code': user.account.billing_plan,
            }
        )

    def test__subscription_expired__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        account = create_test_account()
        user = create_test_user(account=account)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.subscription_expired(
            is_superuser=is_superuser,
            user=user
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.expired,
            is_superuser=is_superuser,
            properties={
                'account_id': user.account.id,
                'category': EventCategory.subscriptions,
            }
        )

    def test__subscription_canceled__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        account = create_test_account()
        user = create_test_user(account=account)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.subscription_canceled(
            is_superuser=is_superuser,
            user=user
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.canceled,
            is_superuser=is_superuser,
            properties={
                'account_id': user.account.id,
                'category': EventCategory.subscriptions,
            }
        )

    def test__trial_subscription_created__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        max_users = 100
        plan = BillingPlanType.PREMIUM
        account = create_test_account(max_users=max_users, plan=plan)
        user = create_test_user(account=account)

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.trial_subscription_created(
            is_superuser=is_superuser,
            user=user
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.trial,
            is_superuser=is_superuser,
            properties={
                'category': EventCategory.subscriptions,
                'account_id': user.account_id,
                'email': user.email,
                'quantity': user.account.max_users,
                'plan_code': user.account.billing_plan,
            }
        )

    def test__task_returned__ok(self, mocker):

        # arrange
        is_superuser = True
        account = create_test_account()
        user = create_test_user(account=account)
        return_value = True
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.current_task_instance

        # act
        result = AnalyticService.task_returned(
            user=user,
            task=task,
            auth_type=AuthTokenType.USER,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TaskAnalyticsEvent.returned,
            is_superuser=is_superuser,
            properties={
                'workflow_id': task.workflow.id,
                'workflow_name': task.workflow.name,
                'task_name': task.name,
                'category': EventCategory.tasks,
                'auth_type': AuthTokenType.USER,
            }
        )

    def test__template_generation_init__ok(self, mocker):

        # arrange
        user = create_test_user()
        return_value = True
        description = 's0me description'
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.template_generation_init(
            user=user,
            description=description,
            auth_type=AuthTokenType.API,
            is_superuser=True,
            success=False,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            is_superuser=True,
            event=TemplateAnalyticsEvent.generation_init,
            properties={
                'account_id': user.account_id,
                'request description': description,
                'category': EventCategory.templates,
                'label': Label.template_generation,
                'auth_type': AuthTokenType.API,
                'success': False,
            }
        )

    def test__workflow_returned__ok(self, mocker):

        # arrange
        is_superuser = True
        account = create_test_account()
        user = create_test_user(account=account)
        return_value = True
        auth_type = AuthTokenType.USER
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.current_task_instance

        # act
        result = AnalyticService.workflow_returned(
            user=user,
            task=task,
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.returned,
            is_superuser=is_superuser,
            properties={
                'account_id': account.id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'returned_to_task': task.name,
                'category': EventCategory.workflows,
                'auth_type': auth_type,
            }
        )

    def test__library_template_opened__ok(self, mocker):

        # arrange
        user = create_test_user()
        is_superuser = True
        auth_type = AuthTokenType.API
        return_value = True
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )
        category = SystemTemplateCategory.objects.create(
            name='Sales',
            order=1,
        )
        name = 'Some name'
        sys_template = SystemTemplate.objects.create(
            name=name,
            type=SysTemplateType.LIBRARY,
            template={},
            category=category,
            is_active=True
        )

        # act
        result = AnalyticService.library_template_opened(
            user=user,
            sys_template=sys_template,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            is_superuser=is_superuser,
            event=LibraryTemplateAnalyticsEvent.opened,
            properties={
                'id': sys_template.id,
                'template_name': sys_template.name,
                'template_category': sys_template.category.name,
                'account_id': user.account_id,
                'category': EventCategory.templates,
                'label': Label.library_template_opened,
                'auth_type': auth_type,
            }
        )

    def test__account_created__ok(self, mocker):

        # arrange
        account = create_test_account()
        utm_source = 'some_utm_source'
        utm_medium = 'some_utm_medium'
        utm_campaign = 'some_utm_campaign'
        utm_term = 'some_utm_term'
        utm_content = 'some_utm_content'
        gclid = 'some_gclid'
        account.accountsignupdata_set.update(
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content,
            gclid=gclid
        )
        user = create_test_user(account=account)
        is_superuser = True
        auth_type = AuthTokenType.API
        return_value = True
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.account_created(
            user=user,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            is_superuser=is_superuser,
            event=AccountAnalyticsEvent.created,
            properties={
                'account_id': account.id,
                'email': user.email,
                'category': EventCategory.accounts,
                'auth_type': auth_type,
                'utm_source': utm_source,
                'utm_medium': utm_medium,
                'utm_campaign': utm_campaign,
                'utm_term': utm_term,
                'utm_content': utm_content,
                'gclid': gclid
            }
        )

    def test__account_verified__ok(self, mocker):

        # arrange
        account = create_test_account()
        utm_source = 'some_utm_source'
        utm_medium = 'some_utm_medium'
        utm_campaign = 'some_utm_campaign'
        utm_term = 'some_utm_term'
        utm_content = 'some_utm_content'
        gclid = 'some_gclid'
        account.accountsignupdata_set.update(
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content,
            gclid=gclid
        )
        user = create_test_user(account=account)
        is_superuser = True
        auth_type = AuthTokenType.API
        return_value = True
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.account_verified(
            user=user,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            is_superuser=is_superuser,
            event=AccountAnalyticsEvent.verified,
            properties={
                'account_id': account.id,
                'email': user.email,
                'category': EventCategory.accounts,
                'auth_type': auth_type,
                'utm_source': utm_source,
                'utm_medium': utm_medium,
                'utm_campaign': utm_campaign,
                'utm_term': utm_term,
                'utm_content': utm_content,
                'gclid': gclid
            }
        )

    def test__tenants_added__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        auth_type = AuthTokenType.API
        master_account = create_test_account()
        master_user = create_test_user(account=master_account)
        tenant_account = create_test_account()

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.tenants_added(
            master_user=master_user,
            tenant_account=tenant_account,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=master_user.id,
            event=TenantsAnalyticsEvent.added,
            is_superuser=is_superuser,
            properties={
                'category': EventCategory.tenants,
                'account_id': master_account.id,
                'tenant_id': tenant_account.id,
                'auth_type': auth_type,
            }
        )

    def test__tenants_accessed__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        auth_type = AuthTokenType.API
        master_account = create_test_account()
        master_user = create_test_user(account=master_account)
        tenant_account = create_test_account()

        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.tenants_accessed(
            master_user=master_user,
            tenant_account=tenant_account,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=master_user.id,
            event=TenantsAnalyticsEvent.accessed,
            is_superuser=is_superuser,
            properties={
                'category': EventCategory.tenants,
                'account_id': master_account.id,
                'tenant_id': tenant_account.id,
                'auth_type': auth_type,
            }
        )

    def test__template_generated_from_landing__ok(self, mocker):

        # arrange
        is_superuser = True
        return_value = True
        auth_type = AuthTokenType.API
        user = create_test_user()
        template = create_test_template(user=user)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.template_generated_from_landing(
            user=user,
            template=template,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.generated_from_landing,
            is_superuser=is_superuser,
            properties={
                'id': template.id,
                'account_id': user.account.id,
                'category': EventCategory.templates,
                'label': Label.template_generation,
                'auth_type': auth_type,
            }
        )

    def test__template_created_from_landing_library__ok(self, mocker):

        # arrange
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.USER
        user = create_test_user()
        template = create_test_template(user=user)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.template_created_from_landing_library(
            user=user,
            template=template,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=TemplateAnalyticsEvent.created_from_landing_library,
            is_superuser=is_superuser,
            properties={
                'id': template.id,
                'template_name': template.name,
                'account_id': user.account.id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            }
        )

    def test__comment_added__ok(self, mocker):

        # arrange
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.comment_added(
            user=user,
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,

        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=CommentAnalyticsEvent.added,
            is_superuser=is_superuser,
            properties={
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            }
        )

    def test__mentions_created__ok(self, mocker):

        # arrange
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.mentions_created(
            user=user,
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,

        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=MentionsAnalyticsEvent.created,
            is_superuser=is_superuser,
            properties={
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.mentions,
                'auth_type': auth_type,
            }
        )

    def test__comment_edited__ok(self, mocker):

        # arrange
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.comment_edited(
            user=user,
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,

        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=CommentAnalyticsEvent.edited,
            is_superuser=is_superuser,
            properties={
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            }
        )

    def test__comment_deleted__ok(self, mocker):

        # arrange
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.comment_deleted(
            user=user,
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,

        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=CommentAnalyticsEvent.deleted,
            is_superuser=is_superuser,
            properties={
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            }
        )

    def test_comment_reaction_added__ok(self, mocker):

        # arrange
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.comment_reaction_added(
            user=user,
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=CommentAnalyticsEvent.reaction_added,
            is_superuser=is_superuser,
            properties={
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            }
        )

    def test_comment_reaction_deleted__ok(self, mocker):

        # arrange
        is_superuser = False
        return_value = True
        auth_type = AuthTokenType.API
        user = create_test_user()
        workflow = create_test_workflow(user=user, tasks_count=1)
        private_track_mock = mocker.patch(
            'pneumatic_backend.analytics.services.AnalyticService._track',
            return_value=return_value
        )

        # act
        result = AnalyticService.comment_reaction_deleted(
            user=user,
            workflow=workflow,
            auth_type=auth_type,
            is_superuser=is_superuser,
        )

        # assert
        assert result == return_value
        private_track_mock.assert_called_once_with(
            user_id=user.id,
            event=CommentAnalyticsEvent.reaction_deleted,
            is_superuser=is_superuser,
            properties={
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            }
        )
