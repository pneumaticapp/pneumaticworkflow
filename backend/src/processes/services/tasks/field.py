import re
from decimal import Decimal, DecimalException
from typing import Any, Iterable, List, NamedTuple, Optional, Set, Union

from django.contrib.auth import get_user_model
from django.core.exceptions import (
    ValidationError as ValidationCoreError,
)
from django.db.models import ObjectDoesNotExist

from src.generics.validators import NoSchemaURLValidator
from src.processes.enums import FieldType
from src.processes.messages import workflow as messages
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.services.base import BaseWorkflowService
from src.processes.services.tasks.exceptions import TaskFieldException
from src.processes.services.tasks.selection import SelectionService
from src.services.markdown import MarkdownService
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.utils import (
    extract_file_ids_from_text,
    sync_storage_attachments_for_scope,
)
from src.utils.dates import date_tsp_to_user_fmt

UserModel = get_user_model()


class FieldData(NamedTuple):
    value: str = ''
    markdown_value: str = ''
    clear_value: str = ''
    user_id: Optional[str] = None
    group_id: Optional[str] = None


class TaskFieldService(BaseWorkflowService):

    NULL_VALUES = (None, '', [])
    STRING_LENGTH = 140

    def _get_valid_number_value(self, raw_value: Any, **kwargs) -> FieldData:

        try:
            value = Decimal(raw_value)
        except (TypeError, ValueError, DecimalException) as ex:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0084,
            ) from ex
        return FieldData(
            value=value,
            markdown_value=value,
            clear_value=value,
        )

    def _get_valid_string_value(self, raw_value: Any, **kwargs) -> FieldData:

        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0025,
            )
        if len(raw_value) > self.STRING_LENGTH:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0026(self.STRING_LENGTH),
            )
        return FieldData(
            value=raw_value,
            markdown_value=raw_value,
            clear_value=MarkdownService.clear(raw_value),
        )

    def _get_valid_text_value(self, raw_value: Any, **kwargs) -> FieldData:

        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0025,
            )
        return FieldData(
            value=raw_value,
            markdown_value=raw_value,
            clear_value=MarkdownService.clear(raw_value),
        )

    def _get_valid_radio_value(
        self,
        raw_value: str,
        selections: Iterable[FieldTemplateSelection],
    ) -> FieldData:

        """ Selections need for first create selection
            when TaskField selections doesn't exist """

        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0028,
            )
        try:
            selection = selections.get(api_name=raw_value)
        except ObjectDoesNotExist as ex:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0028,
            ) from ex
        else:
            return FieldData(
                value=selection.value,
                markdown_value=selection.value,
                clear_value=MarkdownService.clear(selection.value),
            )

    def _get_valid_checkbox_value(
        self,
        raw_value: List[str],
        selections: Iterable[FieldTemplateSelection],
    ) -> FieldData:

        if not isinstance(raw_value, list):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0029,
            )

        for el in raw_value:
            if not isinstance(el, str):
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0030,
                )

        selections_values = list(
            selections.by_api_names(raw_value).values_list('value', flat=True),
        )
        if len(selections_values) < len(raw_value):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0031,
            )
        value = ', '.join(selections_values)
        return FieldData(
            value=value,
            markdown_value=value,
            clear_value=MarkdownService.clear(value),
        )

    def _get_valid_date_value(
        self,
        raw_value: Any,
        **kwargs,
    ) -> FieldData:

        if not isinstance(raw_value, (int, float)):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0032,
            )
        value = str(raw_value)
        user_fmt_value = date_tsp_to_user_fmt(
            date_tsp=raw_value,
            user=self.user,
        )
        return FieldData(
            value=value,
            markdown_value=user_fmt_value,
            clear_value=user_fmt_value,
        )

    def _get_valid_url_value(self, raw_value: Any, **kwargs) -> FieldData:

        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0034,
            )
        try:
            NoSchemaURLValidator()(raw_value)
        except ValidationCoreError as ex:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0035,
            ) from ex
        else:
            markdown_value = f'[{self.instance.name}]({raw_value})'
            return FieldData(
                value=raw_value,
                markdown_value=markdown_value,
                clear_value=raw_value,
            )

    def _get_valid_dropdown_value(
        self,
        raw_value: Any,
        **kwargs,
    ) -> FieldData:

        return self._get_valid_radio_value(raw_value, **kwargs)

    def _get_valid_file_value(self, raw_value: Any, **kwargs) -> FieldData:
        """
        Validate file field value using new storage service.

        Args:
            raw_value: List of file_ids from new storage service

        Returns:
            FieldData with file information
        """
        if not isinstance(raw_value, list):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0036,
            )

        # In new architecture, raw_value contains file_ids (strings)
        file_ids = raw_value

        # For now, return a simple representation
        # In future, this could fetch file metadata from storage service
        if file_ids:
            value = ', '.join(file_ids)
            markdown_value = ', '.join(
                [f'File: {file_id}' for file_id in file_ids],
            )
        else:
            value = ''
            markdown_value = ''

        return FieldData(
            value=value,
            markdown_value=markdown_value,
            clear_value=value,
        )

    def _get_valid_user_value(self, raw_value: Any, **kwargs) -> FieldData:

        user_id = None
        group_id = None
        value = None

        if isinstance(raw_value, str):
            if re.match(
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                raw_value,
            ):
                try:
                    user = self.account.users.get(email__iexact=raw_value)
                    user_id = user.id
                    value = user.name_by_status
                except ObjectDoesNotExist:
                    pass
            else:
                try:
                    group = self.account.user_groups.get(
                        name__iexact=raw_value,
                    )
                    group_id = group.id
                    value = group.name
                except ObjectDoesNotExist:
                    pass
        if user_id is None and group_id is None:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0090,
            )
        return FieldData(
            user_id=user_id,
            group_id=group_id,
            value=value,
            markdown_value=value,
            clear_value=value,
        )

    def _get_valid_value(self, raw_value: Any, **kwargs) -> FieldData:
        if raw_value in self.NULL_VALUES:
            if self.instance.is_required:
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0023,
                )
            return FieldData()
        func = getattr(self, f'_get_valid_{self.instance.type}_value')
        return func(raw_value, **kwargs)

    def _create_instance(
        self,
        instance_template: FieldTemplate,
        **kwargs,
    ):
        self.instance = TaskField(
            kickoff_id=kwargs.get('kickoff_id'),
            task_id=kwargs.get('task_id'),
            type=instance_template.type,
            is_required=instance_template.is_required,
            name=instance_template.name,
            description=instance_template.description,
            api_name=instance_template.api_name,
            order=instance_template.order,
            workflow_id=kwargs['workflow_id'],
        )
        if not kwargs.get('skip_value'):
            raw_value = kwargs.get('value')
            selections = (
                instance_template.selections.all()
                if self.instance.type in FieldType.TYPES_WITH_SELECTIONS
                else None
            )
            # self.instance.value, self.instance.markdown_value = (
            field_data = self._get_valid_value(
                raw_value=raw_value,
                selections=selections,
            )
            self.instance.value = field_data.value
            self.instance.markdown_value = field_data.markdown_value
            self.instance.clear_value = field_data.clear_value
            self.instance.user_id = field_data.user_id
            self.instance.group_id = field_data.group_id
        self.instance.save()

    def _create_related(
        self,
        instance_template: FieldTemplate,
        **kwargs,
    ):
        skip_value = kwargs.get('skip_value')
        raw_value = kwargs.get('value')
        if self.instance.type == FieldType.FILE and not skip_value:
            self._link_new_attachments(raw_value)
        elif self.instance.type in FieldType.TYPES_WITH_SELECTIONS:
            if skip_value:
                self._create_selections(instance_template)
            else:
                self._create_selections_with_value(
                    raw_value=raw_value,
                    instance_template=instance_template,
                )

    def _link_new_attachments(
        self,
        file_ids: Optional[List[str]] = None,
    ):
        """
        Create new attachments for the task field in storage service.

        Args:
            file_ids: List of file_ids from new storage service
        """
        if file_ids not in self.NULL_VALUES:
            self._sync_storage_attachments(file_ids)

    def _create_selections(
        self,
        instance_template: FieldTemplate,
    ):

        for selection_template in instance_template.selections.all():
            selection_service = SelectionService(user=self.user)
            selection_service.create(
                instance_template=selection_template,
                field_id=self.instance.id,
                is_selected=False,
            )

    def _get_selections_values(
        self,
        raw_value: Union[str, List[str], None],
    ) -> Set:

        if self.instance.type in FieldType.TYPES_WITH_SELECTION:
            # selection api_name
            value = {raw_value}
        else:
            value = set()
            for el in raw_value:
                # selection api_name
                value.add(el)
        return value

    def _create_selections_with_value(
        self,
        raw_value: Union[str, List[str], None],
        instance_template: FieldTemplate,
    ):
        """ raw_value - validated FieldTemplateSelection id(s) or None """

        if raw_value in self.NULL_VALUES:
            for selection_template in instance_template.selections.all():
                selection_service = SelectionService(user=self.user)
                selection_service.create(
                    instance_template=selection_template,
                    field_id=self.instance.id,
                    is_selected=False,
                )
        else:
            selections_values = self._get_selections_values(raw_value)
            for selection_template in instance_template.selections.all():
                selection_service = SelectionService(user=self.user)
                selection_service.create(
                    instance_template=selection_template,
                    field_id=self.instance.id,
                    is_selected=(
                        selection_template.api_name in selections_values
                    ),
                )

    def _update_selections(self, raw_value: Union[str, List[str], None]):

        """ raw_value - validated FieldSelection id """

        if raw_value in self.NULL_VALUES:
            for selection in self.instance.selections.all():
                selection_service = SelectionService(
                    instance=selection,
                    user=self.user,
                )
                selection_service.partial_update(
                    is_selected=False,
                    force_save=True,
                )
        else:
            selections_values = self._get_selections_values(raw_value)
            for selection in self.instance.selections.all():
                selection_service = SelectionService(
                    instance=selection,
                    user=self.user,
                )
                selection_service.partial_update(
                    is_selected=selection.api_name in selections_values,
                    force_save=True,
                )

    def _remove_unused_attachments(
        self,
        value: Optional[str],
        file_ids: Optional[List[str]],
    ):
        """
        Remove unused attachments from new storage service.

        Args:
            value: Field value
            file_ids: List of file_ids to keep
        """
        if not file_ids:
            file_ids = []

        # Get current attachments for this field
        current_attachments = Attachment.objects.filter(
            task=self.instance.task,
            workflow=self.instance.workflow,
        )

        # Remove attachments not in the new file_ids list
        if value:
            current_attachments.exclude(file_id__in=file_ids).delete()
        else:
            # If no value, remove all attachments
            current_attachments.delete()

    def _sync_storage_attachments(
        self,
        file_ids: Optional[List[str]],
    ):
        """
        Create Attachment records for file_ids in new storage service.

        Args:
            file_ids: List of file_ids from new storage service
        """
        if file_ids in self.NULL_VALUES:
            return

        if self.instance.task_id:
            source_type = SourceType.TASK
        else:
            source_type = SourceType.WORKFLOW

        for file_id in file_ids:
            # Check if attachment already exists to avoid duplicates
            if not Attachment.objects.filter(file_id=file_id).exists():
                Attachment.objects.create(
                    file_id=file_id,
                    account=self.account,
                    source_type=source_type,
                    access_type=AccessType.RESTRICTED,
                    task=self.instance.task,
                    workflow=self.instance.workflow,
                )

    def partial_update(
        self,
        force_save=False,
        **update_kwargs,
    ) -> TaskField:

        """ Set or update field value only """

        old_markdown_value = self.instance.markdown_value
        raw_value = update_kwargs.pop('value', None)
        selections = (
            self.instance.selections.all()
            if self.instance.type in FieldType.TYPES_WITH_SELECTIONS
            else None
        )
        field_data = self._get_valid_value(
            raw_value=raw_value,
            selections=selections,
        )
        if self.instance.type == FieldType.FILE:
            self._remove_unused_attachments(
                value=raw_value,
                file_ids=raw_value if isinstance(raw_value, list) else [],
            )
        super().partial_update(
            force_save=True,
            value=field_data.value,
            markdown_value=field_data.markdown_value,
            clear_value=field_data.clear_value,
            user_id=field_data.user_id,
            group_id=field_data.group_id,
        )
        if self.instance.type == FieldType.FILE:
            self._link_new_attachments(raw_value)
        elif self.instance.type in FieldType.TYPES_WITH_SELECTIONS:
            self._update_selections(raw_value)
        elif self.instance.type in {
            FieldType.STRING,
            FieldType.TEXT,
            FieldType.URL,
        }:
            old_file_ids = extract_file_ids_from_text(old_markdown_value)
            new_file_ids = extract_file_ids_from_text(
                self.instance.markdown_value,
            )
            removed_file_ids = list(
                set(old_file_ids) - set(new_file_ids),
            )
            added_file_ids = list(
                set(new_file_ids) - set(old_file_ids),
            )
            source_type = (
                SourceType.TASK
                if self.instance.task_id
                else SourceType.WORKFLOW
            )
            sync_storage_attachments_for_scope(
                account=self.account,
                user=self.user,
                add_file_ids=added_file_ids,
                remove_file_ids=removed_file_ids,
                source_type=source_type,
                task=self.instance.task,
                workflow=self.instance.workflow,
                access_type=AccessType.RESTRICTED,
            )
        return self.instance
