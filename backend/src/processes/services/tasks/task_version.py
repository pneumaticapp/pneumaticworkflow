from typing import Dict, Optional, List
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_duration

from src.notifications.tasks import send_new_task_notification, \
    send_removed_task_notification
from src.processes.models import (
    Task,
    Condition,
    Predicate,
    Rule,
    FieldSelection,
    TaskField,
    ChecklistSelection,
    Delay,
    RawDueDate,
    Workflow, TaskPerformer,
)
from src.processes.enums import TaskStatus
from src.processes.services.tasks.checklist_version import (
        ChecklistUpdateVersionService,
    )
from src.processes.services.base import (
    BaseUpdateVersionService,
)
from src.processes.utils.common import (
    insert_fields_values_to_text
)
from src.processes.services.tasks.mixins import (
    ConditionMixin,
)
from src.processes.services.tasks.task import (
    TaskService
)


UserModel = get_user_model()


class TaskUpdateVersionService(
    BaseUpdateVersionService,
    ConditionMixin,
):

    # TODO Very bad code. Needs to be refactored

    def _update_fields(
        self,
        data: Optional[List[Dict]] = None
    ):

        # TODO Move to TaskFieldService

        field_ids = []
        if data:
            for field_data in data:
                field, _ = self._update_field(field_data)
                field_ids.append(field.id)
                if field_data.get('selections'):
                    selection_ids = set()
                    for selection_data in field_data['selections']:
                        selection, __ = (
                            FieldSelection.objects.update_or_create(
                                field=field,
                                api_name=selection_data['api_name'],
                                defaults={
                                    'value': selection_data['value'],
                                }
                            )
                        )
                        selection_ids.add(selection.id)
                    field.selections.exclude(id__in=selection_ids).delete()
        self.instance.output.exclude(id__in=field_ids).delete()

    def _update_delay(self, new_duration: Optional[str] = None):

        existent_delay = self.instance.get_active_delay()
        if new_duration:
            if existent_delay:
                if not existent_delay.directly_status:
                    # Update existent delay from template
                    new_duration = parse_duration(new_duration)
                    if existent_delay.duration != new_duration:
                        existent_delay.duration = new_duration
                        existent_delay.save(update_fields=['duration'])
            else:
                # Create new delay from template
                Delay.objects.create(
                    task=self.instance,
                    duration=new_duration,
                    workflow=self.instance.workflow
                )
        else:  # noqa: PLR5501
            if existent_delay:
                if self.instance.is_active:
                    if not existent_delay.directly_status:
                        # Deactivate existent delay from template
                        existent_delay.end_date = timezone.now()
                        existent_delay.save(update_fields=['end_date'])
                else:
                    # Deactivate delay from template for inactive tasks
                    existent_delay.delete()

    def _update_conditions(
        self,
        data: Optional[List[dict]] = None
    ):
        self.instance.conditions.all().delete()
        if not data:
            return

        conditions_tree = {}
        conditions = []
        for condition_data in data:
            rules = condition_data.get('rules')
            conditions.append(
                Condition(
                    action=condition_data['action'],
                    order=condition_data['order'],
                    api_name=condition_data['api_name'],
                    task=self.instance,
                )
            )
            rules_tree = []
            for rule_template in rules:
                predicate_templates = rule_template.get('predicates')
                predicates = []
                for predicate_template in predicate_templates:
                    predicates.append(Predicate(
                        operator=predicate_template['operator'],
                        field_type=predicate_template['field_type'],
                        value=predicate_template['value'],
                        field=predicate_template['field'],
                        api_name=predicate_template['api_name'],
                    ))
                rules_tree.append((
                    Rule(api_name=rule_template['api_name']),
                    predicates
                ))
            conditions_tree[condition_data['api_name']] = rules_tree
        conditions = Condition.objects.bulk_create(conditions)
        self.create_rules(conditions, conditions_tree)

    def _update_field(self, template: Dict):

        # TODO Move to TaskFieldService

        return TaskField.objects.update_or_create(
            task=self.instance,
            api_name=template['api_name'],
            defaults={
                'name': template['name'],
                'description': template['description'],
                'type': template['type'],
                'is_required': template['is_required'],
                'order': template['order'],
                'workflow': self.instance.workflow
            }
        )

    def _update_checklists(
        self,
        version: int,
        fields_values: Dict[str, str],
        data: Optional[List[dict]] = None,
    ):
        api_names = set()
        if data:
            for checklist_data in data:
                checklist_service = ChecklistUpdateVersionService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type
                )
                checklist_service.update_from_version(
                    data=checklist_data,
                    version=version,
                    fields_values=fields_values,
                    task=self.instance
                )
                api_names.add(checklist_data['api_name'])
        self.instance.checklists.exclude(api_name__in=api_names).delete()
        self.instance.checklists_total = (
            ChecklistSelection.objects.filter(
                checklist__task=self.instance
            ).count()
        )
        self.instance.checklists_marked = (
            ChecklistSelection.objects.filter(
                checklist__task=self.instance
            ).marked().count()
        )
        self.instance.save(
            update_fields=[
                'checklists_total',
                'checklists_marked'
            ]
        )

    def _update_raw_due_date(
        self,
        data: Optional[dict] = None,
    ):

        if data is None:
            RawDueDate.objects.filter(task=self.instance).delete()
        else:
            RawDueDate.objects.update_or_create(
                task=self.instance,
                defaults={
                    'rule': data['rule'],
                    'api_name': data['api_name'],
                    'duration': parse_duration(data['duration']),
                    'duration_months': data.get('duration_months', 0),
                    'source_id': data['source_id'],
                }
            )

    def _create_or_update_instance(
        self,
        data: dict,
        workflow: Workflow,
        fields_values: Dict[str, str]
    ):

        defaults = {
            'require_completion_by_all': data[
                'require_completion_by_all'
            ],
            'name_template': data['name'],
            'name': insert_fields_values_to_text(
                text=data['name'],
                fields_values=fields_values,
            ),
            'number': data['number'],
            'description': insert_fields_values_to_text(
                text=data['description'],
                fields_values=fields_values,
            ),
            'clear_description': insert_fields_values_to_text(
                text=data['clear_description'],
                fields_values=fields_values,
            ),
            'description_template': data['description'],
            'is_urgent': workflow.is_urgent,
            'revert_task': data['revert_task'],
            'parents': data['parents'],
        }

        self.instance, _ = Task.objects.update_or_create(
            account=workflow.account,
            workflow=workflow,
            api_name=data['api_name'],
            defaults=defaults
        )
        return self.instance

    def _update_performers(
        self,
        data: dict,
    ):
        send_new_task_recipients = set()
        send_removed_task_recipients = set()
        account = self.instance.account
        workflow = self.instance.workflow
        performer_before = (
            TaskPerformer.objects
            .exclude_directly_deleted()
            .by_task(self.instance.id)
            .get_user_ids_set()
        )
        self.instance.update_raw_performers_from_task_template(data)
        (
            created_user_ids,
            created_group_ids,
            deleted_user_ids,
            deleted_group_ids,
        ) = self.instance.update_performers()

        performer_after = (
            TaskPerformer.objects
            .exclude_directly_deleted()
            .by_task(self.instance.id)
            .get_user_ids_set()
        )

        if not performer_after:
            default_performer = (
                account.get_owner() if workflow.is_external
                else workflow.workflow_starter
            )
            self.instance.add_raw_performer(default_performer)
            self.instance.performers.add(default_performer)
            send_new_task_recipients.add(
                (
                    default_performer.id,
                    default_performer.email,
                    default_performer.is_new_tasks_subscriber
                )
            )
        if deleted_group_ids:
            for user in (
                account.users.
                get_users_in_groups(deleted_group_ids)
                .only('id', 'email')
            ):
                if user.id not in performer_after:
                    send_removed_task_recipients.add((user.id, user.email))
        if deleted_user_ids:
            for user in (
                account.users
                .filter(id__in=deleted_user_ids)
                .only('id', 'email')
            ):
                if user.id not in performer_after:
                    send_removed_task_recipients.add((user.id, user.email))
        if created_user_ids:
            for user in (
                account.users
                .filter(id__in=created_user_ids)
                .only('id', 'email', 'is_new_tasks_subscriber')
            ):
                if user.id not in performer_before:
                    send_new_task_recipients.add(
                        (user.id, user.email, user.is_new_tasks_subscriber)
                    )
        if created_group_ids:
            for user in (
                account.users
                .get_users_in_groups(created_group_ids)
                .only('id', 'email', 'is_new_tasks_subscriber')
            ):
                if user.id not in performer_before:
                    send_new_task_recipients.add(
                        (user.id, user.email, user.is_new_tasks_subscriber)
                    )
        task_data = None
        if send_new_task_recipients:
            wf_starter = workflow.workflow_starter
            wf_starter_name = wf_starter.name if wf_starter else None
            wf_starter_photo = wf_starter.photo if wf_starter else None
            task_data = self.instance.get_data_for_list()
            send_new_task_notification.delay(
                logging=account.log_api_requests,
                account_id=account.id,
                recipients=list(send_new_task_recipients),
                task_id=self.instance.id,
                task_name=self.instance.name,
                task_data=task_data,
                task_description=self.instance.description,
                workflow_name=workflow.name,
                template_name=workflow.get_template_name(),
                workflow_starter_name=wf_starter_name,
                workflow_starter_photo=wf_starter_photo,
                due_date_timestamp=(
                    self.instance.due_date.timestamp()
                    if self.instance.due_date else None
                ),
                logo_lg=account.logo_lg,
                is_returned=False
            )
        if send_removed_task_recipients:
            task_data = task_data or self.instance.get_data_for_list()
            send_removed_task_notification.delay(
                task_id=self.instance.id,
                recipients=list(send_removed_task_recipients),
                account_id=account.id,
                task_data=task_data
            )

    def update_from_version(
        self,
        data: dict,
        version: int,
        **kwargs
    ):
        """
            data = {
                'number': int,
                'name': str,
                'name_template': str,
                'description': str,
                'is_urgent': bool,
                'require_completion_by_all': bool,
                'fields': list,
                'checklists': list,
                'conditions': list,
                'raw_due_date: dict,
                'raw_performers': list,
                'delay': str,
                'parents': list,
                'revert_task': str,
            }
        """

        workflow = kwargs['workflow']
        completed_tasks_fields_values = workflow.get_fields_markdown_values(
            tasks_filter_kwargs={'task__status': TaskStatus.COMPLETED}
        )
        self._create_or_update_instance(
            data=data,
            workflow=workflow,
            fields_values=completed_tasks_fields_values
        )
        self._update_fields(data=data.get('fields'))
        self._update_conditions(data=data.get('conditions'))
        self._update_checklists(
            data=data.get('checklists'),
            version=version,
            fields_values=completed_tasks_fields_values
        )
        self._update_delay(new_duration=data.get('delay'))
        # Don't snooze active tasks if delay created
        if self.instance.is_active:
            self._update_performers(data)
            self._update_raw_due_date(data=data.get('raw_due_date'))
            service = TaskService(instance=self.instance, user=self.user)
            service.set_due_date_from_template()
        elif self.instance.is_pending:
            self.instance.update_raw_performers_from_task_template(data)
            self._update_raw_due_date(data=data.get('raw_due_date'))
            self.instance.taskperformer_set.exclude_directly_deleted(
                ).update(
                    is_completed=False,
                    date_completed=None
                )
