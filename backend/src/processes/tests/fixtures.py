from datetime import datetime, timedelta
from typing import List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.accounts.enums import (
    BillingPlanType,
    Language,
    LeaseLevel,
    UserDateFormat,
    UserFirstDayWeek,
    UserInviteStatus,
    UserStatus,
)
from src.accounts.models import (
    Account,
    AccountSignupData,
    UserGroup,
    UserInvite,
)
from src.accounts.services.guests import GuestService
from src.authentication.enums import AuthTokenType
from src.payment.enums import BillingPeriod
from src.processes.enums import (
    ConditionAction,
    FieldType,
    OwnerType,
    PerformerType,
    PredicateOperator,
    PredicateType,
    TaskStatus,
    TemplateType,
    WorkflowEventType,
    WorkflowStatus,
)
from src.processes.models.templates.checklist import (
    ChecklistTemplate,
    ChecklistTemplateSelection,
)
from src.processes.models.templates.conditions import (
    ConditionTemplate,
    PredicateTemplate,
    RuleTemplate,
)
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.preset import (
    TemplatePreset,
    TemplatePresetField,
)
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.conditions import (
    Condition,
    Predicate,
    Rule,
)
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.fields import (
    TaskField,
)
from src.processes.models.workflows.kickoff import KickoffValue
from src.processes.models.workflows.task import Task
from src.processes.models.workflows.workflow import Workflow
from src.processes.serializers.templates.template import (
    TemplateSerializer,
)
from src.processes.services.tasks.task import TaskService
from src.utils.salt import get_salt
from src.webhooks.enums import HookEvent
from src.webhooks.models import WebHook

UserModel = get_user_model()


def create_test_account(
    name: Optional[str] = 'Test Company',
    max_users: int = settings.DEFAULT_MAX_USERS,
    lease_level: LeaseLevel.LITERALS = LeaseLevel.STANDARD,
    logo_sm: Optional[str] = None,
    logo_lg: Optional[str] = None,
    master_account: Optional[Account] = None,
    plan: Optional[BillingPlanType.LITERALS] = BillingPlanType.FREEMIUM,
    period: Optional[BillingPeriod.LITERALS] = None,
    plan_expiration: Optional[datetime] = None,
    stripe_id: Optional[str] = None,
    trial_ended: bool = False,
    trial_start: Optional[datetime] = None,
    trial_end: Optional[datetime] = None,
    tmp_subscription: bool = False,
    tenant_name: Optional[str] = None,
    is_verified: bool = True,
    billing_sync: bool = True,
    log_api_requests: bool = False,
):
    plan_expiration = plan_expiration or (
        None if plan == BillingPlanType.FREEMIUM
        else timezone.now() + timedelta(days=1)
    )

    period = period or (
        None if plan == BillingPlanType.FREEMIUM
        else BillingPeriod.MONTHLY
    )

    if lease_level == LeaseLevel.TENANT and not master_account:
        master_account = create_test_account(
            plan=BillingPlanType.PREMIUM,
            plan_expiration=plan_expiration,
            period=period,
            name='master',
            billing_sync=billing_sync,
        )
        plan = master_account.billing_plan
        plan_expiration = master_account.plan_expiration
        period = master_account.billing_period

    account = Account.objects.create(
        name=name,
        tenant_name=tenant_name,
        billing_plan=plan,
        billing_period=period,
        max_users=max_users,
        plan_expiration=plan_expiration,
        lease_level=lease_level,
        logo_sm=logo_sm,
        logo_lg=logo_lg,
        master_account=master_account,
        stripe_id=stripe_id,
        trial_ended=trial_ended,
        trial_start=trial_start,
        trial_end=trial_end,
        tmp_subscription=tmp_subscription,
        is_verified=is_verified,
        billing_sync=billing_sync,
        log_api_requests=log_api_requests,
    )
    AccountSignupData.objects.create(account=account)
    return account


