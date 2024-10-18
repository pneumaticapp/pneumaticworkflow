from typing import List, Optional, Union, Iterable
from django.conf import settings
from django.db import transaction
from django.db.models import (
    Count,
    Q,
    F,
    Avg,
    Max,
)
from pneumatic_backend.processes.queries import (
    WorkflowListQuery,
    RunningTaskTemplateQuery,
)
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.generics.querysets import (
    AccountBaseQuerySet,
    BaseQuerySet,
    BaseHardQuerySet,
)
from pneumatic_backend.processes.enums import (
    WorkflowStatus,
    TemplateType,
    WorkflowEventType,
    DirectlyStatus,
    SysTemplateType,
    WorkflowEventActionType,
)


class WorkflowsBaseQuerySet(AccountBaseQuerySet):

    pass


class DelayBaseQuerySet(BaseQuerySet):

    def current_task_delay_qst(self, task):
        return self.filter(
            task_id=task.id,
            end_date__isnull=True
        ).order_by('-id')

    def current_task_delay(self, task):
        return self.current_task_delay_qst(task).first()

    def active(self):
        return self.filter(end_date__isnull=True)


class TasksBaseQuerySet(BaseQuerySet):

    def on_raw_performer(self, user_id: int):
        return self.filter(raw_performers__user_id=user_id)

    def raw_performers_count(self, count: int):

        """ Returns tasks where count raw_performers == count """

        return self.annotate(
            raw_performers_count=Count('raw_performers')
        ).filter(raw_performers_count=count)


