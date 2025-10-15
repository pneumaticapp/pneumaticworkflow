# ruff: noqa: PLC0415
from datetime import datetime
from typing import Iterable, List, Optional, Union

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import (
    Avg,
    Count,
    F,
    Max,
    Prefetch,
    Q,
)

from src.accounts.enums import UserType
from src.accounts.models import UserGroup
from src.generics.querysets import (
    AccountBaseQuerySet,
    BaseHardQuerySet,
    BaseQuerySet,
)
from src.processes.enums import (
    ConditionAction,
    DirectlyStatus,
    PerformerType,
    SysTemplateType,
    TaskStatus,
    TemplateOrdering,
    TemplateType,
    WorkflowEventActionType,
    WorkflowEventType,
    WorkflowStatus,
)
from src.processes.queries import (
    RunningTaskTemplateQuery,
    TemplateExportQuery,
    TemplateListQuery,
    WorkflowListQuery,
)

UserModel = get_user_model()


class WorkflowsBaseQuerySet(AccountBaseQuerySet):

    pass


class DelayBaseQuerySet(BaseQuerySet):

    def active(self):
        return self.filter(end_date__isnull=True)


class TasksBaseQuerySet(BaseQuerySet):

    def on_raw_performer(self, user_id: int):
        return self.filter(raw_performers__user_id=user_id)

    def raw_performers_count(self, count: int):

        """ Returns tasks where count raw_performers == count """

        return self.annotate(
            raw_performers_count=Count('raw_performers'),
        ).filter(raw_performers_count=count)


class TaskTemplateQuerySet(TasksBaseQuerySet):

    def on_account(self, account_id: int):
        return self.filter(template__account_id=account_id)

    def with_tasks_in_progress(
        self,
        template_id: int,
        user_id: int,
        with_tasks_in_progress: bool,
    ):
        query = RunningTaskTemplateQuery(
            template_id=template_id,
            user_id=user_id,
        )
        return self.execute_raw(query)


