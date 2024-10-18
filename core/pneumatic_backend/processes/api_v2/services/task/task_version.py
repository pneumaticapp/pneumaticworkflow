from typing import Dict, Optional, List
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_duration
from pneumatic_backend.processes.models import (
    Task,
    Condition,
    Predicate,
    Rule,
    FieldSelection,
    TaskField,
    ChecklistSelection,
    Delay,
    RawDueDate,
    Workflow,
)
from pneumatic_backend.processes.api_v2.services.task\
    .checklist_version import (
        ChecklistUpdateVersionService,
    )
from pneumatic_backend.processes.api_v2.services.base import (
    BaseUpdateVersionService,
)
from pneumatic_backend.processes.utils.common import (
    insert_fields_values_to_text
)
from pneumatic_backend.processes.api_v2.mixins.task import (
    ConditionMixin,
)
from pneumatic_backend.processes.api_v2.services.task.task import (
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
                                template_id=selection_data['id'],
                                defaults={
                                    'value': selection_data['value'],
                                    'api_name': selection_data['api_name'],
                                }
                            )
                        )
                        selection_ids.add(selection.id)
                    field.selections.exclude(id__in=selection_ids).delete()
        self.instance.output.exclude(id__in=field_ids).delete()

    def _update_delay(self, new_duration: Optional[str] = None):

        active_delay = self.instance.get_active_delay()
        if new_duration:
            new_duration = parse_duration(new_duration)
            if active_delay:
                if not active_delay.directly_status:
                    if active_delay.duration != new_duration:
                        active_delay.duration = new_duration
                        active_delay.save(update_fields=['duration'])
            else:
                Delay.objects.create(
                    task=self.instance,
                    duration=new_duration,
                )
        elif active_delay:
            if self.instance.number == self.instance.workflow.current_task:
                if not active_delay.directly_status:
                    active_delay.end_date = timezone.now()
                    active_delay.save(update_fields=['end_date'])
            else:
                active_delay.delete()

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
                    template_id=condition_data['id'],
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
                        template_id=predicate_template['id'],
                    ))
                rules_tree.append((
                    Rule(template_id=rule_template['id']),
                    predicates
                ))
            conditions_tree[condition_data['id']] = rules_tree
        conditions = Condition.objects.bulk_create(conditions)
        self.create_rules(conditions, conditions_tree)

    def _update_field(self, template: Dict):

        # TODO Move to TaskFieldService

        return TaskField.objects.update_or_create(
            task=self.instance,
            template_id=template['id'],
            defaults={
                'name': template['name'],
                'description': template['description'],
                'type': template['type'],
                'is_required': template['is_required'],
                'api_name': template['api_name'],
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
        prev_tasks_fields_values: Dict[str, str]
    ):

        defaults = {
            'require_completion_by_all': data[
                'require_completion_by_all'
            ],
            'name_template': data['name'],
            'name': insert_fields_values_to_text(
                text=data['name'],
                fields_values=prev_tasks_fields_values,
            ),
            'number': data['number'],
            'description': insert_fields_values_to_text(
                text=data['description'],
                fields_values=prev_tasks_fields_values,
            ),
            'clear_description': insert_fields_values_to_text(
                text=data['clear_description'],
                fields_values=prev_tasks_fields_values,
            ),
            'description_template': data['description'],
            'is_urgent': workflow.is_urgent,
            'template_id': data['id']  # deprecated
        }
        if data['number'] > workflow.current_task:
            # Uncomplete tasks after current
            defaults['date_started'] = None
            defaults['date_completed'] = None
            defaults['is_completed'] = False

        self.instance, created = Task.objects.update_or_create(
            account=workflow.account,
            workflow=workflow,
            api_name=data['api_name'],
            defaults=defaults
        )
        if (
            created
            and self.instance.number < workflow.current_task
            and not self.instance.is_completed
            and not self.instance.is_skipped
            and not self.instance.date_first_started
        ):
            # skip new added task before current wf task
            self.instance.is_skipped = True
            self.instance.save(update_fields=['is_skipped'])
        return self.instance

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
            }
        """

        workflow = kwargs['workflow']
        prev_tasks_fields_values = workflow.get_fields_markdown_values(
            tasks_filter_kwargs={'number__lt': data['number']},
        )
        self._create_or_update_instance(
            data=data,
            workflow=workflow,
            prev_tasks_fields_values=prev_tasks_fields_values
        )
        self._update_fields(data=data.get('fields'))
        self._update_conditions(data=data.get('conditions'))
        self._update_checklists(
            data=data.get('checklists'),
            version=version,
            fields_values=prev_tasks_fields_values
        )
        self._update_delay(new_duration=data.get('delay'))

        if self.instance.number == workflow.current_task:
            self.instance.update_raw_performers_from_task_template(data)
            self.instance.update_performers()
            performers = self.instance.performers.exclude_directly_deleted()
            if not performers.exists():
                self.instance.add_raw_performer(workflow.workflow_starter)
                self.instance.performers.add(workflow.workflow_starter)
            self._update_raw_due_date(data=data.get('raw_due_date'))
            service = TaskService(
                instance=self.instance,
                user=self.user
            )
            service.set_due_date_from_template()
        elif self.instance.number > workflow.current_task:
            self.instance.update_raw_performers_from_task_template(data)
            self._update_raw_due_date(data=data.get('raw_due_date'))
            self.instance.taskperformer_set.exclude_directly_deleted(
                ).update(
                    is_completed=False,
                    date_completed=None
                )
