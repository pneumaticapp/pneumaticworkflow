import re
from typing import Dict
from src.processes.models.workflows.task import Task

SECTION_PATTERN = re.compile(
    r'^##(?!#)[ \t]*(?P<api_name>\S+)[ \t]*$',
    re.MULTILINE,
)


class TaskResponseService:

    """ Parses an AI agent answer into the task output fields values """

    def __init__(self, task: Task, text: str):
        self.task = task
        self.text = text

    def _get_sections(self) -> Dict[str, str]:

        """ Answer parts by the '## <api_name>' headings """

        sections = {}
        matches = list(SECTION_PATTERN.finditer(self.text))
        for number, match in enumerate(matches):
            if number + 1 < len(matches):
                end = matches[number + 1].start()
            else:
                end = len(self.text)
            value = self.text[match.end():end]
            sections[match.group('api_name')] = value.strip()
        return sections

    def get_fields_values(self) -> Dict[str, str]:

        """ Values for all the fields the agent was asked to fill in.
            A field the agent skipped gets an empty value """

        sections = self._get_sections()
        fields = self.task.output.all()
        return {
            field.api_name: sections.get(field.api_name, '')
            for field in fields
        }