class TemplateQuerySet(WorkflowsBaseQuerySet):
    def __init__(self, *args, **kwargs):
        self._custom_filter_props.add('_workflows_filters')
        self._workflows_filters = Q()
        super().__init__(*args, **kwargs)

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def public(self):
        return self.filter(is_public=True)

    def with_template_owner(self, user_id: int):
        return self.filter(
            Q(owners__type='user', owners__user_id=user_id) |
            Q(owners__type='group', owners__group__users__id=user_id),
        ).distinct()

    def get_owners_as_users(self):
        user_owners = self.filter(
            owners__type='user',
            owners__user_id__isnull=False,
        ).values_list('owners__user_id', flat=True)
        group_owners = self.filter(
            owners__type='group',
            owners__group__users__isnull=False,
            owners__group__users__id__isnull=False,
        ).prefetch_related('owners__group__users').values_list(
            'owners__group__users__id', flat=True,
        )
        return user_owners.union(group_owners)

    @transaction.atomic
    def delete(self):
        for template in self:
            template.workflows.update(
                is_legacy_template=True,
                legacy_template_name=template.name,
            )
        super().delete()

    def by_events_datetime(
        self,
        filter_,
    ):
        return self.filter(
            workflows__events__type__in=[
                WorkflowEventType.TASK_COMPLETE,
                WorkflowEventType.COMMENT,
                WorkflowEventType.RUN,
            ],
            **filter_,
        ).distinct()

    def workflows_updated_from(self, value, as_combine=False):
        filter_ = Q(workflows__status_updated__gte=value)
        return self._add_filter(filter_, as_combine, '_workflows_filters')

    def workflows_updated_to(self, value, as_combine=False):
        filter_ = Q(workflows__status_updated__lt=value)
        return self._add_filter(filter_, as_combine, '_workflows_filters')

    def avg_workflow_duration(self):
        duration = (
            F('workflow__status_updated') -
            F('workflow__date_created')
        )
        return self.annotate(avg_workflow_duration=Avg(duration))

    def onboarding_owner(self):
        return self.filter(type=TemplateType.ONBOARDING_ACCOUNT_OWNER)

    def onboarding_admin(self):
        return self.filter(type=TemplateType.ONBOARDING_ADMIN)

    def onboarding_not_admin(self):
        return self.filter(type=TemplateType.ONBOARDING_NON_ADMIN)

    def onboarding(self):
        return self.filter(type__in=TemplateType.TYPES_ONBOARDING)

    def exclude_onboarding(self):
        return self.filter(
            ~Q(type__in=TemplateType.TYPES_ONBOARDING),
        )

    def paid(self):
        return self.filter(
            Q(
                tasks__conditions__is_deleted=False,
            ) | Q(
                is_public=True,
            ),
        ).distinct('id')

    def by_workflows_status(
        self,
        status: Union[WorkflowStatus, List[WorkflowStatus]],
    ):
        filter_kwargs = {'workflows__is_deleted': False}
        if isinstance(status, Iterable):
            filter_kwargs['workflows__status__in'] = status
        else:
            filter_kwargs['workflows__status'] = status
        return self.filter(**filter_kwargs)

    def raw_list_query(
        self,
        account_id: int,
        user_id: int,
        is_account_owner: bool,
        ordering: Optional[TemplateOrdering] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
    ):
        from src.processes.models.templates.owner import (
            TemplateOwner,
        )

        query = TemplateListQuery(
            user_id=user_id,
            is_account_owner=is_account_owner,
            account_id=account_id,
            ordering=ordering,
            search_text=search,
            is_active=is_active,
            is_public=is_public,
        )
        return (
            self.execute_raw(query)
            .prefetch_related(
                Prefetch(
                    'owners',
                    queryset=TemplateOwner.objects.order_by('type', 'id'),
                ),
                'kickoff',
                'kickoff__fields',
                'kickoff__fields__selections',
            )
        )

    def raw_export_query(
        self,
        account_id: int,
        user_id: int,
        ordering: Optional[TemplateOrdering] = None,
        is_active: Optional[bool] = None,
        is_public: Optional[bool] = None,
        owners_ids: Optional[List[int]] = None,
        owners_group_ids: Optional[List[int]] = None,
        **kwargs,
    ):
        from src.processes.models.templates.owner import TemplateOwner
        if owners_ids:
            group_ids = (
                UserGroup.objects
                .on_account(account_id=account_id)
                .filter(users__in=owners_ids)
                .values_list('id', flat=True)
            )
            if owners_group_ids:
                owners_group_ids = list(
                    set(group_ids) | set(owners_group_ids),
                )
            else:
                owners_group_ids = list(group_ids)
        query = TemplateExportQuery(
            user_id=user_id,
            account_id=account_id,
            ordering=ordering,
            is_active=is_active,
            is_public=is_public,
            owners_ids=owners_ids,
            owners_group_ids=owners_group_ids,
        )
        return (
            self.execute_raw(query).
            prefetch_related(
                Prefetch(
                    'owners',
                    queryset=TemplateOwner.objects.order_by('type', 'id'),
                ),
                'tasks',
                'tasks__fields',
                'tasks__fields__selections',
                'tasks__checklists',
                'tasks__checklists__selections',
                'tasks__conditions',
                'tasks__conditions__rules',
                'tasks__conditions__rules__predicates',
                'tasks__raw_performers',
                'kickoff',
                'kickoff__fields',
                'kickoff__fields__selections',
            )
        )