def create_test_user(
    email: str = 'test@pneumatic.app',
    account: Optional[Account] = None,
    is_staff: bool = True,
    is_admin: bool = True,
    is_account_owner: bool = True,
    status: UserStatus.LITERALS = UserStatus.ACTIVE,
    first_name='John',
    last_name='Doe',
    phone: str = '79999999999',
    photo: Optional[str] = None,
    is_new_tasks_subscriber: bool = True,
    is_complete_tasks_subscriber: bool = True,
    tz: str = settings.TIME_ZONE,
    language: Language.LITERALS = settings.LANGUAGE_CODE,
    date_fmt: str = UserDateFormat.PY_USA_12,
    date_fdw: int = UserFirstDayWeek.SUNDAY,
) -> UserModel:

    """ Instead of this method use:
        - create_test_owner
        - create_test_admin
        - create_test_not_admin """

    account = account or create_test_account()
    return UserModel.objects.create(
        account=account,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        is_admin=is_admin,
        is_staff=is_staff,
        is_account_owner=is_account_owner,
        status=status,
        photo=photo,
        is_new_tasks_subscriber=is_new_tasks_subscriber,
        is_complete_tasks_subscriber=is_complete_tasks_subscriber,
        timezone=tz,
        language=language,
        date_fmt=date_fmt,
        date_fdw=date_fdw,
    )


def create_test_owner(**kwargs) -> UserModel:
    kwargs['is_account_owner'] = True
    kwargs['is_admin'] = True
    kwargs['email'] = kwargs.get('email', 'owner@pneumatic.app')
    return create_test_user(**kwargs)


def create_test_admin(*args, **kwargs) -> UserModel:
    kwargs['is_account_owner'] = False
    kwargs['is_admin'] = True
    kwargs['email'] = kwargs.get('email', 'admin@pneumatic.app')
    return create_test_user(**kwargs)


def create_test_not_admin(*args, **kwargs) -> UserModel:
    kwargs['is_account_owner'] = False
    kwargs['is_admin'] = False
    kwargs['email'] = kwargs.get('email', 'not_admin@pneumatic.app')
    return create_test_user(**kwargs)


def create_test_guest(
    email: str = 'guest@pneumatic.app',
    account: Optional[Account] = None,
):
    account = account or create_test_account()
    return GuestService.create(
        email=email,
        account_id=account.id,
    )


def create_invited_user(
    user: UserModel,
    email: str = 'test1@pneumatic.app',
    is_admin: bool = True,
    first_name='',
    last_name='',
    status: UserStatus = UserStatus.INVITED,
):
    invited_user = UserModel.objects.create(
        account=user.account,
        email=email,
        phone='79999999999',
        status=status,
        is_admin=is_admin,
        first_name=first_name,
        last_name=last_name,
    )
    user_invite = UserInvite(
        email=email,
        account=user.account,
        invited_by=user,
        invited_user=invited_user,
    )
    if status == UserStatus.ACTIVE:
        user_invite.status = UserInviteStatus.ACCEPTED
    else:
        user_invite.status = UserInviteStatus.PENDING
    user_invite.save()
    return invited_user


def create_checklist_template(
    task_template: TaskTemplate,
    selections_count: int = 1,
    api_name_prefix: Optional[str] = None,
) -> ChecklistTemplate:
    if api_name_prefix is None:
        api_name_prefix = ''
    checklist_template = ChecklistTemplate.objects.create(
        template=task_template.template,
        task=task_template,
        api_name=f'{api_name_prefix}checklist',
    )
    for num in range(1, selections_count + 1):
        ChecklistTemplateSelection.objects.create(
            checklist=checklist_template,
            template=task_template.template,
            value=f'some value {num}',
            api_name=f'{api_name_prefix}cl-selection-{num}',
        )
    return checklist_template


def create_test_template(
    user: UserModel,
    with_delay: bool = False,
    is_active: bool = False,
    is_public: bool = False,
    is_embedded: bool = False,
    finalizable: bool = False,
    kickoff: Optional[Kickoff] = None,
    tasks_count: int = 3,
    name: str = 'Test workflow',
    type_: str = TemplateType.CUSTOM,
    wf_name_template: Optional[str] = None,
    description: str = 'Test desc',
    reminder_notification: bool = False,
    completion_notification: bool = False,
) -> Template:

    account = user.account
    template = Template.objects.create(
        name=name,
        finalizable=finalizable,
        account=account,
        description=description,
        is_public=is_public,
        is_embedded=is_embedded,
        type=type_,
        wf_name_template=wf_name_template,
        reminder_notification=reminder_notification,
        completion_notification=completion_notification,
    )
    if kickoff is None:
        Kickoff.objects.create(
            template=template,
            account=account,
        )
    else:
        kickoff.template = template
        kickoff.save()
    TemplateOwner.objects.create(
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=user.id,
    )
    if tasks_count:
        parents = []
        for number in range(1, tasks_count + 1):
            data = {
                'name': f'Task №{number}',
                'number': number,
                'template': template,
                'account': account,
                'parents': parents,
            }
            if with_delay and number > 1:
                data['delay'] = '00:00:01'
            task_template = TaskTemplate.objects.create(**data)
            task_template.add_raw_performer(user)
            if number > 1:
                condition_template = ConditionTemplate.objects.create(
                    task=task_template,
                    action=ConditionAction.START_TASK,
                    order=0,
                    template=template,
                )
                rule = RuleTemplate.objects.create(
                    condition=condition_template,
                    template=template,
                )
                PredicateTemplate.objects.create(
                    rule=rule,
                    operator=PredicateOperator.COMPLETED,
                    field_type=PredicateType.TASK,
                    field=parents[0],
                    value=None,
                    template=template,
                )
            parents = [task_template.api_name]

    slz = TemplateSerializer(
        instance=template,
        context={
            'user': user,
            'account': user.account,
            'is_superuser': False,
            'auth_type': AuthTokenType.USER,
        },
    )
    slz.initial_data = slz.data
    slz.save_as_draft()
    template.is_active = is_active
    template.save()
    return template


