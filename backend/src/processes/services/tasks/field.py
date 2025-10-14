from typing import List, Any, Union, Optional, Iterable, Set
from decimal import Decimal, DecimalException
from typing import NamedTuple
from django.db.models import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from src.generics.validators import NoSchemaURLValidator
from django.core.exceptions import (
    ValidationError as ValidationCoreError,
)
from src.processes.messages import workflow as messages
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.templates.fields import (
    FieldTemplateSelection,
    FieldTemplate,
)
from src.processes.models.workflows.fields import TaskField
from src.processes.services.base import BaseWorkflowService
from src.processes.services.tasks.exceptions import TaskFieldException
from src.processes.services.tasks.selection import SelectionService
from src.services.markdown import MarkdownService
from src.processes.enums import FieldType
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
        else:
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

        if not isinstance(raw_value, list):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0036,
            )
        try:
            attachments_ids = [int(attach_id) for attach_id in raw_value]
        except (ValueError, TypeError) as ex:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0036,
            ) from ex
        else:
            attachments = (
                FileAttachment.objects
                .on_account(self.account.id)
                .by_ids(attachments_ids)
                .only('name', 'url')
            )
            if hasattr(self.instance, 'id'):
                attachments = (
                    attachments.with_output_or_not_attached(self.instance.id)
                )
            else:
                attachments = attachments.not_attached()
            urls = [e.url for e in attachments]
            if len(urls) < len(attachments_ids):
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0037,
                )
            value = ', '.join(urls)
            markdown_value = ', '.join(
                [f'[{e.name}]({e.url})' for e in attachments],
            )
            return FieldData(
                value=value,
                markdown_value=markdown_value,
                clear_value=value,
            )

    def _get_valid_user_value(self, raw_value: Any, **kwargs) -> FieldData:

        try:
            user_id = int(raw_value)
        except (ValueError, TypeError) as ex:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0038,
            ) from ex
        else:
            user = self.account.users.by_id(user_id).first()
            if user is None:
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0039,
                )
            value = user.name_by_status
            return FieldData(
                value=value,
                markdown_value=value,
                clear_value=value,
                user_id=user_id,
            )

    def _get_valid_value(self, raw_value: Any, **kwargs) -> FieldData:
        if raw_value in self.NULL_VALUES:
            if self.instance.is_required:
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0023,
                )
            else:
                return FieldData()
        else:
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
        attachments_ids: Optional[List[int]] = None,
    ):

        """ Attach new account files to the task field
            attachments_ids - validated list ids """

        if attachments_ids not in self.NULL_VALUES:
            (
                FileAttachment.objects
                .on_account(self.account.id)
                .with_output_or_not_attached(self.instance.id)
                .by_ids(attachments_ids)
                .update(
                    output_id=self.instance.id,
                    workflow_id=self.instance.workflow.id,
                )
            )

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
        attachment_ids: Optional[List[str]],
    ):

        # TODO remove unused attachments
        #   instead of call DELETE /workflows/attachments/:id
        current_attach_ids = self.instance.attachments.ids_set()
        if value:
            new_attach_ids = {int(e) for e in attachment_ids}
            deleted_attach_ids = current_attach_ids - new_attach_ids
        else:
            deleted_attach_ids = current_attach_ids
        if deleted_attach_ids:
            FileAttachment.objects.filter(
                id__in=deleted_attach_ids,
            ).delete()

    def partial_update(
        self,
        force_save=False,
        **update_kwargs,
    ) -> TaskField:

        """ Set or update field value only """

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
                attachment_ids=raw_value,
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
        return self.instance
