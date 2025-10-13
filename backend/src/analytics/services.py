from typing import Optional, List
import analytics
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
from src.accounts.models import (
    Account,
    UserGroup,
)
from src.processes.models.templates.template import Template
from src.processes.models.templates.system_template import SystemTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.conditions import ConditionTemplate
from src.processes.models.workflows.workflow import Workflow
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.attachment import FileAttachment
from src.analytics.labels import Label
from src.analytics.actions import (
    WorkflowActions,
)
from src.accounts.enums import SourceType
from src.analytics.events import (
    UserAnalyticsEvent,
    WorkflowAnalyticsEvent,
    TemplateAnalyticsEvent,
    EventCategory,
    SubscriptionAnalyticsEvent,
    SearchAnalyticsEvent,
    AttachmentAnalyticsEvent,
    AccountAnalyticsEvent,
    TaskAnalyticsEvent,
    LibraryTemplateAnalyticsEvent,
    TenantsAnalyticsEvent,
    MentionsAnalyticsEvent,
    CommentAnalyticsEvent,
    GroupsAnalyticsEvent,
)
from src.authentication.enums import AuthTokenType
from src.analytics import exceptions
from src.processes.enums import TemplateIntegrationType

UserModel = get_user_model()


class AnalyticService:

    """ *Method naming recommendation:
        Compose the method name with the following pattern:
            def <category>_<event>(*args, **kwargs) -> bool:
                ...
        Example:
            category = EventCategory.users
            event = UserAnalyticsEvent.invite_sent

            Method name in result:
                def users_invite_sent(*args, **kwargs) -> bool: """

    @classmethod
    def _skip(cls, *args, **kwargs) -> bool:
        if (
            settings.PROJECT_CONF['ANALYTICS']
            and settings.ANALYTICS_WRITE_KEY
        ):
            return kwargs.get('is_superuser', False)
        else:
            return True

    @classmethod
    def _track(cls, *args, **kwargs) -> bool:
        if cls._skip(*args, **kwargs):
            return False
        kwargs.pop('is_superuser', None)
        analytics.debug = settings.ANALYTICS_DEBUG
        analytics.write_key = settings.ANALYTICS_WRITE_KEY
        analytics.track(*args, **kwargs)
        return True

    @classmethod
    def track(cls, *args, **kwargs) -> bool:
        return cls._track(*args, **kwargs)

    @classmethod
    def users_invite_sent(
        cls,
        invite_from,
        invite_to,
        current_url: str,
        is_superuser: bool,
    ) -> bool:
        return cls._track(
            user_id=invite_from.id,
            event=UserAnalyticsEvent.invite_sent,
            properties={
                'text': f'Invited a "{invite_to.email}" to the team',
                'email': invite_from.email,
                'first_name': invite_from.first_name,
                'last_name': invite_from.last_name,
                'account_id': invite_from.account_id,
                'invitee_email': invite_to.email,
                'category': EventCategory.users,
                'current_url': current_url,
            },
            is_superuser=is_superuser,
        )

    @classmethod
    def users_invited(
        cls,
        invite_to: UserModel,
        invite_token: str,
        is_superuser: bool,
    ) -> bool:

        """ Sent always to trigger the sending of an invitation email
            is_superuser may be "master account" for tenant """

        return cls._track(
            user_id=invite_to.id,
            event=UserAnalyticsEvent.invited,
            properties={
                'text': 'Invitation sent by email',
                'first_name': invite_to.first_name,
                'last_name': invite_to.last_name,
                'email': invite_to.email,
                'invite_token': invite_token,
                'account_id': invite_to.account_id,
                'category': EventCategory.users,
            },
            is_superuser=False,
        )

    @classmethod
    def users_joined(
        cls,
        user: UserModel,
    ) -> bool:
        return cls._track(
            user_id=user.id,
            event=UserAnalyticsEvent.joined,
            is_superuser=False,
            properties={
                'text': 'Accepted the invitation',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.users,
            },
        )

    @classmethod
    def workflows_terminated(
        cls,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.terminated,
            is_superuser=is_superuser,
            properties={
                'text': f'{workflow.name} (id: {workflow.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'category': EventCategory.workflows,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def workflows_ended(
        cls,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.ended,
            is_superuser=is_superuser,
            properties={
                'text': f'{workflow.name} (id: {workflow.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'category': EventCategory.workflows,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def templates_kickoff_created(
        cls,
        user: UserModel,
        template: Template,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.kickoff_created,
            is_superuser=is_superuser,
            properties={
                'text': f'{template.name} (id: {template.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def templates_kickoff_updated(
        cls,
        user: UserModel,
        template: Template,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.kickoff_edited,
            is_superuser=is_superuser,
            properties={
                'text': f'{template.name} (id: {template.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def templates_created(
        cls,
        user: UserModel,
        template: Template,
        is_superuser: bool,
        auth_type: AuthTokenType,
        kickoff_fields_count: int,
        tasks_count: int,
        tasks_fields_count: int,
        delays_count: int,
        due_in_count: int,
        conditions_count: int,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.created,
            is_superuser=is_superuser,
            properties={
                'text': f'{template.name} (id: {template.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'is_active': template.is_active,
                'is_public': template.is_public,
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

    @classmethod
    def templates_updated(
        cls,
        user: UserModel,
        template: Template,
        is_superuser: bool,
        auth_type: AuthTokenType,
        kickoff_fields_count: int,
        tasks_count: int,
        tasks_fields_count: int,
        delays_count: int,
        due_in_count: int,
        conditions_count: int,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.updated,
            is_superuser=is_superuser,
            properties={
                'text': f'{template.name} (id: {template.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'is_active': template.is_active,
                'is_public': template.is_public,
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

    @classmethod
    def templates_deleted(
        cls,
        user: UserModel,
        template: Template,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.deleted,
            is_superuser=is_superuser,
            properties={
                'text': f'{template.name} (id: {template.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': template.id,
                'name': template.name,
                'type': template.type,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def templates_task_due_date_created(
        cls,
        user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
        task: TaskTemplate,
        template: Template,
    ):
        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.due_date_created,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{template.name} (id: {template.id}). '
                    f'Step: "{task.name}" '
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'template_id': template.id,
                'template_name': template.name,
                'task_number': task.number,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def templates_task_condition_created(
        cls,
        user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
        task: TaskTemplate,
        condition: ConditionTemplate,
        template: Template,
    ):
        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.condition_created,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{template.name} (id: {template.id}). '
                    f'Step: "{task.name}" '
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'template_id': template.id,
                'template_name': template.name,
                'task_number': task.number,
                'condition_id': condition.id,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def users_guest_invite_sent(
        cls,
        task: Task,
        invite_from: UserModel,
        invite_to: UserModel,
        current_url: str,
        is_superuser: bool,
    ) -> bool:
        return cls._track(
            user_id=invite_from.id,
            event=UserAnalyticsEvent.guest_invite_sent,
            properties={
                'text': (
                    f'Invited a guest "{invite_to.email}" '
                    f'to the the task "{task.name}" (id: {task.id})'
                ),
                'email': invite_from.email,
                'first_name': invite_from.first_name,
                'last_name': invite_from.last_name,
                'account_id': invite_from.account_id,
                'invitee_email': invite_to.email,
                'category': EventCategory.users,
                'current_url': current_url,
            },
            is_superuser=is_superuser,
        )

    @classmethod
    def users_guest_invited(
        cls,
        invite_from: UserModel,
        invite_to: UserModel,
        is_superuser: bool,
    ) -> bool:

        """ Sent always to trigger the sending of an invitation email
            is_superuser may be "master account" for tenant """

        return cls._track(
            user_id=invite_to.id,
            event=UserAnalyticsEvent.guest_invited,
            properties={
                'text': 'Guest invitation sent by email',
                'email': invite_from.email,
                'first_name': invite_from.first_name,
                'last_name': invite_from.last_name,
                'account_id': invite_from.account_id,
                'invite_to_email': invite_to.email,
                'category': EventCategory.users,
            },
            is_superuser=is_superuser,
        )

    @classmethod
    def users_transferred(
        cls,
        user: UserModel,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=UserAnalyticsEvent.transferred,
            properties={
                'text': 'User transfer accepted',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.users,
            },
        )

    @classmethod
    def users_invite_accepted(
        cls,
        user_id: int,
        invited_user: UserModel,
        is_superuser: bool,
    ) -> bool:
        return cls._track(
            user_id=user_id,
            event=UserAnalyticsEvent.invite_accepted,
            properties={
                'text': 'User invitation accepted',
                'email': invited_user.email,
                'first_name': invited_user.first_name,
                'last_name': invited_user.last_name,
                'account_id': invited_user.account_id,
                'category': EventCategory.users,
                'invitee': {
                    'email': invited_user.email,
                    'full_name': invited_user.get_full_name(),
                },
            },
            is_superuser=is_superuser,
        )

    @classmethod
    def users_digest(
        cls,
        user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=user.id,
            event=UserAnalyticsEvent.digest,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.users,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def workflows_started(
        cls,
        workflow: Workflow,
        auth_type: AuthTokenType,
        is_superuser: bool,
        user: Optional[UserModel] = None,
        anonymous_id: Optional[str] = None,
    ) -> bool:

        if not user and not anonymous_id:
            raise exceptions.InvalidUserCredentials()

        if auth_type in AuthTokenType.EXTERNAL_TYPES:
            label = Label.external_workflow
        else:
            label = Label.internal_workflow

        params = {
            'event': WorkflowAnalyticsEvent.started,
            'is_superuser': is_superuser,
            'properties': {
                'text': f'{workflow.name} (id: {workflow.id})',
                'email': None,
                'first_name': None,
                'last_name': None,
                'account_id': workflow.account_id,
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'category': EventCategory.workflows,
                'auth_type': auth_type,
                'label': label,
            },
        }
        if user:
            params['user_id'] = user.id
            params['properties']['first_name'] = user.first_name
            params['properties']['last_name'] = user.last_name
            params['properties']['email'] = user.email
        else:
            params['anonymous_id'] = anonymous_id

        return cls._track(**params)

    @classmethod
    def workflows_urgent(
        cls,
        workflow: Workflow,
        auth_type: AuthTokenType,
        is_superuser: bool,
        user: UserModel,
        action: WorkflowActions,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.urgent,
            is_superuser=is_superuser,
            properties={
                'text': f'{workflow.name} (id: {workflow.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'auth_type': auth_type,
                'category': EventCategory.workflows,
                'label': Label.urgent,
                'action': action,
            },
        )

    @classmethod
    def workflows_updated(
        cls,
        user: UserModel,
        workflow: Workflow,
        auth_type: AuthTokenType,
        is_superuser: bool,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.updated,
            is_superuser=is_superuser,
            properties={
                'text': f'{workflow.name} (id: {workflow.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': workflow.id,
                'name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'category': EventCategory.workflows,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def search_search(
        cls,
        user: UserModel,
        page: str,
        search_text: str,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=user.id,
            event=SearchAnalyticsEvent.search,
            is_superuser=is_superuser,
            properties={
                'text': f'Page: "{page}". Search text: "{search_text}"',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'page': page,
                'search_text': search_text,
                'category': EventCategory.search,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def attachments_uploaded(
        cls,
        attachment: FileAttachment,
        is_superuser: bool,
        auth_type: AuthTokenType,
        user: Optional[UserModel] = None,
        anonymous_id: Optional[str] = None,
    ):

        if not user.is_authenticated and not anonymous_id:
            raise exceptions.InvalidUserCredentials()

        analytics_data = {
            'event': AttachmentAnalyticsEvent.uploaded,
            'is_superuser': is_superuser,
            'properties': {
                'text': f'{attachment.name} {attachment.url}',
                'email': None,
                'first_name': None,
                'last_name': None,
                'account_id': attachment.account_id,
                'auth_type': auth_type,
                'id': attachment.id,
                'size': attachment.humanize_size,
                'category': EventCategory.attachments,
                'type': attachment.extension,
            },
        }
        if user.is_authenticated:
            analytics_data['user_id'] = user.id
            analytics_data['properties']['email'] = user.email
            analytics_data['properties']['first_name'] = user.first_name
            analytics_data['properties']['last_name'] = user.last_name
        else:
            analytics_data['anonymous_id'] = anonymous_id
        return cls._track(**analytics_data)

    @classmethod
    def templates_integrated(
        cls,
        template_id: int,
        account_id: int,
        integration_type: TemplateIntegrationType.LITERALS,
        user: Optional[UserModel] = None,
        anonymous_id: Optional[str] = None,
        is_superuser: bool = False,
    ) -> bool:

        if not user and not anonymous_id:
            raise exceptions.InvalidUserCredentials()

        params = {
            'event': TemplateAnalyticsEvent.integrated,
            'is_superuser': is_superuser,
            'properties': {
                'text': (
                    f'Template id: {template_id}. '
                    f'Integration type: "{integration_type}"'
                ),
                'email': None,
                'first_name': None,
                'last_name': None,
                'account_id': account_id,
                'template_id': template_id,
                'integration_type': integration_type,
                'category': EventCategory.templates,
            },
        }
        if user:
            params['user_id'] = user.id
            params['properties']['email'] = user.email
            params['properties']['first_name'] = user.first_name
            params['properties']['last_name'] = user.last_name
        else:
            params['anonymous_id'] = anonymous_id

        return cls._track(**params)

    @classmethod
    def accounts_webhooks_subscribed(
        cls,
        user: UserModel,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=AccountAnalyticsEvent.webhooks_subscribed,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.accounts,
            },
        )

    @classmethod
    def checklist_created(
        cls,
        user: UserModel,
        template: Template,
        task: TaskTemplate,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.checklist_created,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{template.name} (id: {template.id}). '
                    f'Step: "{task.name}" '
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': template.id,
                'name': template.name,
                'task_number': task.number,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def workflow_delayed(
        cls,
        user: UserModel,
        duration: timedelta,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ) -> bool:

        return cls._track(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.delayed,
            is_superuser=is_superuser,
            properties={
                'text': f'{workflow.name} (id: {workflow.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': workflow.id,
                'duration': duration.days,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'category': EventCategory.workflows,
                'auth_type': auth_type,
                'label': Label.delayed,
                'action': WorkflowActions.delayed,
            },
        )

    @classmethod
    def subscription_created(
        cls,
        user: UserModel,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.created,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.subscriptions,
                'quantity': user.account.max_users,
                'plan_code': user.account.billing_plan,
            },
        )

    @classmethod
    def subscription_updated(
        cls,
        user: UserModel,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.updated,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'category': EventCategory.subscriptions,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'quantity': user.account.max_users,
                'plan_code': user.account.billing_plan,
            },
        )

    @classmethod
    def subscription_converted(
        cls,
        user: UserModel,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.converted,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.subscriptions,
                'quantity': user.account.max_users,
                'plan_code': user.account.billing_plan,
            },
        )

    @classmethod
    def subscription_expired(
        cls,
        user: UserModel,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.expired,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.subscriptions,
            },
        )

    @classmethod
    def subscription_canceled(
        cls,
        user: UserModel,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.canceled,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account.id,
                'category': EventCategory.subscriptions,
            },
        )

    @classmethod
    def trial_subscription_created(
        cls,
        user: UserModel,
        is_superuser: bool = False,
    ):

        return cls._track(
            user_id=user.id,
            event=SubscriptionAnalyticsEvent.trial,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.subscriptions,
                'quantity': user.account.max_users,
                'plan_code': user.account.billing_plan,
            },
        )

    @classmethod
    def task_returned(
        cls,
        user: UserModel,
        task: Task,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=TaskAnalyticsEvent.returned,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{task.workflow.name} (id: {task.workflow.id}). '
                    f'Task: "{task.name}" (id: {task.id}). '
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'workflow_id': task.workflow.id,
                'workflow_name': task.workflow.name,
                'task_name': task.name,
                'task_id': task.id,
                'category': EventCategory.tasks,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def workflow_returned(
        cls,
        user: UserModel,
        task: Task,
        workflow: Workflow,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):

        return cls._track(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.returned,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}) '
                    f'has been returned to '
                    f'task "{task.name}" (id: {task.id}). '
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'returned_to_task': task.name,
                'category': EventCategory.workflows,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def template_generation_init(
        cls,
        success: bool,
        user: UserModel,
        description: str,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.generation_init,
            is_superuser=is_superuser,
            properties={
                'text': f'Prompt: {description}',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'request description': description,
                'category': EventCategory.templates,
                'label': Label.template_generation,
                'auth_type': auth_type,
                'success': success,
            },
        )

    @classmethod
    def template_generated_from_landing(
        cls,
        user: UserModel,
        template: Template,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.generated_from_landing,
            is_superuser=is_superuser,
            properties={
                'text': f'{template.name} (id: {template.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': template.id,
                'category': EventCategory.templates,
                'label': Label.template_generation,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def template_created_from_landing_library(
        cls,
        user: UserModel,
        template: Template,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):
        return cls._track(
            user_id=user.id,
            event=TemplateAnalyticsEvent.created_from_landing_library,
            is_superuser=is_superuser,
            properties={
                'text': f'{template.name} (id: {template.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': template.id,
                'template_name': template.name,
                'category': EventCategory.templates,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def task_completed(
        cls,
        user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
        task: Task,
        workflow: Workflow,
    ):
        cls._track(
            user_id=user.id,
            event=TaskAnalyticsEvent.completed,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Task: "{task.name}" (id: {task.id}). '
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'task_name': task.name,
                'task_id': task.id,
                'category': EventCategory.tasks,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def workflow_completed(
        cls,
        user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
        workflow: Workflow,
    ):
        cls._track(
            user_id=user.id,
            event=WorkflowAnalyticsEvent.completed,
            is_superuser=is_superuser,
            properties={
                'text': f'{workflow.name} (id: {workflow.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': workflow.id,
                'workflow_name': workflow.name,
                'template_id': workflow.template_id,
                'template_name': workflow.get_template_name(),
                'category': EventCategory.workflows,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def library_template_opened(
        cls,
        user: UserModel,
        sys_template: SystemTemplate,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ) -> bool:

        if sys_template.category_id:
            category_name = sys_template.category.name
        else:
            category_name = None
        return cls._track(
            user_id=user.id,
            event=LibraryTemplateAnalyticsEvent.opened,
            is_superuser=is_superuser,
            properties={
                'text': f'{sys_template.name} (id: {sys_template.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'id': sys_template.id,
                'template_name': sys_template.name,
                'template_category': category_name,
                'category': EventCategory.templates,
                'label': Label.library_template_opened,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def account_created(
        cls,
        user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        signup_data = user.get_account_signup_data()
        return cls._track(
            user_id=user.id,
            event=AccountAnalyticsEvent.created,
            is_superuser=is_superuser,
            properties={
                'text': f'{user.account.name} (id: {user.account.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.accounts,
                'auth_type': auth_type,
                **signup_data.as_dict(),
            },
        )

    @classmethod
    def account_verified(
        cls,
        user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        signup_data = user.get_account_signup_data()
        return cls._track(
            user_id=user.id,
            event=AccountAnalyticsEvent.verified,
            is_superuser=is_superuser,
            properties={
                'text': f'{user.account.name} (id: {user.account.id})',
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'account_id': user.account_id,
                'category': EventCategory.accounts,
                'auth_type': auth_type,
                **signup_data.as_dict(),
            },
        )

    @classmethod
    def tenants_added(
        cls,
        master_user: UserModel,
        tenant_account: Account,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=master_user.id,
            event=TenantsAnalyticsEvent.added,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{tenant_account.tenant_name} '
                    f'(id: {tenant_account.id})'
                ),
                'first_name': master_user.first_name,
                'last_name': master_user.last_name,
                'email': master_user.email,
                'account_id': master_user.account_id,
                'tenant_id': tenant_account.id,
                'category': EventCategory.tenants,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def tenants_accessed(
        cls,
        master_user: UserModel,
        tenant_account: Account,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=master_user.id,
            event=TenantsAnalyticsEvent.accessed,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{tenant_account.tenant_name} '
                    f'(id: {tenant_account.id})'
                ),
                'first_name': master_user.first_name,
                'last_name': master_user.last_name,
                'email': master_user.email,
                'account_id': master_user.account_id,
                'tenant_id': tenant_account.id,
                'category': EventCategory.tenants,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def mentions_created(
        cls,
        text: str,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=user.id,
            event=MentionsAnalyticsEvent.created,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Text: "{text}"'
                ),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.mentions,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def comment_added(
        cls,
        text: str,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=user.id,
            event=CommentAnalyticsEvent.added,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Text: "{text}"'
                ),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def comment_edited(
        cls,
        text: str,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=user.id,
            event=CommentAnalyticsEvent.edited,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Text: "{text}"'
                ),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def comment_deleted(
        cls,
        text: str,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=user.id,
            event=CommentAnalyticsEvent.deleted,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Text: "{text}"'
                ),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def comment_reaction_added(
        cls,
        text: str,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=user.id,
            event=CommentAnalyticsEvent.reaction_added,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Reaction: "{text}"'
                ),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def comment_reaction_deleted(
        cls,
        text: str,
        user: UserModel,
        workflow: Workflow,
        is_superuser: bool,
        auth_type: AuthTokenType,
    ):
        return cls._track(
            user_id=user.id,
            event=CommentAnalyticsEvent.reaction_deleted,
            is_superuser=is_superuser,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Reaction: "{text}"'
                ),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'category': EventCategory.comments,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def users_logged_in(
        cls,
        user: UserModel,
        is_superuser: bool,
        auth_type: AuthTokenType,
        source: SourceType,
    ):
        return cls._track(
            user_id=user.id,
            event=UserAnalyticsEvent.logged_in,
            is_superuser=is_superuser,
            properties={
                'text': '',
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'account_id': user.account_id,
                'category': EventCategory.users,
                'auth_type': auth_type,
                'source': source,
            },
        )

    @classmethod
    def groups_created(
        cls,
        user_id: int,
        user_email: str,
        user_first_name: str,
        user_last_name: str,
        group_photo: Optional[str],
        group_users: Optional[List[int]],
        account_id: int,
        group_id: int,
        group_name: str,
        auth_type: AuthTokenType,
        text: str,
        is_superuser: bool,
    ) -> bool:
        return cls._track(
            user_id=user_id,
            event=GroupsAnalyticsEvent.created,
            is_superuser=is_superuser,
            properties={
                'text': text,
                'email': user_email,
                'first_name': user_first_name,
                'last_name': user_last_name,
                'photo': group_photo,
                'users': group_users,
                'account_id': account_id,
                'id': group_id,
                'name': group_name,
                'category': EventCategory.groups,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def groups_deleted(
        cls,
        user_id: int,
        user_email: str,
        user_first_name: str,
        user_last_name: str,
        group_photo: Optional[str],
        group_users: Optional[List[int]],
        account_id: int,
        group_id: int,
        group_name: str,
        auth_type: AuthTokenType,
        text: str,
        is_superuser: bool,
    ) -> bool:
        return cls._track(
            user_id=user_id,
            event=GroupsAnalyticsEvent.deleted,
            is_superuser=is_superuser,
            properties={
                'text': text,
                'email': user_email,
                'first_name': user_first_name,
                'last_name': user_last_name,
                'photo': group_photo,
                'users': group_users,
                'account_id': account_id,
                'id': group_id,
                'name': group_name,
                'category': EventCategory.groups,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def groups_updated(
        cls,
        user_id: int,
        user_email: str,
        user_first_name: str,
        user_last_name: str,
        group_photo: Optional[str],
        group_users: Optional[List[int]],
        account_id: int,
        group_id: int,
        group_name: str,
        auth_type: AuthTokenType,
        text: str,
        is_superuser: bool,
    ) -> bool:
        return cls._track(
            user_id=user_id,
            event=GroupsAnalyticsEvent.updated,
            is_superuser=is_superuser,
            properties={
                'text': text,
                'email': user_email,
                'first_name': user_first_name,
                'last_name': user_last_name,
                'photo': group_photo,
                'users': group_users,
                'account_id': account_id,
                'id': group_id,
                'name': group_name,
                'category': EventCategory.groups,
                'auth_type': auth_type,
            },
        )

    @classmethod
    def task_performer_created(
        cls,
        user: UserModel,
        performer: UserModel,
        task: Task,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):
        workflow = task.workflow
        return cls._track(
            user_id=user.id,
            event=TaskAnalyticsEvent.performer_created,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Task: "{task.name}" (id: {task.id}). '
                    f'{performer.name_by_status} assigned as performer'
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'performer_id': performer.id,
                'performer_name': performer.name_by_status,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'task_id': task.id,
                'task_name': task.name,
                'category': EventCategory.tasks,
                'auth_type': auth_type,
            },
            is_superuser=is_superuser,
        )

    @classmethod
    def task_performer_deleted(
        cls,
        user: UserModel,
        performer: UserModel,
        task: Task,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):
        workflow = task.workflow
        return cls._track(
            user_id=user.id,
            event=TaskAnalyticsEvent.performer_deleted,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Task: "{task.name}" (id: {task.id}). '
                    f'{performer.name_by_status} removed from performers'
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'performer_id': performer.id,
                'performer_name': performer.name_by_status,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'task_id': task.id,
                'task_name': task.name,
                'category': EventCategory.tasks,
                'auth_type': auth_type,
            },
            is_superuser=is_superuser,
        )

    @classmethod
    def task_group_performer_created(
        cls,
        user: UserModel,
        performer: UserGroup,
        task: Task,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):
        workflow = task.workflow
        return cls._track(
            user_id=user.id,
            event=TaskAnalyticsEvent.group_performer_created,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Task: "{task.name}" (id: {task.id}). '
                    f'{performer.name} assigned as performer'
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'performer_id': performer.id,
                'performer_name': performer.name,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'task_id': task.id,
                'task_name': task.name,
                'category': EventCategory.tasks,
                'auth_type': auth_type,
            },
            is_superuser=is_superuser,
        )

    @classmethod
    def task_group_performer_deleted(
        cls,
        user: UserModel,
        performer: UserGroup,
        task: Task,
        auth_type: AuthTokenType,
        is_superuser: bool = False,
    ):
        workflow = task.workflow
        return cls._track(
            user_id=user.id,
            event=TaskAnalyticsEvent.group_performer_deleted,
            properties={
                'text': (
                    f'{workflow.name} (id: {workflow.id}). '
                    f'Task: "{task.name}" (id: {task.id}). '
                    f'{performer.name} removed from performers'
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'performer_id': performer.id,
                'performer_name': performer.name,
                'account_id': user.account_id,
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'task_id': task.id,
                'task_name': task.name,
                'category': EventCategory.tasks,
                'auth_type': auth_type,
            },
            is_superuser=is_superuser,
        )