class WorkflowQuerySet(WorkflowsBaseQuerySet):
    def running(self):
        return self.filter(
            status__in=[WorkflowStatus.RUNNING, WorkflowStatus.DELAYED],
        )

    def completed(self):
        return self.filter(status=WorkflowStatus.DONE)

    def exclude_legacy(self):
        return self.filter(template__isnull=False)

    def with_template_owner(self, user_id: int):
        return self.exclude_legacy().filter(
            template__template_owners=user_id,
        ).distinct()

    def with_member(self, user_id: int):
        return self.filter(members=user_id)

    def exclude_onboarding(self):
        return self.filter(
            ~Q(template__type__in=TemplateType.TYPES_ONBOARDING),
        )

    def fields_query(
        self,
        account_id: int,
        template_id: Optional[int] = None,
        status: Optional[WorkflowStatus] = None,
        fields: Optional[List[str]] = None,
        **kwargs,
    ):
        qst = self.on_account(account_id)
        if template_id is not None:
            qst = qst.filter(template_id=template_id)
        if status is not None:
            qst = qst.filter(status=status)
        qst = qst.order_by('-date_created')
        if fields:
            from src.processes.models.workflows.fields import TaskField
            qst = qst.prefetch_related(
                Prefetch(
                    lookup='fields',
                    queryset=(
                        TaskField.objects
                        .filter(api_name__in=fields)
                        .prefetch_related(
                            'selections',
                            'attachments',
                        )
                    ),
                ),
            )
        else:
            qst = qst.prefetch_related(
                'fields',
                'fields__selections',
                'fields__attachments',
            )
        return qst

    def raw_list_query(
        self,
        account_id: int,
        user_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[str] = None,
        ordering: Optional[str] = None,
        template_id: Optional[int] = None,
        template_task_api_name: Optional[str] = None,
        current_performer: Optional[List[int]] = None,
        current_performer_group_ids: Optional[List[int]] = None,
        workflow_starter: Optional[int] = None,
        is_external: Optional[bool] = None,
        search: Optional[str] = None,
        fields: Optional[List[str]] = None,
        ancestor_task_id: Optional[int] = None,
        using: str = 'default',
    ):
        if current_performer:
            performer_group_ids = UserGroup.objects.filter(
                users__in=current_performer,
            ).values_list('id', flat=True)
            if current_performer_group_ids:
                current_performer_group_ids = list(
                    set(performer_group_ids) |
                    set(current_performer_group_ids),
                )
            else:
                current_performer_group_ids = list(performer_group_ids)
        query = WorkflowListQuery(
            limit=limit,
            offset=offset,
            status=status,
            ordering=ordering,
            template=template_id,
            task_api_name=template_task_api_name,
            current_performer=current_performer,
            current_performer_group_ids=current_performer_group_ids,
            workflow_starter=workflow_starter,
            is_external=is_external,
            search=search,
            account_id=account_id,
            user_id=user_id,
            ancestor_task_id=ancestor_task_id,
        )
        from src.processes.models.templates.template import (
            Template,
        )
        from src.processes.models.workflows.task import (
            Delay,
            Task,
            TaskPerformer,
        )
        prefetch_args = [
            Prefetch(
                lookup='owners',
                to_attr='owners_ids',
                queryset=UserModel.objects.order_by('id').only('id'),
            ),
            Prefetch(
                lookup='template',
                queryset=Template.objects.only(
                    'id',
                    'name',
                    'is_active',
                ),
            ),
            Prefetch(
                lookup='tasks',
                to_attr='active_tasks',
                queryset=(
                    Task.objects.prefetch_related(
                        Prefetch(
                            lookup='performers',
                            to_attr='all_performers',
                            queryset=(
                                TaskPerformer.objects
                                .exclude_directly_deleted()
                            ),
                        ),
                        Prefetch(
                            lookup='delay_set',
                            to_attr='current_delay',
                            queryset=Delay.objects.filter(
                                end_date__isnull=True,
                            ).order_by('-id'),
                        ),
                    ).exclude(
                        status=TaskStatus.SKIPPED,
                    )
                ),
            ),
        ]
        if fields:
            from src.processes.models.workflows.fields import TaskField
            prefetch_args.append(
                Prefetch(
                    lookup='fields',
                    to_attr='filtered_fields',
                    queryset=(
                        TaskField.objects
                        .filter(api_name__in=fields)
                        .order_by('kickoff_id', 'task__number', '-order')
                    ),
                ),
            )

        raw_qst = (
            self.raw(
                raw_query=query.get_sql(),
                params=query.params,
                using=using,
            ).prefetch_related(*prefetch_args)
        )
        raw_qst.count = self.raw(
            raw_query=query.get_count_sql(),
            params=query.params,
            using=using,
        )[0].count
        return raw_qst


