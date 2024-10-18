from dataclasses import dataclass, field
from typing import List

from pneumatic_backend.processes.models import FieldTemplate


@dataclass
class TaskForTasksDigest:
    task_id: int
    task_name: str
    started: int = 0
    in_progress: int = 0
    overdue: int = 0
    completed: int = 0


@dataclass
class TemplateForTasksDigest:
    template_id: int
    template_name: str
    started: int = 0
    in_progress: int = 0
    overdue: int = 0
    completed: int = 0
    tasks: List[TaskForTasksDigest] = field(default_factory=list)

    @property
    def fields(self):
        if not getattr(self, '_fields', None):
            query = FieldTemplate.objects.by_template(self.template_id).values(
                'api_name',
                'name',
            )
            setattr(
                self,
                '_fields',
                {item['api_name']: item['name'] for item in query},
            )
        return getattr(self, '_fields', None)


@dataclass
class TemplateForWorkflowsDigest:
    template_id: int
    template_name: str
    started: int = 0
    in_progress: int = 0
    overdue: int = 0
    completed: int = 0


@dataclass
class WorkflowsDigest:
    """Describes a structure of Weekly workflows digest.
    Overdue count is number of workflows have overdue tasks
    ONLY during specified date range.
    """
    templates: List[TemplateForWorkflowsDigest] = field(default_factory=list)
    started: int = 0
    in_progress: int = 0
    overdue: int = 0
    completed: int = 0


@dataclass
class TasksDigest:
    """Describes a structure of Weekly tasks digest."""
    templates: List[TemplateForTasksDigest] = field(default_factory=list)
    started: int = 0
    in_progress: int = 0
    overdue: int = 0
    completed: int = 0

    @property
    def tmp(self):
        return getattr(self, '_template', None)

    @tmp.setter
    def tmp(self, template: TemplateForTasksDigest):
        setattr(self, '_template', template)

    def put_tmp(self):
        if self.tmp:
            self.templates.append(self.tmp)
            self.tmp = None
