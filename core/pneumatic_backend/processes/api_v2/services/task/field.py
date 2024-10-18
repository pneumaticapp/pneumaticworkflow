from datetime import datetime
from typing import List, Any, Union, Optional, Iterable, Set
from django.db.models import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from pneumatic_backend.generics.validators import NoSchemaURLValidator
from django.core.exceptions import (
    ValidationError as ValidationCoreError
)
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.processes.models import (
    FieldTemplate,
    FileAttachment,
    TaskField,
    FieldTemplateSelection,
)
from pneumatic_backend.processes.enums import FieldType
from pneumatic_backend.processes.api_v2.services.base import (
    BaseWorkflowService
)
from pneumatic_backend.processes.api_v2.services.task.exceptions import (
    TaskFieldException
)
from pneumatic_backend.processes.api_v2.services.task.selection import (
    SelectionService
)
from pneumatic_backend.services.markdown import MarkdownService


UserModel = get_user_model()


class TaskFieldService(BaseWorkflowService):

    NULL_VALUES = (None, '', [])
    STRING_LENGTH = 140

    def _get_valid_string_value(self, raw_value: Any, **kwargs) -> str:
        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0025
            )
        if len(raw_value) > self.STRING_LENGTH:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0026(self.STRING_LENGTH)
            )
        return raw_value

    def _get_valid_text_value(self, raw_value: Any, **kwargs) -> str:
        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0025
            )
        return raw_value

    def __get_selections_values_by_ids(
        self,
        selection_ids: list,
        selections: Iterable[FieldTemplateSelection]
    ) -> str:

        # TODO Remove in https://my.pneumatic.app/workflows/34311/
        try:
            # TODO raw_value FieldTemplateSelection id
            #   Remove in https://my.pneumatic.app/workflows/34311/
            selections_ids = [
                int(selection_id) for selection_id in selection_ids
            ]
        except (ValueError, TypeError):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0030
            )
        else:
            selections_values = list(
                selections.by_ids(
                    selections_ids
                ).values_list('value', flat=True)
            )
            if len(selections_values) < len(selections_ids):
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0031
                )
            else:
                return ', '.join(selections_values)

    def __get_selection_value_by_id(
        self,
        selection_id: str,
        selections: Iterable[FieldTemplateSelection]
    ) -> str:

        # TODO Remove in https://my.pneumatic.app/workflows/34311/

        try:
            # raw_value FieldTemplateSelection id
            selection_id = int(selection_id)
        except (ValueError, TypeError):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0028
            )
        try:
            # FieldTemplate selections
            selection = selections.get(id=selection_id)
        except ObjectDoesNotExist:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0028
            )
        else:
            return selection.value

    def _get_valid_radio_value(
        self,
        raw_value: str,
        selections: Iterable[FieldTemplateSelection]
    ) -> str:

        """ Selections need for first create selection
            when TaskField selections doesn't exist """

        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0028
            )
        try:
            selection = selections.get(api_name=raw_value)
        except ObjectDoesNotExist:
            # TODO Remove in https://my.pneumatic.app/workflows/34311/
            return self.__get_selection_value_by_id(
                selection_id=raw_value,
                selections=selections
            )
            # TODO Uncomment in https://my.pneumatic.app/workflows/34311/
            # raise TaskFieldException(
            #     api_name=self.instance.api_name,
            #     message=messages.MSG_PW_0028
            # )
        else:
            return selection.value

    def _get_valid_checkbox_value(
        self,
        raw_value: List[str],
        selections: Iterable[FieldTemplateSelection]
    ) -> str:

        if not isinstance(raw_value, list):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0029
            )

        for el in raw_value:
            if not isinstance(el, str):
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0030
                )

        selections_values = list(
            selections.by_api_names(raw_value).values_list('value', flat=True)
        )
        if len(selections_values) < len(raw_value):
            # TODO Remove in https://my.pneumatic.app/workflows/34311/
            return self.__get_selections_values_by_ids(
                selection_ids=raw_value,
                selections=selections
            )
            # TODO Uncomment in https://my.pneumatic.app/workflows/34311/
            # raise TaskFieldException(
            #     api_name=self.instance.api_name,
            #     message=messages.MSG_PW_0031
            # )
        else:
            return ', '.join(selections_values)

    def _get_valid_date_value(self, raw_value: Any, **kwargs) -> str:
        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0032
            )
        try:
            datetime.strptime(raw_value, '%m/%d/%Y')
        except ValueError:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0033
            )
        else:
            return raw_value

    def _get_valid_url_value(self, raw_value: Any, **kwargs) -> str:
        if not isinstance(raw_value, str):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0034
            )
        try:
            NoSchemaURLValidator()(raw_value)
        except ValidationCoreError:
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0035
            )
        else:
            return raw_value

    def _get_valid_dropdown_value(self, raw_value: Any, **kwargs) -> str:
        return self._get_valid_radio_value(raw_value, **kwargs)

    def _get_valid_file_value(self, raw_value: Any, **kwargs) -> str:

        if not isinstance(raw_value, list):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0036
            )
        try:
            attachments_ids = [int(attach_id) for attach_id in raw_value]
        except (ValueError, TypeError):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0036
            )
        else:
            qst = FileAttachment.objects.on_account(self.account.id).by_ids(
                attachments_ids
            )
            if hasattr(self.instance, 'id'):
                qst = qst.with_output_or_not_attached(self.instance.id)
            else:
                qst = qst.not_attached()
            urls = list(qst.only_urls())
            if len(urls) < len(attachments_ids):
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0037
                )
            return ', '.join(urls)

    def _get_valid_user_value(self, raw_value: Any, **kwargs) -> str:
        try:
            value = int(raw_value)
        except (ValueError, TypeError):
            raise TaskFieldException(
                api_name=self.instance.api_name,
                message=messages.MSG_PW_0038
            )
        else:
            user = self.account.users.by_id(value).first()
            if user is None:
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0039
                )
            return user.name_by_status

    def _get_valid_value(self, raw_value: Any, **kwargs) -> str:
        value = ''
        if raw_value in self.NULL_VALUES:
            if self.instance.is_required:
                raise TaskFieldException(
                    api_name=self.instance.api_name,
                    message=messages.MSG_PW_0023
                )
            else:
                return value
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
            template_id=instance_template.id,
            workflow_id=kwargs['workflow_id']
        )
        if not kwargs.get('skip_value'):
            raw_value = kwargs.get('value')
            selections = (
                instance_template.selections.all()
                if self.instance.type in FieldType.TYPES_WITH_SELECTIONS
                else None
            )
            self.instance.value = self._get_valid_value(
                raw_value=raw_value,
                selections=selections
            )
            self.instance.clear_value = MarkdownService.clear(
                self.instance.value
            )
            if self.instance.type == FieldType.USER:
                self.instance.user_id = int(raw_value)
        self.instance.save()

    def _create_related(
        self,
        instance_template: FieldTemplate,
        **kwargs
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
                    instance_template=instance_template
                )

    def _link_new_attachments(
        self,
        attachments_ids: Optional[List[int]] = None
    ):

        """ Attach new account files to the task field
            attachments_ids - validated list ids """

        if attachments_ids not in self.NULL_VALUES:
            FileAttachment.objects.on_account(
                self.account.id
            ).with_output_or_not_attached(self.instance.id).by_ids(
                attachments_ids
            ).update(
                output_id=self.instance.id,
                workflow_id=self.instance.workflow.id
            )

    def _create_selections(
        self,
        instance_template: FieldTemplate
    ):

        for selection_template in instance_template.selections.all():
            selection_service = SelectionService(user=self.user)
            selection_service.create(
                instance_template=selection_template,
                field_id=self.instance.id,
                is_selected=False
            )

    def _get_selections_values(
        self,
        raw_value: Union[str, List[str], None]
    ) -> Set:

        if self.instance.type in FieldType.TYPES_WITH_SELECTION:
            try:
                # TODO Remove in https://my.pneumatic.app/workflows/34311/
                # selection id
                value = {int(raw_value)}
            except ValueError:
                # selection api_name
                value = {raw_value}
        else:
            value = set()
            for el in raw_value:
                try:
                    # TODO Remove in
                    #  https://my.pneumatic.app/workflows/34311/
                    # selection id
                    value.add(int(el))
                except ValueError:
                    # selection api_name
                    value.add(el)
        return value

    def _create_selections_with_value(
        self,
        raw_value: Union[str, List[str], None],
        instance_template: FieldTemplate
    ):
        """ raw_value - validated FieldTemplateSelection id(s) or None """

        if raw_value in self.NULL_VALUES:
            for selection_template in instance_template.selections.all():
                selection_service = SelectionService(user=self.user)
                selection_service.create(
                    instance_template=selection_template,
                    field_id=self.instance.id,
                    is_selected=False
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
                        # Remove in https://my.pneumatic.app/workflows/34311/
                        or selection_template.id in selections_values
                    )
                )

    def _update_selections(self, raw_value: Union[str, List[str], None]):

        """ raw_value - validated FieldSelection id """

        if raw_value in self.NULL_VALUES:
            for selection in self.instance.selections.all():
                selection_service = SelectionService(
                    instance=selection,
                    user=self.user
                )
                selection_service.partial_update(
                    is_selected=False,
                    force_save=True
                )
        else:
            selections_values = self._get_selections_values(raw_value)
            for selection in self.instance.selections.all():
                selection_service = SelectionService(
                    instance=selection,
                    user=self.user
                )
                selection_service.partial_update(
                    is_selected=(
                        selection.api_name in selections_values
                        # Remove in https://my.pneumatic.app/workflows/34311/
                        or selection.id in selections_values
                    ),
                    force_save=True
                )

    def partial_update(
        self,
        force_save=False,
        **update_kwargs
    ) -> TaskField:

        """ Set or update field value only """

        raw_value = update_kwargs.pop('value', None)
        selections = (
            self.instance.selections.all()
            if self.instance.type in FieldType.TYPES_WITH_SELECTIONS
            else None
        )
        # validate raw value
        value = self._get_valid_value(
            raw_value=raw_value,
            selections=selections
        )
        clear_value = MarkdownService.clear(value)
        if self.instance.type == FieldType.FILE:
            # TODO remove unused attachments
            #   instead of call DELETE /workflows/attachments/:id
            current_attach_ids = self.instance.attachments.ids_set()
            if value:
                new_attach_ids = set(int(e) for e in raw_value)
                deleted_attach_ids = current_attach_ids - new_attach_ids
            else:
                deleted_attach_ids = current_attach_ids
            if deleted_attach_ids:
                FileAttachment.objects.filter(
                    id__in=deleted_attach_ids
                ).delete()
        super().partial_update(
            force_save=True,
            value=value,
            clear_value=clear_value,
            user_id=raw_value if self.instance.type == FieldType.USER else None
        )
        if self.instance.type == FieldType.FILE:
            self._link_new_attachments(raw_value)
        elif self.instance.type in FieldType.TYPES_WITH_SELECTIONS:
            self._update_selections(raw_value)
        return self.instance
