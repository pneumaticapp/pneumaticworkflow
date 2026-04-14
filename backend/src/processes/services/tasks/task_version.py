from typing import Dict, List, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_duration

from src.notifications.tasks import (
    send_new_task_notification,
    send_removed_task_notification, send_new_task_websocket,
)
from src.processes.models.workflows.checklist import (
    ChecklistSelection,
)
from src.processes.models.workflows.conditions import (
    Condition,
    Predicate,
    Rule,
)
from src.processes.models.workflows.fieldset import (
    FieldSet,
    FieldSetRule,
)
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.models.workflows.raw_due_date import RawDueDate
from src.processes.models.workflows.task import (
    Delay,
    Task,
    TaskPerformer,
)
from src.processes.models.workflows.workflow import Workflow
from src.processes.services.base import (
    BaseUpdateVersionService,
)
from src.processes.services.tasks.checklist_version import (
    ChecklistUpdateVersionService,
)
from src.processes.services.tasks.mixins import (
    ConditionMixin,
)
from src.processes.services.tasks.task import (
    TaskService,
)
from src.processes.utils.common import (
    insert_fields_values_to_text,
)

UserModel = get_user_model()


class TaskUpdateVersionService(
    BaseUpdateVersionService,
    ConditionMixin,
):

    # TODO Very bad code. Needs to be refactored

    def _update_field_selections(
        self,
        field: TaskField,
        field_data: Dict,
    ) -> None:

        if field_data.get('selections'):
            selection_ids = set()
            for selection_data in field_data['selections']:
                selection, __ = (
                    FieldSelection.objects.update_or_create(
                        field=field,
                        api_name=selection_data['api_name'],
                        defaults={
                            'value': selection_data['value'],
                        },
                    )
                )
                selection_ids.add(selection.id)
            field.selections.exclude(id__in=selection_ids).delete()

    def _update_fields(
        self,
        data: Optional[List[Dict]] = None,
    ):

        # TODO Move to TaskFieldService

        field_ids = []
        if data:
            for field_data in data:
                field, _ = self._update_field(field_data, fieldset=None)
                field_ids.append(field.id)
                self._update_field_selections(field, field_data)
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
                    workflow=self.instance.workflow,
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
        data: Optional[List[dict]] = None,
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
                ),
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
                        user_id=predicate_template['user_id'],
                        group_id=predicate_template['group_id'],
                    ))
                rules_tree.append((
                    Rule(api_name=rule_template['api_name']),
                    predicates,
                ))
            conditions_tree[condition_data['api_name']] = rules_tree
        conditions = Condition.objects.bulk_create(conditions)
        self.create_rules(conditions, conditions_tree)

    def _update_field(
        self,
        field_data: Dict,
        fieldset: Optional[FieldSet] = None,
    ):

        # TODO Move to TaskFieldService

        return TaskField.objects.update_or_create(
            task=self.instance,
            api_name=field_data['api_name'],
            fieldset=fieldset,
            defaults={
                'name': field_data['name'],
                'description': field_data['description'],
                'type': field_data['type'],
                'is_required': field_data['is_required'],
                'is_hidden': field_data['is_hidden'],
                'order': field_data['order'],
                'workflow': self.instance.workflow,
                'account': self.instance.account,
                'dataset_id': field_data['dataset_id'],
            },
        )

    def _update_fieldset_rules(
        self,
        fieldset: FieldSet,
        rules_data: Optional[List[Dict]],
    ) -> None:

        rule_ids = []
        rules_data = rules_data or []
        for rule_data in rules_data:
            rule, _ = FieldSetRule.objects.update_or_create(
                fieldset=fieldset,
                api_name=rule_data['api_name'],
                defaults={
                    'account_id': fieldset.account_id,
                    'type': rule_data['type'],
                    'value': rule_data.get('value'),
                },
            )
            rule_ids.append(rule.id)
        fieldset.rules.exclude(id__in=rule_ids).delete()

    def _update_fieldset_fields(
        self,
        fieldset: FieldSet,
        fields_data: Optional[List[Dict]],
    ) -> None:

        field_ids = []
        fields_data = fields_data or []
        for field_data in fields_data:
            field, _ = self._update_field(field_data, fieldset=fieldset)
            field_ids.append(field.id)
            self._update_field_selections(field, field_data)
        fieldset.fields.exclude(id__in=field_ids).delete()

    def _update_fieldsets(self, data: Optional[List]) -> None:

        fieldset_api_names = set()
        for fieldset_data in data or []:
            fieldset, _ = FieldSet.objects.update_or_create(
                workflow=self.instance.workflow,
                task=self.instance,
                api_name=fieldset_data['api_name'],
                defaults={
                    'account_id': self.instance.account_id,
                    'name': fieldset_data['name'],
                    'description': fieldset_data['description'],
                    'order': fieldset_data['order'],
                    'label_position': fieldset_data['label_position'],
                    'layout': fieldset_data['layout'],
                },
            )
            self._update_fieldset_rules(
                fieldset=fieldset,
                rules_data=fieldset_data.get('rules'),
            )
            self._update_fieldset_fields(
                fieldset=fieldset,
                fields_data=fieldset_data.get('fields'),
            )
            fieldset_api_names.add(fieldset.api_name)
        FieldSet.objects.filter(
            task=self.instance,
        ).exclude(api_name__in=fieldset_api_names).delete()

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
                    auth_type=self.auth_type,
                )
                checklist_service.update_from_version(
                    data=checklist_data,
                    version=version,
                    fields_values=fields_values,
                    task=self.instance,
                )
                api_names.add(checklist_data['api_name'])
        self.instance.checklists.exclude(api_name__in=api_names).delete()
        self.instance.checklists_total = (
            ChecklistSelection.objects.filter(
                checklist__task=self.instance,
            ).count()
        )
        self.instance.checklists_marked = (
            ChecklistSelection.objects.filter(
                checklist__task=self.instance,
            ).marked().count()
        )
        self.instance.save(
            update_fields=[
                'checklists_total',
                'checklists_marked',
            ],
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
                },
            )

    def _create_or_update_instance(
        self,
        data: dict,
        workflow: Workflow,
        fields_values: Dict[str, str],
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
            defaults=defaults,
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
                    default_performer.is_new_tasks_subscriber,
                ),
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
                        (user.id, user.email, user.is_new_tasks_subscriber),
                    )
        if created_group_ids:
            for user in (
                account.users
                .get_users_in_groups(created_group_ids)
                .only('id', 'email', 'is_new_tasks_subscriber')
            ):
                if user.id not in performer_before:
                    send_new_task_recipients.add(
                        (user.id, user.email, user.is_new_tasks_subscriber),
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
                is_returned=False,
            )
            send_new_task_websocket.delay(
                logging=account.log_api_requests,
                task_id=self.instance.id,
                recipients=list(send_new_task_recipients),
                account_id=account.id,
                task_data=task_data,
            )
        if send_removed_task_recipients:
            task_data = task_data or self.instance.get_data_for_list()
            send_removed_task_notification.delay(
                task_id=self.instance.id,
                recipients=list(send_removed_task_recipients),
                account_id=account.id,
                task_data=task_data,
            )

    def update_from_version(
        self,
        data: dict,
        version: int,
        **kwargs,
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
                'fieldsets': list,
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
        tasks_fields_values = workflow.get_fields_markdown_values()
        self._create_or_update_instance(
            data=data,
            workflow=workflow,
            fields_values=tasks_fields_values,
        )
        self._update_fields(data=data.get('fields'))
        self._update_fieldsets(data=data.get('fieldsets'))
        self._update_conditions(data=data.get('conditions'))
        self._update_checklists(
            data=data.get('checklists'),
            version=version,
            fields_values=tasks_fields_values,
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
                    date_completed=None,
                )