class TaskTemplateQuerySet(TasksBaseQuerySet):
    def active_templates(self):
        return self.filter(template__is_active=True)

    def on_account(self, account_id: int):
        return self.filter(template__account_id=account_id)

    def with_tasks_in_progress(
        self,
        template_id: int,
        user_id: int,
        with_tasks_in_progress: bool
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

    def with_template_owners(self, user_id: int):
        return self.filter(template_owners=user_id).distinct()

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
            ~Q(type__in=TemplateType.TYPES_ONBOARDING)
        )

    def paid(self):
        return self.filter(
            Q(
                tasks__conditions__is_deleted=False
            ) | Q(
                is_public=True
            )
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


class WorkflowQuerySet(WorkflowsBaseQuerySet):
    def running(self):
        return self.filter(
            status__in=[WorkflowStatus.RUNNING, WorkflowStatus.DELAYED],
        )

    def completed(self):
        return self.filter(status=WorkflowStatus.DONE)

    def exclude_legacy(self):
        return self.filter(template__isnull=False)

    def with_template_owners(self, user_id: int):
        return self.exclude_legacy().filter(
            template__template_owners=user_id
        ).distinct()

    def with_member(self, user_id: int):
        return self.filter(members=user_id)

    def exclude_onboarding(self):
        return self.filter(
            ~Q(template__type__in=TemplateType.TYPES_ONBOARDING)
        )

    def raw_list_query(
        self,
        account_id: int,
        user_id: int,
        status: Optional[str] = None,
        ordering: Optional[str] = None,
        template_id: Optional[int] = None,
        template_task_id: Optional[int] = None,
        current_performer: Optional[int] = None,
        workflow_starter: Optional[int] = None,
        is_external: Optional[bool] = None,
        search: Optional[str] = None,
    ):
        query = WorkflowListQuery(
            status=status,
            ordering=ordering,
            template=template_id,
            template_task=template_task_id,
            current_performer=current_performer,
            workflow_starter=workflow_starter,
            is_external=is_external,
            search=search,
            account_id=account_id,
            user_id=user_id
        )
        return self.execute_raw(query, using=settings.REPLICA)


class TasksQuerySet(TasksBaseQuerySet):

    def by_number(self, number):
        return self.filter(number=number)

    def incompleted(self):
        return self.filter(is_completed=False)

    def completed(self):
        return self.filter(is_completed=True)

    def running_now(self):
        return self.filter(
            workflow__current_task=F('number'),
            workflow__status=WorkflowStatus.RUNNING
        )

    def on_account(self, account_id: int):
        return self.filter(
            workflow__account_id=account_id
        )

    def active(self):
        return self.filter(workflow__current_task=F('number'))

    def started(self):
        return self.filter(date_started__isnull=False)

    def with_date_first_started(self):
        return self.filter(date_first_started__isnull=False)

    def active_for_user(self, user_id):
        return self.filter(
            Q(
                Q(
                    require_completion_by_all=False,
                ) | Q(
                    require_completion_by_all=True,
                    taskperformer__is_completed=False
                )
            ) & Q(
                taskperformer__user_id=user_id,
                workflow__current_task=F('number'),
                workflow__status=WorkflowStatus.RUNNING
            ) & ~Q(
                taskperformer__directly_status=DirectlyStatus.DELETED
            )
        )

    def new_completed_on_top(self):
        return self.order_by('-date_completed')

    def on_performer(self, user_id: int):
        return self.filter(
            taskperformer__user_id=user_id
        )

    def exclude_directly_deleted(self):
        return self.exclude(
            taskperformer__directly_status=DirectlyStatus.DELETED
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

    def by_api_names(self, api_names: List[int]):
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
            Q(event__isnull=True, output__isnull=True)
        )

    def with_event_or_not_attached(self, event_id):
        return self.filter(
            Q(event_id=event_id) |
            Q(event__isnull=True, output__isnull=True)
        )

    def not_on_event(self):
        return self.filter(event__isnull=True)

    def by_output_api_name(self, api_name: str):
        return self.filter(output__api_name=api_name)

    def on_workflow(self, workflow_id: int):
        return self.filter(workflow_id=workflow_id)

    def only_urls(self):
        return self.values_list('url', flat=True)

    def ids_set(self):
        qst = self.values_list('id', flat=True)
        return set(elem for elem in qst)


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
                  jsonb_array_elements(
                    draft->'template_owners'
                  ) AS template_owners
                FROM processes_templatedraft ptd JOIN processes_template pt
                  ON pt.id = ptd.template_id
                    AND pt.account_id = %(account_id)s
                WHERE ptd.is_deleted IS FALSE
              ) tasks
            WHERE
              task->'raw_performers' @>
                '[{"source_id":%(user_id)s,"type":"user"}]'
                OR template_owners::text = '%(user_id)s'
            """,
            params={'user_id': user_id, 'account_id': account_id}
        )


class TaskPerformerQuerySet(BaseHardQuerySet):

    def with_tasks_after(self, task):
        return self.filter(task__number__gte=task.number)

    def by_task(self, task_id):
        return self.filter(task_id=task_id)

    def by_workflow(self, workflow_id):
        return self.filter(task__workflow_id=workflow_id)

    def by_user(self, user_id):
        return self.filter(user_id=user_id)

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

    def user_ids(self):
        qst = self.values_list('user_id', flat=True)
        return tuple(elem for elem in qst)

    def user_ids_set(self) -> set:
        qst = self.values_list('user_id', flat=True)
        return set(elem for elem in qst)

    def guests(self):
        return self.filter(user__type=UserType.GUEST)

    def users(self):
        return self.filter(user__type=UserType.USER)


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

    def task_complete(self):
        return self.filter(type=WorkflowEventType.TASK_COMPLETE)

    def task_start(self):
        return self.filter(type=WorkflowEventType.TASK_START)

    def task_revert(self):
        return self.filter(type=WorkflowEventType.TASK_REVERT)

    def on_workflow(self, workflow_id: int):
        return self.filter(workflow_id=workflow_id)

    def highlights(
        self,
        account_id: int,
        user_id: int,
        templates: str = None,
        users: str = None,
        date_before: str = None,
        date_after: str = None,
    ):
        # TODO refactoring need

        from pneumatic_backend.processes.queries import HighlightsQuery
        query = HighlightsQuery(
            account_id=account_id,
            user_id=user_id,
            templates=templates,
            users=users,
            date_before=date_before,
            date_after=date_after
        )
        return self.execute_raw(query, using=settings.REPLICA)

    def only_with_attachments(self):
        return self.filter(with_attachments=True)

    def last_created(self):
        return self.order_by('-created').first()

    def by_task(self, task_id: int):
        return self.filter(task_json__id=task_id)

    def by_user(self, user_id: int):
        return self.filter(user_id=user_id)

    def type_comment(self):
        return self.filter(type=WorkflowEventType.COMMENT)

    def update_watched_from(self, actions_ids: List[int]):
        from pneumatic_backend.processes.queries import (
            UpdateWorkflowEventWatchedQuery
        )
        query = UpdateWorkflowEventWatchedQuery(actions_ids)
        return self.execute_raw(query)


class WorkflowEventActionQuerySet(AccountBaseQuerySet):

    def watched(self):
        return self.filter(type=WorkflowEventActionType.WATCHED)

    def only_ids(self):
        return self.values_list('id', flat=True)
