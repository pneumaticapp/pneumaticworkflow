from typing import Optional
from src.processes.enums import FieldType
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import Task


RESPONSE_FORMAT_PROMPT = (
    '# RESPONSE FORMAT\n'
    'Split your answer into sections, '
    'one section per output field listed below.\n'
    'Start every section with a markdown heading of level 2 that contains '
    'only the api_name of the field, '
    'the value of the field follows on the next lines:\n'
    '\n'
    '## <api_name>\n'
    '<value>\n'
    '\n'
    'Rules:\n'
    '- Return the sections in the order they are listed below '
    'and nothing else:\n'
    '  no greetings, no explanations, no text outside the sections.\n'
    '- Use the api_name exactly as it is given, do not translate or rename '
    'it.\n'
    '- Do not use level 2 headings inside a value, use level 3 or deeper.\n'
    '- The value must match the value format of the field.\n'
    '- If a field is not required and there is nothing to put in it,\n'
    '  return the section with an empty value.\n'
    '\n'
    'Fields:'
)


class TaskUserMessageService:

    """ Creates a user message that passes the task to an AI agent """

    def __init__(self, task: Task):
        self.task = task

    def _get_return_comment(self) -> Optional[str]:

        """ Text of the comment the task was returned for rework with.
            None if the current task run was not started by a return """

        events = WorkflowEvent.objects.on_task(self.task.id)
        revert_event = events.task_revert().order_by('-created').first()
        if revert_event is None:
            return None
        complete_event = events.task_complete().order_by('-created').first()
        if complete_event and complete_event.created > revert_event.created:
            return None
        return revert_event.text

    def _get_task_message(self) -> str:

        """ Task name, description and the rework comment """

        parts = [
            f'# TASK\n{self.task.name}',
            f'# DESCRIPTION\n{self.task.description}',
        ]
        comment = self._get_return_comment()
        if comment:
            parts.append(
                '# RETURNED FOR REWORK\n'
                'The task was returned to you for rework. '
                'Comment of the user who returned it:\n'
                f'{comment}',
            )
        return '\n\n'.join(parts)

    def _get_attachments_message(self) -> str:

        """ Content of the files attached to the task. Not implemented yet """

        return ''

    def _get_response_format_message(self) -> str:

        """ Explains how the answer should be formatted """

        fields = self.task.output.filter(
            type__in=(FieldType.STRING, FieldType.TEXT),
        )
        fields_prompts = []
        for field in fields:
            fields_prompts.append(
                self._get_field_prompt_by_type(field=field),
            )
        return '\n\n'.join([RESPONSE_FORMAT_PROMPT, *fields_prompts])

    def get_message(self) -> str:
        parts = (
            self._get_task_message(),
            self._get_attachments_message(),
            self._get_response_format_message(),
        )
        return '\n\n'.join(part for part in parts if part)
