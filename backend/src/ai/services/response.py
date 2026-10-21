import html
import mimetypes
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Union
from zoneinfo import ZoneInfo
from django.contrib.auth import get_user_model
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import Task
from src.ai.services.entities import FieldTag
from src.storage.enums import SourceType, AccessType
from src.storage.services.file_service import FileServiceClient

UserModel = get_user_model()

FIELD_PATTERN = re.compile(
    r'<field\s+(?P<attrs>[^>]*?)'
    r'(?:/>|>(?P<value>.*?)</field\s*>)',
    re.DOTALL,
)
ATTR_PATTERN = re.compile(
    r'(?P<key>\w+)\s*=\s*["\'](?P<value>[^"\']*)["\']',
)
DATE_FORMATS = (
    '%Y-%m-%d',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%dT%H:%M:%S',
)
# The file name becomes the text of a "[filename](url)" markdown link
FILENAME_FORBIDDEN_CHARS = re.compile(
    r'[\[\]()\\/:*?"<>|\x00-\x1f\x7f-\x9f]',
)
DEFAULT_FILE_EXTENSION = '.txt'
DEFAULT_FILE_CONTENT_TYPE = 'text/plain'


class TaskResponseService:

    """ Parses an AI agent answer into the task output fields values """

    def __init__(self, task: Task, text: str, user: UserModel):
        self.task = task
        self.text = text
        self.user = user

    def _get_field_by_attrs(
        self,
        attrs: Dict[str, str],
        fields: List[TaskField],
    ) -> Optional[TaskField]:

        """ Field the answer tag refers to. The name is a fallback
            identifier in case the agent has mangled the api_name """

        api_name = attrs.get('api_name')
        for field in fields:
            if field.api_name == api_name:
                return field
        name = attrs.get('name', '').strip().lower()
        if not name:
            return None
        for field in fields:
            if field.name.strip().lower() == name:
                return field
        return None

    def _get_tag_attrs(self, tag_match: re.Match) -> Dict[str, str]:

        """ Attributes of a <field> tag of the answer, unescaped

            <field api_name="phone-1" name="Phone &amp; fax">
            -> {'api_name': 'phone-1', 'name': 'Phone & fax'} """

        raw_attrs = tag_match.group('attrs')
        attrs = {}
        for attr_match in ATTR_PATTERN.finditer(raw_attrs):
            key = attr_match.group('key')
            value = html.unescape(attr_match.group('value'))
            attrs[key] = value
        return attrs

    def _get_sections(
        self,
        fields: List[TaskField],
    ) -> Dict[str, List[FieldTag]]:

        """ Answer tags per field api_name in the order of appearance.
            Tags that do not refer to any of the fields are skipped """

        sections = defaultdict(list)
        for tag_match in FIELD_PATTERN.finditer(self.text):
            attrs = self._get_tag_attrs(tag_match=tag_match)
            field = self._get_field_by_attrs(attrs=attrs, fields=fields)
            if field is None:
                continue

            raw_value = tag_match.group('value') or ''
            value = raw_value.strip().replace('<\\/', '</')
            tag = FieldTag(value=value, attrs=attrs)
            sections[field.api_name].append(tag)
        return sections

    def _get_single_value(self, tags: List[FieldTag]) -> str:

        """ Value of a field the agent answers with a single tag """

        return tags[0].value if tags else ''

    def _get_checkbox_value(self, tags: List[FieldTag]) -> List[str]:

        """ Values of a field the agent answers with a tag per value """

        return [tag.value for tag in tags if tag.value]

    def _get_date_value(self, tags: List[FieldTag]) -> Union[str, float]:

        """ Timestamp of the date the agent answered with.
            The date is read in the timezone of the agent user.
            A date in an unknown format is treated as an empty value """

        raw_value = self._get_single_value(tags=tags)
        if not raw_value:
            return ''
        raw_value = raw_value.rstrip('Z')
        user_timezone = ZoneInfo(self.user.timezone)
        for date_format in DATE_FORMATS:
            try:
                date = datetime.strptime(raw_value, date_format).replace(
                    tzinfo=user_timezone,
                )
            except ValueError:
                continue
            return date.timestamp()
        return ''

    def _get_filename(self, tag: FieldTag) -> str:

        """ Name of a file the agent wrote, safe for a markdown link.
            A name without an extension gets the text one """

        raw_name = tag.attrs.get('filename') or tag.attrs.get('api_name')
        name = FILENAME_FORBIDDEN_CHARS.sub('', raw_name or '').strip()
        if not name:
            name = 'file'
        extension = os.path.splitext(name)[1]
        if extension:
            return name
        return f'{name}{DEFAULT_FILE_EXTENSION}'

    def _get_file_value(self, tags: List[FieldTag]) -> List[str]:

        """ Markdown links to the files the agent wrote, a tag per file.
            Every file is uploaded to the file service """

        tags = [tag for tag in tags if tag.value]
        if not tags:
            return []
        client = FileServiceClient(user=self.user)
        links = []
        for tag in tags:
            filename = self._get_filename(tag=tag)
            content_type = (
                mimetypes.guess_type(filename)[0]
                or DEFAULT_FILE_CONTENT_TYPE
            )
            public_url = client.upload_file_with_attachment(
                file_content=tag.value.encode('utf-8'),
                filename=filename,
                content_type=content_type,
                account=self.task.account,
                source_type=SourceType.TASK,
                access_type=AccessType.RESTRICTED,
            )
            links.append(f'[{filename}]({public_url})')
        return links

    def _get_field_value(
        self,
        field: TaskField,
        tags: List[FieldTag],
    ) -> Union[str, float, List[str]]:

        """ Value in the form the field validation expects it """

        get_field_value_func = getattr(
            self,
            f'_get_{field.type}_value',
            self._get_single_value,
        )
        return get_field_value_func(tags=tags)

    def get_fields_values(self) -> Dict[str, Union[str, float, List[str]]]:

        """ Values for all the fields the agent was asked to fill in.
            A field the agent skipped gets an empty value """

        fields = self.task.output.all()
        sections = self._get_sections(fields=fields)
        result = {}
        for field in fields:
            result[field.api_name] = self._get_field_value(
                field=field,
                tags=sections.get(field.api_name, []),
            )
        return result