def create_test_workflow(
    user: UserModel,
    template: Optional[Template] = None,
    with_delay: bool = False,
    tasks_count: int = 3,
    active_task_number: int = 1,
    is_external: bool = False,
    is_urgent: bool = False,
    finalizable: bool = False,
    name: Optional[str] = None,
    name_template: Optional[str] = None,
    status: int = WorkflowStatus.RUNNING,
    due_date: Optional[datetime] = None,
    ancestor_task: Optional[Task] = None,
    description: Optional[str] = None,
) -> Workflow:
    custom_template = template is not None
    if not custom_template:
        template = create_test_template(
            user=user,
            with_delay=with_delay,
            tasks_count=tasks_count,
            is_active=True,
            is_public=is_external,
            finalizable=finalizable,
        )
    workflow_starter = None if is_external else user
    if status == WorkflowStatus.DONE:
        date_completed = timezone.now() + timedelta(hours=1)
    else:
        date_completed = None
    workflow = Workflow.objects.create(
        name=name or template.name,
        name_template=name_template,
        description=description,
        account=template.account,
        template=template,
        status=status,
        status_updated=timezone.now(),
        date_completed=date_completed,
        workflow_starter=workflow_starter,
        is_external=is_external,
        is_urgent=is_urgent,
        finalizable=template.finalizable,
        due_date=due_date,
        ancestor_task=ancestor_task,
        reminder_notification=template.reminder_notification,
        completion_notification=template.completion_notification,
    )
    if custom_template:
        template_owners_ids = Template.objects.filter(
            id=template.id,
        ).get_owners_as_users()
        workflow.owners.set(template_owners_ids)
        workflow.members.add(*template_owners_ids)
    else:
        workflow.members.add(*set(
            template.owners.values_list('user_id', flat=True),
        ))
        workflow.owners.add(*set(
            template.owners.values_list('user_id', flat=True),
        ))

    KickoffValue.objects.create(
        workflow=workflow,
        account=workflow.account,
    )
    now_date = timezone.now()
    for task_template in template.tasks.all():
        task_service = TaskService(user=user)
        task = task_service.create(
            instance_template=task_template,
            workflow=workflow,
        )

        # emulate run workflow
        if task.number == active_task_number:
            task.date_first_started = now_date
            task.date_started = now_date
            task.status = TaskStatus.ACTIVE
            task.save(
                update_fields=['date_first_started', 'date_started', 'status'],
            )
            task.update_performers()
        elif task.number < active_task_number:
            task.date_first_started = now_date
            task.date_started = now_date
            task.date_completed = now_date + timedelta(seconds=30)
            task.status = TaskStatus.COMPLETED
            task.save(
                update_fields=[
                    'date_first_started',
                    'date_started',
                    'date_completed',
                    'status',
                ],
            )
            task.update_performers()
            task.taskperformer_set.update(
                is_completed=True,
                date_completed=timezone.now(),
            )
        else:
            task.update_performers()
        # Create conditions
        for condition_template in task_template.conditions.all():
            condition = Condition.objects.create(
                task=task,
                action=condition_template.action,
                order=condition_template.order,
                api_name=condition_template.api_name,
            )
            for rule_template in condition_template.rules.all():
                rule = Rule.objects.create(
                    condition=condition,
                    api_name=rule_template.api_name,
                )
                for predicate_template in rule_template.predicates.all():
                    Predicate.objects.create(
                        rule=rule,
                        operator=predicate_template.operator,
                        field_type=predicate_template.field_type,
                        value=predicate_template.value,
                        field=predicate_template.field,
                        api_name=predicate_template.api_name,
                    )

        now_date += timedelta(seconds=60)
    return workflow


