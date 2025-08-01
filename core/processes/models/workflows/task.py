from datetime import datetime
from django.utils import timezone
from typing import List, Optional, Union, Set, Tuple
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from pneumatic_backend.accounts.models import (
    AccountBaseMixin,
    Notification,
    UserGroup
)
from pneumatic_backend.generics.managers import BaseSoftDeleteManager
from pneumatic_backend.generics.models import SoftDeleteModel
from pneumatic_backend.processes.models import Workflow
from pneumatic_backend.processes.models.mixins import (
    TaskMixin,
    TaskRawPerformersMixin,
    ApiNameMixin,
)
from pneumatic_backend.processes.querysets import (
    TasksQuerySet,
    DelayBaseQuerySet,
    TaskPerformerQuerySet
)
from pneumatic_backend.processes.enums import (
    PerformerType,
    DirectlyStatus,
    FieldType,
    TaskStatus,
)

UserModel = get_user_model()


class Task(
    SoftDeleteModel,
    AccountBaseMixin,
    TaskMixin,
    TaskRawPerformersMixin,
    ApiNameMixin
):

    class Meta:
        ordering = ['number']

    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    performers = models.ManyToManyField(
        UserModel,
        through='TaskPerformer'
    )
    name = models.TextField()
    name_template = models.TextField()
    status = models.CharField(
        choices=TaskStatus.CHOICES,
        max_length=50,
        default=TaskStatus.PENDING
    )
    description_template = models.TextField(null=True, blank=True)
    is_completed_deprecated = models.BooleanField(default=False)
    is_skipped_deprecated = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    date_first_started = models.DateTimeField(
        null=True,
        help_text='set when the task becomes active for the first time'
    )
    date_started = models.DateTimeField(
        null=True,
        help_text='set every time the task becomes active'
    )
    date_completed = models.DateTimeField(null=True)
    due_date = models.DateTimeField(null=True)
    due_date_directly_status = models.IntegerField(
        default=DirectlyStatus.NO_STATUS,
        choices=DirectlyStatus.CHOICES
    )
    checklists_total = models.IntegerField(default=0)
    checklists_marked = models.IntegerField(default=0)
    contains_comments = models.BooleanField(default=False)
    clear_description = models.TextField(
        null=True,
        blank=True,
        help_text='Does not contains markdown'
    )

    search_content = SearchVectorField(null=True)

    objects = BaseSoftDeleteManager.from_queryset(TasksQuerySet)()

    @property
    def next(self):
        try:
            return Task.objects.get(
                number=self.number + 1,
                workflow=self.workflow,
            )
        except Task.DoesNotExist:
            return None

    @property
    def prev(self):
        if self.revert_task:
            return Task.objects.get(
                api_name=self.revert_task,
                workflow_id=self.workflow_id
            )
        try:
            return Task.objects.get(
                number=self.number - 1,
                workflow_id=self.workflow_id
            )
        except Task.DoesNotExist:
            return None

    def set_date_first_started(self, value: datetime):
        if self.date_first_started is None:
            self.date_first_started = value

    def reset_delay(self, delay=None):
        if delay is None:
            delay = Delay.objects.filter(
                task=self,
            ).order_by('-id').first()
        if delay and delay.pk:
            delay.start_date = None
            delay.end_date = None
            delay.save()
        return delay

    def webhook_payload(self):
        from pneumatic_backend.processes.api_v2.serializers.workflow.task \
            import TaskSerializer
        task_data = TaskSerializer(instance=self).data
        task_data.update(**self.workflow.webhook_payload())
        return {'task': task_data}

    def get_active_delay(self):
        return self.delay_set.active().first()

    def get_last_delay(self):
        return self.delay_set.order_by('-start_date').first()

    def _get_raw_performer(
        self,
        api_name: str,
        performer_type: PerformerType = PerformerType.USER,
        user: Optional[UserModel] = None,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        field=None,  # Optional[TaskField]
    ):  # -> RawPerformer

        """ Returns new a raw performer object with given data """

        from pneumatic_backend.processes.models.workflows\
            .raw_performer import RawPerformer

        result = RawPerformer(
            account=self.account,
            task=self,
            workflow=self.workflow,
            field=field,
            api_name=api_name,
            type=performer_type,
        )
        if user:
            result.user = user
        elif user_id:
            result.user_id = user_id
        elif group_id:
            result.group_id = group_id
        return result

    def add_raw_performer(
        self,
        user: Optional[UserModel] = None,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
        field=None,
        api_name: Optional[str] = None,
        performer_type: PerformerType = PerformerType.USER,
    ):  # -> RawPerformer

        """ Creates and returns a raw performer for a task with given data
            Optionally updates the performers after create raw performers """

        if performer_type != PerformerType.WORKFLOW_STARTER:
            if not group_id and not user and not user_id and not field:
                raise Exception(
                    'Raw performer should be linked with field or user'
                )

        raw_performer = self._get_raw_performer(
            api_name=api_name,
            performer_type=performer_type,
            user=user,
            group_id=group_id,
            user_id=user_id,
            field=field,
        )
        raw_performer.save()
        return raw_performer

    def exclude_directly_deleted_taskperformer_set(self):
        return self.taskperformer_set.exclude_directly_deleted()

    def get_default_performer(self) -> UserModel:

        """ Returns user, that may be used as default task performer:
            workflow starter or account owner """

        user = self.workflow.workflow_starter
        if not user:
            user = self.workflow.account.users.filter(
                is_account_owner=True
            ).first()
            if not user:
                raise Exception(
                    'Invalid workflow: '
                    'Workflow starter or account owner must be set!'
                )
        return user

    def _get_raw_performers_api_names(self) -> set:
        return set(
            self.raw_performers.values_list('api_name', flat=True)
        )

    def _get_raw_performers_fields_dict(
        self,
        raw_performers_templates: List[dict],
        existent_raw_performer_api_names: Set[int]
    ) -> dict:

        """ For presented RawPerformerTemplates with type Field
            returns TaskFields dict

            Return format: {field.api_name: field, ...}"""

        api_names = set()
        fields_dict = {}
        for raw_performer_template in raw_performers_templates:
            if raw_performer_template['api_name'] not in (
                existent_raw_performer_api_names
            ):
                if raw_performer_template['type'] == PerformerType.FIELD:
                    api_names.add(raw_performer_template['field']['api_name'])
        if api_names:
            fields_dict = self.workflow.get_fields_as_dict(
                tasks_filter_kwargs={'number__lt': self.number},
                fields_filter_kwargs={
                    'type': FieldType.USER,
                    'api_name__in': api_names
                },
                dict_key='api_name'
            )
        return fields_dict

    def update_raw_performers_from_task_template(
        self,
        task_template: Union['TaskTemplate', dict, None] = None,
    ):

        """
            Updates all raw_performers from task_template.raw_performers:
            - create new raw performer (no duplicate)
            - delete orphaned raw performer

            if task_template is None,
            the task_template specified in task_template_id will be used """

        from pneumatic_backend.processes.models.templates\
            .task import TaskTemplate
        from pneumatic_backend.processes.models.workflows\
            .raw_performer import RawPerformer

        raw_performers_templates = ()
        if isinstance(task_template, TaskTemplate):
            raw_performers_templates = (
                task_template.raw_performers.select_related(
                    'field',
                    'group'
                ).all()
            )
            raw_performers_templates = [{
                'id': e.id,
                'type': e.type,
                'user_id': e.user_id,
                'group_id': e.group_id,
                'api_name': e.api_name,
                'field': {
                    'api_name': e.field.api_name
                } if e.type == PerformerType.FIELD else None
            } for e in raw_performers_templates]
        elif isinstance(task_template, dict):
            raw_performers_templates = task_template['raw_performers']
        elif self.api_name:
            task_template = TaskTemplate.objects.by_id(
                self.api_name
            ).first()
            if task_template:
                raw_performers_templates = (
                    task_template.raw_performers.values()
                )

        existent_raw_performer_api_names = (
            self._get_raw_performers_api_names()
        )
        fields_dict = self._get_raw_performers_fields_dict(
            raw_performers_templates,
            existent_raw_performer_api_names
        )

        new_raw_performers = []
        deleted_raw_performer_api_names = (
            existent_raw_performer_api_names.copy()
        )
        for raw_performer_template in raw_performers_templates:
            if raw_performer_template['api_name'] in (
                existent_raw_performer_api_names
            ):
                deleted_raw_performer_api_names.remove(
                    raw_performer_template['api_name']
                )
            else:
                if raw_performer_template['type'] == PerformerType.FIELD:
                    field = fields_dict.get(
                        raw_performer_template['field']['api_name']
                    )
                else:
                    field = None
                new_raw_performers.append(
                    self._get_raw_performer(
                        performer_type=raw_performer_template['type'],
                        user_id=raw_performer_template.get('user_id'),
                        group_id=raw_performer_template.get('group_id'),
                        field=field,
                        api_name=raw_performer_template['api_name'],
                    )
                )
        if new_raw_performers:
            RawPerformer.objects.bulk_create(new_raw_performers)
        if deleted_raw_performer_api_names:
            RawPerformer.objects.filter(
                api_name__in=deleted_raw_performer_api_names
            ).delete()

    def update_performers(
        self,
        raw_performer=None,
        restore_performers: bool = False,
    ) -> Tuple[List[int], List[int], List[int]]:

        # TODO move to TaskService

        """ Update all performers from raw performers:
            - create new performers (no duplicates)
            - delete orphan performers (if there are no raw performers
                left pointing to the performer)
            - delete notifications for deleted performers

            Parameters:
            - raw_performer - if specified, perform operation
                for special raw_performer
            - restore_performers - if true, restore deleted performers
                from user fields

            Returns two lists: created and deleted performers users ids
            """

        if raw_performer:
            raw_performers = (raw_performer,)
        else:
            raw_performers = self.raw_performers.select_related(
                'field',
                'group'
            ).all()

        api_names, user_ids, group_ids = (
            defaultdict(list),
            defaultdict(list),
            defaultdict(list)
        )
        for raw_performer in raw_performers:
            if raw_performer.type == PerformerType.USER:
                user_ids[raw_performer.user_id].append(raw_performer)
            elif raw_performer.type == PerformerType.GROUP:
                group_ids[raw_performer.group_id].append(raw_performer)
            elif raw_performer.type == PerformerType.FIELD:
                api_names[raw_performer.field.api_name].append(raw_performer)
            elif raw_performer.type == PerformerType.WORKFLOW_STARTER:
                user = self.get_default_performer()
                user_ids[user.id].append(raw_performer)

        if api_names:
            user_fields = self.workflow.get_fields(
                tasks_filter_kwargs={'number__lt': self.number},
                fields_filter_kwargs={
                    'type': FieldType.USER,
                    'api_name__in': api_names.keys()
                }
            )
            for field in user_fields:
                if field.user_id:
                    user_ids[field.user_id].extend(api_names[field.api_name])

        raw_performers_for_update = []
        created_performers_user_ids = []
        created_performers_group_ids = []
        if user_ids:
            for user_id, raw_performers_ in user_ids.items():
                task_performer, created = TaskPerformer.objects.get_or_create(
                    type=PerformerType.USER,
                    task_id=self.id,
                    user_id=user_id
                )
                if created:
                    created_performers_user_ids.append(user_id)
                if task_performer.directly_status == DirectlyStatus.NO_STATUS:
                    for raw_performer_ in raw_performers_:
                        raw_performer_.task_performer_id = task_performer.id
                        raw_performers_for_update.append(raw_performer_)
                elif (
                    task_performer.directly_status == DirectlyStatus.DELETED
                    and restore_performers
                ):
                    restore_performer = False
                    for raw_performer_ in raw_performers_:
                        if raw_performer_.type == PerformerType.FIELD:
                            raw_performer_.task_performer_id = (
                                task_performer.id
                            )
                            raw_performers_for_update.append(raw_performer_)
                            restore_performer = True
                    if restore_performer:
                        task_performer.directly_status = (
                            DirectlyStatus.NO_STATUS
                        )
                        task_performer.save(update_fields=('directly_status',))
        if group_ids:
            for group_id, raw_performers_ in group_ids.items():
                task_performer, created = TaskPerformer.objects.get_or_create(
                    type=PerformerType.GROUP,
                    task_id=self.id,
                    group_id=group_id
                )
                if created:
                    created_performers_group_ids.append(group_id)
                if task_performer.directly_status == DirectlyStatus.NO_STATUS:
                    for raw_performer_ in raw_performers_:
                        raw_performer_.task_performer_id = task_performer.id
                        raw_performers_for_update.append(raw_performer_)
                elif (
                    task_performer.directly_status == DirectlyStatus.DELETED
                    and restore_performers
                ):
                    restore_performer = False
                    for raw_performer_ in raw_performers_:
                        if raw_performer_.type == PerformerType.FIELD:
                            raw_performer_.task_performer_id = (
                                task_performer.id
                            )
                            raw_performers_for_update.append(raw_performer_)
                            restore_performer = True
                    if restore_performer:
                        task_performer.directly_status = (
                            DirectlyStatus.NO_STATUS
                        )
                        task_performer.save(update_fields=('directly_status',))
        if raw_performers_for_update:
            from pneumatic_backend.processes.models.workflows \
                .raw_performer import RawPerformer
            RawPerformer.objects.bulk_update(
                objs=raw_performers_for_update,
                fields=('task_performer_id',)
            )

        deleted_performers_user_ids = self._delete_orphaned_performers()
        users_in_groups = (
            UserModel.objects
            .get_users_in_groups(group_ids=group_ids)
            .user_ids_set()
        )
        union_user_ids = list(set(user_ids).union(users_in_groups))
        Notification.objects.exclude_users(
            union_user_ids
        ).by_task(self.id).delete()
        self.workflow.members.add(*created_performers_user_ids)
        return (
            created_performers_user_ids,
            created_performers_group_ids,
            deleted_performers_user_ids
        )

    def _delete_orphaned_performers(self) -> List[int]:

        """ delete orphan performers (if there are no raw performers
            left pointing to the performer) """

        task_performer_ids = list(self.raw_performers.values_list(
            'task_performer_id', flat=True
        ))
        performers_to_delete = TaskPerformer.objects.by_task(
            self.id
        ).exclude_ids(
            task_performer_ids
        ).exclude_directly_changed()
        if performers_to_delete.exists():
            users_ids = list(performers_to_delete.user_ids())
            performers_to_delete.delete()
            return users_ids
        return []

    def delete_raw_performer(
        self,
        user: Optional[UserModel] = None,
        group: Optional[UserGroup] = None,
        field=None,
        performer_type: PerformerType = PerformerType.USER
    ):

        """ Delete a raw_performer
            Check and delete orphan performers.
            Returns the number of raw performers deleted """

        deleted_count = super().delete_raw_performer(
            performer_type=performer_type,
            user=user,
            group=group,
            field=field
        )
        if deleted_count:
            self._delete_orphaned_performers()
        return deleted_count

    def delete_raw_performers(self):

        """ Delete all raw performers
            Check and delete orphan performers """

        super().delete_raw_performers()
        self._delete_orphaned_performers()

    def can_be_completed(self) -> bool:

        if self.is_completed is True:
            return False
        else:
            task_performers = self.taskperformer_set.exclude_directly_deleted()
            completed_performers = task_performers.completed().exists()
            incompleted_performers = task_performers.not_completed().exists()
            by_all = self.require_completion_by_all
            return (
                not by_all and completed_performers or
                by_all and not incompleted_performers
            )

    @property
    def checklists_completed(self):
        return self.checklists_marked == self.checklists_total

    @property
    def is_pending(self):
        return self.status == TaskStatus.PENDING

    @property
    def is_completed(self):
        return self.status == TaskStatus.COMPLETED

    @property
    def is_skipped(self):
        return self.status == TaskStatus.SKIPPED

    @property
    def is_active(self):
        return self.status == TaskStatus.ACTIVE

    @property
    def is_delayed(self):
        return self.status == TaskStatus.DELAYED

    def __str__(self):
        return f'(Task {self.id}) {self.name}'