class TasksQuerySet(TasksBaseQuerySet):

    def by_number(self, number):
        return self.filter(number=number)

    def completed(self):
        return self.filter(status=TaskStatus.COMPLETED)

    def on_account(self, account_id: int):
        return self.filter(
            workflow__account_id=account_id,
        )

    def pending(self):
        return self.filter(status=TaskStatus.PENDING)

    def exclude_pending(self):
        return self.exclude(status=TaskStatus.PENDING)

    def active(self):
        return self.filter(status=TaskStatus.ACTIVE)

    def delayed(self):
        return self.filter(status=TaskStatus.DELAYED)

    def active_or_delayed(self):
        return self.filter(status__in=(TaskStatus.ACTIVE, TaskStatus.DELAYED))

    def with_date_first_started(self):
        return self.filter(date_first_started__isnull=False)

    def active_for_user(self, user_id):
        return self.filter(
            Q(
                Q(
                    require_completion_by_all=False,
                ) | Q(
                    require_completion_by_all=True,
                    taskperformer__is_completed=False,
                ),
            ) & Q(
                (
                    Q(taskperformer__group__users__id=user_id) |
                    Q(taskperformer__user_id=user_id)
                ) &
                Q(
                    status=TaskStatus.ACTIVE,
                    workflow__status=WorkflowStatus.RUNNING,
                ),
            ) & ~Q(
                taskperformer__directly_status=DirectlyStatus.DELETED,
            ),
        )

    def active_for_group(self, group_id):
        return self.filter(
            Q(
                Q(
                    require_completion_by_all=False,
                ) | Q(
                    require_completion_by_all=True,
                    taskperformer__is_completed=False,
                ),
            ) & Q(
                (
                    Q(taskperformer__group_id=group_id) |
                    Q(taskperformer__type=PerformerType.GROUP)
                ) &
                Q(
                    workflow__current_task=F('number'),
                    status=TaskStatus.ACTIVE,
                    workflow__status=WorkflowStatus.RUNNING,
                ),
            ) & ~Q(
                taskperformer__directly_status=DirectlyStatus.DELETED,
            ),
        )

    def new_completed_on_top(self):
        return self.order_by('-date_completed')

    def on_performer(self, user_id: int):
        return self.filter(
            taskperformer__user_id=user_id,
        )

    def exclude_directly_deleted(self):
        return self.exclude(
            taskperformer__directly_status=DirectlyStatus.DELETED,
        )

    def apd_status(self):
        return self.filter(
            status__in=(
                TaskStatus.ACTIVE,
                TaskStatus.PENDING,
                TaskStatus.DELAYED,
            ),
        )


class BaseFieldQuerySet(BaseQuerySet):

    def required(self):
        return self.filter(is_required=True)

    def exclude_api_names(self, api_names: List[str]):
        return self.filter(~Q(api_name__in=api_names))

    def api_names(self):
        return self.values_list('api_name', flat=True)


class FieldTemplateQuerySet(BaseFieldQuerySet):

    def by_template(self, template_id):
        return self.filter(template_id=template_id)


class KickoffQuerySet(AccountBaseQuerySet):
    pass