def get_workflow_create_data(user):
    return {
        'name': 'Test workflow',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'description': 'Test workflow description',
        'kickoff': {
            'fields': [
                {
                    'type': FieldType.STRING,
                    'name': 'Test',
                    'api_name': 'string-field-1',
                    'order': 0,
                },
            ],
        },
        'tasks': [
            {
                'name': 'First {{string-field-1}}',
                'number': 1,
                'api_name': 'task-1-api-name',
                'raw_performers': [{
                    'type': PerformerType.USER,
                    'source_id': user.id,
                }],
            },
            {
                'name': 'Second',
                'number': 2,
                'api_name': 'task-2-api-name',
                'raw_performers': [{
                    'type': PerformerType.USER,
                    'source_id': user.id,
                }],
                'fields': [
                    {
                        'type': FieldType.TEXT,
                        'name': 'Test',
                        'order': 0,
                    },
                ],
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field': 'task-1-api-name',
                                      'field_type': PredicateType.TASK,
                                      'operator': PredicateOperator.COMPLETED,
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                'name': 'Third',
                'number': 3,
                'raw_performers': [{
                    'type': PerformerType.USER,
                    'source_id': user.id,
                }],
                'conditions': [
                    {
                        'order': 1,
                        'action': ConditionAction.START_TASK,
                        'rules': [
                            {
                                'predicates': [
                                    {
                                      'field': 'task-2-api-name',
                                      'field_type': PredicateType.TASK,
                                      'operator': PredicateOperator.COMPLETED,
                                      'value': None,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }


def create_test_attachment(
    account: Account,
    workflow: Optional[Workflow] = None,
    event: Optional[WorkflowEvent] = None,
    field: Optional[TaskField] = None,
    name: str = 'file.jpg',
    size: int = 215678,
):
    filename = f'{get_salt(30)}_{name}'
    thumb_filename = f'thumb_{filename}'
    attachment = FileAttachment(
        account=account,
        workflow=workflow,
        name=filename,
        url=f'https://link.to/{filename}',
        thumbnail_url=f'https://link.to/{thumb_filename}',
        size=size,
    )
    if event:
        attachment.event = event
        event.with_attachments = True
        event.save()
    if field:
        attachment.field = field
    attachment.save()
    return attachment


def create_test_event(
    workflow: Workflow,
    user: UserModel,
    type_event: Optional[WorkflowEventType] = WorkflowEventType.RUN,
    data_create: Optional[datetime] = None,
):
    task = workflow.tasks.get(number=1)
    event = WorkflowEvent.objects.create(
        type=type_event,
        account=workflow.account,
        workflow=workflow,
        user=user,  # For highlights
        task=task,
    )
    if data_create:
        event.created = data_create
        event.save()
    return event


def create_test_group(
    account: Account,
    name: str = 'Group_test',
    photo: Optional[str] = None,
    users: Optional[List[UserModel]] = None,
):
    group = UserGroup.objects.create(
        name=name,
        photo=photo,
        account=account,
    )
    if users:
        group.users.set(users)
    group.save()
    return group


def create_wf_created_webhook(user: UserModel):
    return WebHook.objects.create(
        user_id=user.id,
        event=HookEvent.WORKFLOW_STARTED,
        account_id=user.account.id,
        target='http://test.test',
    )


def create_wf_completed_webhook(user: UserModel):
    return WebHook.objects.create(
        user_id=user.id,
        event=HookEvent.WORKFLOW_COMPLETED,
        account_id=user.account.id,
        target='http://test.test',
    )


def create_task_completed_webhook(user: UserModel):
    return WebHook.objects.create(
        user_id=user.id,
        event=HookEvent.TASK_COMPLETED,
        account_id=user.account.id,
        target='http://test.test',
    )


def create_task_returned_webhook(user: UserModel):
    return WebHook.objects.create(
        user_id=user.id,
        event=HookEvent.TASK_RETURNED,
        account_id=user.account.id,
        target='http://test.test',
    )


def create_test_template_preset(
    template: Template,
    author: UserModel,
    name: str = 'Test Preset',
    is_default: bool = False,
    type: str = 'personal',  # noqa: A002
    fields: Optional[List[dict]] = None,
):
    preset = TemplatePreset.objects.create(
        template=template,
        author=author,
        account=author.account,
        name=name,
        is_default=is_default,
        type=type,
    )

    if fields:
        for field_data in fields:
            TemplatePresetField.objects.create(
                preset=preset,
                api_name=field_data['api_name'],
                order=field_data['order'],
                width=field_data['width'],
            )

    return preset
