from datetime import datetime, timedelta
from typing import Dict, Optional
from django.db.models import Q
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import (
    Task,
    TaskTemplate,
    ChecklistTemplateSelection,
    Condition,
    Predicate,
    Rule,
    Delay,
    RawDueDate,
    TaskField,
)
from pneumatic_backend.processes.enums import (
    DueDateRule,
    FieldType,
)
from pneumatic_backend.processes.api_v2.services.task.checklist import (
    ChecklistService,
)
from pneumatic_backend.processes.api_v2.services.base import (
    BaseWorkflowService,
)
from pneumatic_backend.processes.api_v2.services.task.field import (
    TaskFieldService
)
from pneumatic_backend.processes.utils.common import (
    insert_fields_values_to_text
)
from pneumatic_backend.processes.api_v2.mixins.task import (
    ConditionMixin,
)
from pneumatic_backend.notifications.tasks import send_due_date_changed
from pneumatic_backend.processes.api_v2.services import (
    WorkflowEventService,
)
from pneumatic_backend.services.markdown import MarkdownService

UserModel = get_user_model()


class TaskService(
    BaseWorkflowService,
    ConditionMixin,
):

    def _create_instance(
        self,
        instance_template: TaskTemplate,
        **kwargs,
    ):

        """ redefined_performer - the user who will be appointed
            as the performer of the task instead of performers
            from task template """

        workflow = kwargs['workflow']
        description = instance_template.description
        clear_description = MarkdownService.clear(description)
        self.instance = Task.objects.create(
            api_name=instance_template.api_name,
            account=workflow.account,
            workflow=workflow,
            name=instance_template.name,
            name_template=instance_template.name,
            description=description,
            clear_description=clear_description,
            description_template=instance_template.description,
            number=instance_template.number,
            template_id=instance_template.id,
            require_completion_by_all=(
                instance_template.require_completion_by_all
            ),
            is_urgent=workflow.is_urgent,
            checklists_total=ChecklistTemplateSelection.objects.filter(
                checklist__task=instance_template
            ).count()
        )

    def _create_related(
        self,
        instance_template: TaskTemplate,
        **kwargs
    ):

        self.create_raw_performers_from_template(
            instance_template=instance_template,
            redefined_performer=kwargs.get('redefined_performer')
        )
        self.create_fields_from_template(instance_template)
        self.create_conditions_from_template(instance_template)
        self.create_checklists_from_template(instance_template)
        self.create_raw_due_date_from_template(instance_template)
        if instance_template.delay:
            Delay.objects.create(
                task=self.instance,
                duration=instance_template.delay,
            )

    def partial_update(
        self,
        force_save=False,
        **update_kwargs
    ):
        if 'description' in update_kwargs.keys():
            update_kwargs['clear_description'] = MarkdownService.clear(
                update_kwargs['description']
            )
        super().partial_update(**update_kwargs)
        if 'date_started' in update_kwargs.keys():
            if self.instance.date_first_started is None:
                self.instance.date_first_started = (
                    update_kwargs['date_started']
                )
                self.update_fields.add('date_first_started')
        if force_save:
            self.save()

    def insert_fields_values(
        self,
        fields_values: Dict[str, str],
    ):
        self.instance.description = insert_fields_values_to_text(
            text=self.instance.description_template,
            fields_values=fields_values
        )
        self.instance.clear_description = MarkdownService.clear(
            self.instance.description
        )
        self.update_fields.add('description')
        self.update_fields.add('clear_description')
        self.instance.name = insert_fields_values_to_text(
            text=self.instance.name_template,
            fields_values=fields_values,
        )
        self.update_fields.add('name')
        self.save()
        for checklist in self.instance.checklists.all():
            checklist_service = ChecklistService(
                instance=checklist,
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            checklist_service.insert_fields_values(fields_values)

    def create_conditions_from_template(
        self,
        instance_template: TaskTemplate
    ):

        # TODO Move to ConditionService

        if instance_template.conditions.exists():
            conditions_tree = {}
            conditions = []

            for template in instance_template.conditions.all():
                conditions.append(
                    Condition(
                        action=template.action,
                        order=template.order,
                        task=self.instance,
                        template_id=template.id,
                    )
                )
                rules_tree = []
                for rule_template in template.rules.all():
                    predicates = []
                    for predicate_template in rule_template.predicates.all():
                        predicates.append(Predicate(
                            operator=predicate_template.operator,
                            field_type=predicate_template.field_type,
                            value=predicate_template.value,
                            field=predicate_template.field,
                            template_id=predicate_template.id,
                        ))
                    rules_tree.append((
                        Rule(template_id=rule_template.id),
                        predicates
                    ))
                conditions_tree[template.id] = rules_tree
            conditions = Condition.objects.bulk_create(conditions)
            self.create_rules(conditions, conditions_tree)

    def create_fields_from_template(self, instance_template: TaskTemplate):

        for field_template in instance_template.fields.all():
            service = TaskFieldService(user=self.user)
            service.create(
                instance_template=field_template,
                workflow_id=self.instance.workflow_id,
                task_id=self.instance.id,
                skip_value=True
            )

    def create_checklists_from_template(self, instance_template: TaskTemplate):
        for checklist_template in instance_template.checklists.all():
            checklist_service = ChecklistService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
            )
            checklist_service.create(
                instance_template=checklist_template,
                task=self.instance
            )

    def create_raw_performers_from_template(
        self,
        instance_template: TaskTemplate,
        redefined_performer: Optional[UserModel] = None
    ):
        if redefined_performer:
            self.instance.add_raw_performer(user=redefined_performer)
        else:
            self.instance.update_raw_performers_from_task_template(
                instance_template
            )

    def create_raw_due_date_from_template(
        self,
        instance_template: TaskTemplate
    ):
        raw_due_date_template = getattr(
            instance_template,
            'raw_due_date',
            None
        )
        if raw_due_date_template:
            RawDueDate.objects.create(
                task=self.instance,
                duration=raw_due_date_template.duration,
                duration_months=raw_due_date_template.duration_months,
                rule=raw_due_date_template.rule,
                source_id=raw_due_date_template.source_id,
                api_name=raw_due_date_template.api_name
            )

    def get_task_due_date(self) -> Optional[datetime]:

        """ Calculates the due date value by rule """

        raw_due_date = getattr(self.instance, 'raw_due_date', None)
        due_date = None
        if raw_due_date:
            start_date = None
            end_date = None
            rule = raw_due_date.rule
            duration = raw_due_date.duration
            if raw_due_date.duration_months > 0:
                duration += timedelta(days=(30 * raw_due_date.duration_months))

            if rule in DueDateRule.TASK_RULES:
                if rule == DueDateRule.AFTER_TASK_STARTED:
                    if self.instance.api_name == raw_due_date.source_id:
                        start_date = self.instance.date_first_started
                    else:
                        task = Task.objects.filter(
                            workflow_id=self.instance.workflow_id,
                            api_name=raw_due_date.source_id,
                            number__lt=self.instance.number
                        ).only('date_first_started').first()
                        if task:
                            start_date = task.date_first_started
                elif rule == DueDateRule.AFTER_TASK_COMPLETED:
                    task = Task.objects.filter(
                        workflow_id=self.instance.workflow_id,
                        api_name=raw_due_date.source_id,
                        number__lt=self.instance.number
                    ).only('date_completed').first()
                    if task:
                        start_date = task.date_completed
            elif rule in DueDateRule.FIELD_RULES:
                field = TaskField.objects.filter(
                    (
                        Q(task__number__lt=self.instance.number) |
                        Q(kickoff__workflow_id=self.instance.workflow_id)
                    ),
                    workflow_id=self.instance.workflow_id,
                    api_name=raw_due_date.source_id,
                    type=FieldType.DATE,
                ).first()
                if field and field.value:
                    if rule == DueDateRule.AFTER_FIELD:
                        start_date = datetime.strptime(
                            field.value, '%m/%d/%Y'
                        )
                    if rule == DueDateRule.BEFORE_FIELD:
                        end_date = datetime.strptime(field.value, '%m/%d/%Y')
            elif rule == DueDateRule.AFTER_WORKFLOW_STARTED:
                start_date = self.instance.workflow.date_created

            if start_date:
                due_date = start_date + duration
            elif end_date:
                due_date = end_date - duration
        return due_date

    def set_due_date_from_template(self):

        """ Update if not changed directly """

        if self.instance.due_date_directly_status:
            return
        due_date = self.get_task_due_date()
        if due_date != self.instance.due_date:
            self.partial_update(
                due_date=due_date,
                force_save=True
            )

    def set_due_date_directly(self, value: Optional[datetime] = None):

        self.partial_update(
            due_date=value,
            force_save=True
        )
        send_due_date_changed.delay(
            logging=self.user.account.log_api_requests,
            author_id=self.user.id,
            task_id=self.instance.id,
            task_name=self.instance.name,
            workflow_name=self.instance.workflow.name,
            account_id=self.instance.account_id,
        )
        WorkflowEventService.due_date_changed_event(
            task=self.instance,
            user=self.user
        )