class FieldTemplateValuesQuerySet(BaseQuerySet):

    def by_ids(self, ids: List[int]):
        return self.filter(id__in=ids)

    def by_api_names(self, api_names: List[str]):
        return self.filter(api_name__in=api_names)

    def selected(self):
        return self.filter(is_selected=True)


class FieldSelectionQuerySet(BaseQuerySet):

    def by_ids(self, ids: List[int]):
        return self.filter(id__in=ids)

    def by_api_names(self, api_names: List[str]):
        return self.filter(api_name__in=api_names)

    def exclude_by_ids(self, ids: List[int]):
        return self.exclude(id__in=ids)

    def exclude_values(self, values: List[str]):
        return self.filter(~Q(value__in=values))

    def selected(self):
        return self.filter(is_selected=True)


class SystemTemplateQuerySet(BaseQuerySet):

    def active(self):
        return self.filter(is_active=True)

    def library(self):
        return self.filter(type=SysTemplateType.LIBRARY)

    def activated(self):
        return self.filter(type=SysTemplateType.ACTIVATED)

    def onboarding(self):
        return self.filter(type__in=SysTemplateType.TYPES_ONBOARDING)

    def onboarding_owner(self):
        return self.filter(type=SysTemplateType.ONBOARDING_ACCOUNT_OWNER)

    def onboarding_admin(self):
        return self.filter(type=SysTemplateType.ONBOARDING_ADMIN)

    def onboarding_not_admin(self):
        return self.filter(type=SysTemplateType.ONBOARDING_NON_ADMIN)

    def exclude_library(self):
        return self.exclude(type=SysTemplateType.LIBRARY)


class TaskFieldQuerySet(BaseFieldQuerySet):

    def with_attachments(self):
        return self.filter(attachments__isnull=False)

    def only_values(self):
        return self.values_list('value', flat=True)


class FileAttachmentQuerySet(AccountBaseQuerySet):

    def by_ids(self, ids: List[int]):
        return self.filter(id__in=ids)

    def not_attached(self):
        return self.filter(event__isnull=True, output__isnull=True)

    def with_output_or_not_attached(self, output_id):
        return self.filter(
            Q(output_id=output_id) |
            Q(event__isnull=True, output__isnull=True),
        )

    def with_event_or_not_attached(self, event_id):
        return self.filter(
            Q(event_id=event_id) |
            Q(event__isnull=True, output__isnull=True),
        )

    def not_on_event(self):
        return self.filter(event__isnull=True)

    def by_output_api_name(self, api_name: str):
        return self.filter(output__api_name=api_name)

    def on_workflow(self, workflow_id: int):
        return self.filter(workflow_id=workflow_id)

    def ids_set(self):
        qst = self.values_list('id', flat=True)
        return set(qst)


class TemplateDraftQuerySet(BaseQuerySet):
    def on_account(self, account_id: int):
        return self.filter(template__account_id=account_id)

    def by_user(self, account_id: int, user_id: int):
        return self.raw(
            """
            SELECT
              id,
              draft
            FROM
              (
                SELECT
                  ptd.id,
                  draft,
                  jsonb_array_elements(draft->'tasks') as task,
                  jsonb_array_elements(draft->'owners') AS owners
                FROM processes_templatedraft ptd
                  JOIN processes_template pt
                    ON pt.id = ptd.template_id
                      AND pt.account_id = %(account_id)s
                WHERE ptd.is_deleted IS FALSE
                AND draft IS NOT NULL
                AND draft ? 'tasks'
                AND jsonb_typeof(draft->'tasks')='array'
                AND draft ? 'owners'
                AND jsonb_typeof(draft->'owners')='array'
              ) tasks
            WHERE
              (
                jsonb_typeof(task->'raw_performers')='array'
                AND task->'raw_performers' @>
                '[{"source_id": "%(user_id)s", "type":"user"}]'
              ) OR (
                owners @> '{"source_id": "%(user_id)s","type":"user"}'
            )
            """,
            params={'user_id': user_id, 'account_id': account_id},
        )