class TaskForList(
    SoftDeleteModel,
    models.Model
):

    class Meta:
        managed = False

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=280)
    api_name = models.CharField(max_length=280)
    workflow_name = models.CharField(max_length=120)
    date_started = models.DateTimeField()
    date_started_tsp = models.FloatField()
    date_completed = models.DateTimeField(null=True)
    date_completed_tsp = models.FloatField(null=True)
    template_id = models.IntegerField(null=True)
    # TODO Remove in https://my.pneumatic.app/workflows/36988/
    template_task_id = models.IntegerField(null=True)
    template_task_api_name = models.CharField(max_length=100, null=True)
    is_urgent = models.BooleanField()
    due_date = models.DateTimeField(null=True)
    due_date_tsp = models.FloatField(null=True)
    status = models.CharField(max_length=50)

    objects = BaseSoftDeleteManager.from_queryset(TasksQuerySet)()


class Delay(
    SoftDeleteModel
):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
    )
    duration = models.DurationField()
    start_date = models.DateTimeField(
        null=True,
        blank=True,
    )
    estimated_end_date = models.DateTimeField(
        null=True,
        blank=True,
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=(
            'The date the delay really ended'
            '(for example will be ended forced by resuming the workflow)'
        ),
    )
    directly_status = models.IntegerField(
        default=DirectlyStatus.NO_STATUS,
        choices=DirectlyStatus.CHOICES
    )

    def save(self, update_fields=None, **kwargs):
        if self.start_date:
            self.estimated_end_date = self.start_date + self.duration

        if update_fields is not None:
            update_fields.append('estimated_end_date')

        super().save(update_fields=update_fields)

    @property
    def is_expired(self):
        if self.estimated_end_date:
            return self.estimated_end_date < timezone.now()
        else:
            return False

    objects = BaseSoftDeleteManager.from_queryset(DelayBaseQuerySet)()


class TaskPerformer(
    SoftDeleteModel
):

    class Meta:
        unique_together = ('user', 'task')
        ordering = ('user_id',)

    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        null=True,
    )
    group = models.ForeignKey(
        UserGroup,
        on_delete=models.CASCADE,
        null=True,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE
    )
    type = models.CharField(
        max_length=100,
        choices=PerformerType.choices,
        default=PerformerType.USER,
    )
    directly_status = models.IntegerField(
        default=DirectlyStatus.NO_STATUS,
        choices=DirectlyStatus.CHOICES
    )
    is_completed = models.BooleanField(default=False)
    date_completed = models.DateTimeField(null=True)

    objects = BaseSoftDeleteManager.from_queryset(TaskPerformerQuerySet)()