class TaskPerformerQuerySet(BaseHardQuerySet):

    def with_tasks_after(self, task):
        return self.filter(task__number__gte=task.number)

    def by_task(self, task_id):
        return self.filter(task_id=task_id)

    def by_tasks(self, task_ids: List[int]):
        return self.filter(task_id__in=task_ids)

    def by_workflow(self, workflow_id):
        return self.filter(task__workflow_id=workflow_id)

    def by_user(self, user_id):
        return self.filter(user_id=user_id)

    def by_user_or_group(self, user_id):
        return self.filter(Q(user_id=user_id) | Q(group__users__id=user_id))

    def completed(self):
        return self.filter(is_completed=True)

    def not_completed(self):
        return self.filter(is_completed=False)

    def exclude_users(self, users: List[int]):
        return self.filter(~Q(user__in=users))

    def exclude_directly_changed(self):
        return self.filter(directly_status=DirectlyStatus.NO_STATUS)

    def exclude_directly_deleted(self):
        return self.exclude(directly_status=DirectlyStatus.DELETED)

    def user_is_subscriber(self):
        return self.filter(
            Q(user__is_complete_tasks_subscriber=True) |
            Q(group__users__is_complete_tasks_subscriber=True),
        ).distinct()

    def get_user_ids_set(self):
        direct_user_ids = self.filter(
            user__type=UserType.USER,
        ).values_list('user_id', flat=True)
        group_user_ids = (
            self.filter(group__users__type=UserType.USER)
            .values_list('group__users__id', flat=True)
        )
        return set(direct_user_ids).union(set(group_user_ids))

    def get_user_emails_and_ids_set(self):
        direct_users = self.filter(
            user__type=UserType.USER,
        ).values_list('user_id', 'user__email')
        group_users = (
            self.filter(group__users__type=UserType.USER)
            .values_list('group__users__id', 'group__users__email')
        )
        return set(direct_users).union(set(group_users))

    def get_user_ids_emails_subscriber_set(self):
        direct_users = self.filter(user__isnull=False).values_list(
            'user_id',
            'user__email',
            'user__is_new_tasks_subscriber',
        )
        group_users = self.filter(group__isnull=False).values_list(
            'group__users__id',
            'group__users__email',
            'group__users__is_new_tasks_subscriber',
        )
        return set(direct_users).union(set(group_users))

    def group_ids(self):
        qst = self.filter(type='group').values_list('group_id', flat=True)
        return tuple(elem for elem in qst)

    def user_ids(self):
        qst = self.filter(type='user').values_list('user_id', flat=True)
        return tuple(elem for elem in qst)

    def user_ids_set(self) -> set:
        qst = self.values_list('user_id', flat=True)
        return set(qst)

    def guests(self):
        return self.filter(user__type=UserType.GUEST)

    def users(self):
        direct_users = self.filter(
            user__isnull=False,
            user__type=UserType.USER,
        )
        group_users = (
            self.filter(group__isnull=False)
            .filter(
                group__users__isnull=False,
                group__users__type=UserType.USER,
            )
        )
        return (direct_users | group_users).distinct()

    def new_task_recipients(self):

        """ Returns task performers of users who are
            subscribed to notifications about new tasks """

        direct_users = self.filter(type=PerformerType.USER).only(
            'user_id',
            'user__email',
            'user__is_new_tasks_subscriber',
        ).annotate(
            email=F('user__email'),
            is_subscribed=F('user__is_new_tasks_subscriber'),
        )
        group_users = self.filter(group__isnull=False).only(
            'group__users__id',
            'group__users__email',
            'group__users__is_new_tasks_subscriber',
        ).annotate(
            email=F('group__users__email'),
            is_subscribed=F('group__users__is_new_tasks_subscriber'),
        )
        return direct_users.union(group_users)


class ChecklistTemplateQuerySet(BaseQuerySet):
    pass


class ChecklistTemplateSelectionQuerySet(BaseQuerySet):
    pass


class ChecklistQuerySet(BaseQuerySet):

    def with_workflow_member(self, user_id: int):
        return self.filter(task__workflow__members=user_id)


class ChecklistSelectionQuerySet(BaseQuerySet):

    def marked(self):
        return self.exclude(date_selected__isnull=True)


class SystemWorkflowKickoffDataQuerySet(BaseQuerySet):

    def active(self):
        return self.filter(is_active=True)

    def onboarding_owner(self):
        return self.filter(user_role=SysTemplateType.ONBOARDING_ACCOUNT_OWNER)

    def onboarding_admin(self):
        return self.filter(user_role=SysTemplateType.ONBOARDING_ADMIN)

    def onboarding_not_admin(self):
        return self.filter(user_role=SysTemplateType.ONBOARDING_NON_ADMIN)

    def only_data(self):
        return self.values_list('kickoff_data', flat=True)


class SystemTemplateCategoryQuerySet(BaseQuerySet):

    def active(self):
        return self.filter(is_active=True)

    def max_order(self) -> int:
        value = self.aggregate(Max('order'))['order__max']
        return 0 if value is None else value


class WorkflowEventQuerySet(AccountBaseQuerySet):

    def type_in(self, types: List[int]):
        return self.filter(type__in=types)

    def exclude_type(self, event_type: int):
        return self.exclude(type=event_type)

    def exclude_comments(self):
        return self.exclude(type=WorkflowEventType.COMMENT)

    def type_comment(self):
        return self.filter(type=WorkflowEventType.COMMENT)

    def task_complete(self):
        return self.filter(type=WorkflowEventType.TASK_COMPLETE)

    def task_start(self):
        return self.filter(type=WorkflowEventType.TASK_START)

    def task_revert(self):
        return self.filter(type=WorkflowEventType.TASK_REVERT)

    def on_workflow(self, workflow_id: int):
        return self.filter(workflow_id=workflow_id)

    def on_task(self, task_id: int):
        return self.filter(task_id=task_id)

    def highlights(
        self,
        account_id: int,
        user_id: int,
        templates: str = None,
        current_performer_ids: Optional[List[int]] = None,
        current_performer_group_ids: Optional[List[int]] = None,
        date_before_tsp: Optional[datetime] = None,
        date_after_tsp: Optional[datetime] = None,
    ):
        # TODO refactoring need

        from src.processes.queries import HighlightsQuery
        query = HighlightsQuery(
            account_id=account_id,
            user_id=user_id,
            templates=templates,
            current_performer_ids=current_performer_ids,
            current_performer_group_ids=current_performer_group_ids,
            date_before_tsp=date_before_tsp,
            date_after_tsp=date_after_tsp,
        )
        return self.execute_raw(query)

    def only_with_attachments(self):
        return self.filter(with_attachments=True)

    def last_created(self):
        return self.order_by('-created').first()

    def by_task(self, task_id: int):
        return self.filter(task_id=task_id)

    def by_user(self, user_id: int):
        return self.filter(user_id=user_id)

    def update_watched_from(self, actions_ids: List[int]):
        from src.processes.queries import (
            UpdateWorkflowEventWatchedQuery,
        )
        query = UpdateWorkflowEventWatchedQuery(actions_ids)
        return self.execute_raw(query)


class WorkflowEventActionQuerySet(AccountBaseQuerySet):

    def watched(self):
        return self.filter(type=WorkflowEventActionType.WATCHED)

    def only_ids(self):
        return self.values_list('id', flat=True)


class ConditionQuerySet(BaseQuerySet):

    def start_task(self):
        return self.filter(action=ConditionAction.START_TASK)

    def skip_task(self):
        return self.filter(action__in=(
                ConditionAction.SKIP_TASK,
                ConditionAction.END_WORKFLOW,
            ),
        )
