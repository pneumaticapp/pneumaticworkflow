# ruff: noqa: PLC0415
from copy import deepcopy
from typing import Dict, List, Optional
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from src.generics.base.service import BaseModelService
from src.processes.enums import LabelPosition, FieldSetLayout
from src.processes.messages.fieldset import (
    MSG_FS_0014,
    MSG_FS_0015,
    MSG_FS_0016,
)
from src.processes.models.templates.fields import (
    FieldTemplate,
    FieldTemplateSelection,
)
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldSetTemplateRuleSet,
    FieldSetTemplateRuleGroupOr,
    FieldSetTemplateRuleGroupAnd,
)
from src.processes.services.exceptions import (
    FieldsetTemplateInUseException,
    FieldsetTemplateInUseException2,
    FieldsetTemplateSharedIdMissing,
    FieldsetTemplateTemplateIdMissing,
)
from src.processes.services.fieldsets.fieldset_rule import \
    FieldsetTemplateRuleSetService
from src.processes.services.templates.field_template import (
    FieldTemplateService,
)
from src.processes.utils.common import create_api_name
from src.utils.validation import raise_validation_error


UserModel = get_user_model()


class FieldSetTemplateService(BaseModelService):

    def _create_instance(
        self,
        name: str,
        is_shared: bool,
        template_id: Optional[int] = None,
        order: int = 0,
        title: str = '',
        description: str = '',
        kickoff_id: Optional[int] = None,
        task_id: Optional[int] = None,
        shared_fieldset_id: Optional[int] = None,
        api_name: Optional[str] = None,
        label_position: LabelPosition.LITERALS = LabelPosition.TOP,
        layout: FieldSetLayout.LITERALS = FieldSetLayout.VERTICAL,
        **kwargs,
    ):

        if not is_shared:
            if not template_id:
                raise FieldsetTemplateTemplateIdMissing
            if not shared_fieldset_id:
                raise FieldsetTemplateSharedIdMissing

        create_kwargs = {
            'template_id': template_id,
            'account': self.account,
            'order': order,
            'name': name,
            'title': title or name,
            'description': description,
            'label_position': label_position,
            'layout': layout,
            'kickoff_id': kickoff_id,
            'task_id': task_id,
            'shared_fieldset_id': shared_fieldset_id,
            'is_shared': is_shared,
        }
        if api_name:
            create_kwargs['api_name'] = api_name
        self.instance = FieldsetTemplate.objects.create(**create_kwargs)
        return self.instance

    def create_shared_fieldset(
        self,
        name: str,
        title: str = '',
        description: str = '',
        api_name: Optional[str] = None,
        label_position: LabelPosition.LITERALS = LabelPosition.TOP,
        layout: FieldSetLayout.LITERALS = FieldSetLayout.VERTICAL,
        **kwargs,
    ):

        """ Creates a shared FieldSetTemplate
            that is not linked to a template. """

        return super().create(
            name=name,
            title=title,
            description=description,
            api_name=api_name,
            label_position=label_position,
            layout=layout,
            is_shared=True,
            **kwargs,
        )

    def create_from_shared(
        self,
        shared_fieldset_data: dict,
        shared_fieldset_id: int,
        template_id: int,
        order: int = 0,
        kickoff_id: Optional[int] = None,
        task_id: Optional[int] = None,
        api_name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> FieldsetTemplate:

        fieldset_data = self.get_new_fieldset_data(
            shared_fieldset_data=shared_fieldset_data,
            api_name=api_name,
            title=title,
            description=description,
        )

        return self.create(
            **fieldset_data,
            is_shared=False,
            shared_fieldset_id=shared_fieldset_id,
            order=order,
            kickoff_id=kickoff_id,
            task_id=task_id,
            template_id=template_id,
        )

    def _create_related(
        self,
        rulesets: Optional[List[Dict]] = None,
        fields: Optional[List[Dict]] = None,
        **kwargs,
    ):
        if fields:
            self._create_fields(fields_data=fields)
        if rulesets:
            self.create_rulesets(rulesets_data=rulesets)

    def _get_step_name(self) -> str:
        if self.instance.kickoff_id:
            return 'Kickoff'
        if self.instance.task_id:
            return self.instance.task.name
        return 'Kickoff'

    def _create_fields(
        self,
        fields_data: List[Dict],
    ):
        for field_data in fields_data:
            field_data_dict = dict(field_data)
            # Field-level rulesets are not created here yet.
            field_data_dict.pop('rulesets', None)
            field_data_dict.pop('id', None)
            service = FieldTemplateService(
                user=self.user,
                is_superuser=self.is_superuser,
                auth_type=self.auth_type,
                account=self.account,
            )
            try:
                service.create(
                    fieldset_id=self.instance.id,
                    template_id=self.instance.template_id,
                    **field_data_dict,
                )
            except IntegrityError as ex:
                ex_str = str(ex)
                step_name = self._get_step_name()
                if (
                    'processes_fieldtemplate_template_api_name_unique'
                    in ex_str
                ):
                    api_name = field_data_dict.get('api_name')
                    raise_validation_error(
                        api_name=api_name,
                        message=MSG_FS_0015(
                            name=step_name,
                            field_name=field_data_dict.get('name'),
                            api_name=api_name,
                        ),
                    )
                if (
                    'processes_fieldtemplateselection'
                    '_template_api_name_unique'
                    in ex_str
                ):
                    selections = field_data_dict.get('selections') or []
                    api_names = [s.get('api_name') for s in selections]
                    api_name = next(
                        (
                            name for name in api_names
                            if api_names.count(name) > 1
                        ),
                        api_names[-1] if api_names else None,
                    )
                    raise_validation_error(
                        api_name=api_name,
                        message=MSG_FS_0016(
                            name=step_name,
                            api_name=api_name,
                        ),
                    )
                raise

    def _update_fields(
        self,
        fields_data: List[Dict],
    ):
        """ All fieldset fields will be updated """

        existing_fields = {
            field.api_name: field
            for field in self.instance.fields.all()
        }
        fields_api_names = set()
        for field_data in fields_data:
            field_api_name = field_data.get('api_name')
            if field_api_name and field_api_name in existing_fields:
                service = FieldTemplateService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=existing_fields[field_api_name],
                )
                service.partial_update(force_save=True, **field_data)
                fields_api_names.add(field_api_name)
            else:
                service = FieldTemplateService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                )
                field = service.create(
                    fieldset_id=self.instance.id,
                    template_id=self.instance.template_id,
                    **field_data,
                )
                fields_api_names.add(field.api_name)

        self.instance.fields.exclude(api_name__in=fields_api_names).delete()

    def partial_update(
        self,
        **update_kwargs,
    ) -> FieldsetTemplate:

        if self.instance.is_shared and self.instance.child_fieldsets.exists():
            raise FieldsetTemplateInUseException2

        rulesets_data = update_kwargs.pop('rulesets', None)
        fields_data = update_kwargs.pop('fields', None)
        with transaction.atomic():
            if update_kwargs:
                self.instance = super().partial_update(
                    force_save=True,
                    **update_kwargs,
                )

            if fields_data is not None:
                self._update_fields(fields_data=fields_data)
            if rulesets_data is not None:
                self.update_rulesets(rulesets_data=rulesets_data)
            return self.instance

    def partial_update_instance(
        self,
        **update_kwargs,
    ) -> FieldsetTemplate:

        with transaction.atomic():
            if update_kwargs:
                self.instance = super().partial_update(
                    force_save=True,
                    **update_kwargs,
                )
            return self.instance

    def delete(self) -> None:
        if self.instance.is_shared and self.instance.child_fieldsets.exists():
            raise FieldsetTemplateInUseException
        if self.instance.kickoff_id or self.instance.task_id:
            raise FieldsetTemplateInUseException
        self.instance.delete()

    @staticmethod
    def _replace_api_names(shared_fieldset_data: dict) -> dict:

        fieldset_data = deepcopy(shared_fieldset_data)
        fieldset_data['api_name'] = create_api_name(
            FieldsetTemplate.api_name_prefix,
        )
        fields_map: Dict[str, str] = {}
        updated_fields_data = []
        for field_data in fieldset_data.get('fields', []):
            new_api_name = create_api_name(
                FieldTemplate.api_name_prefix,
            )
            fields_map[field_data['api_name']] = new_api_name
            field_data['api_name'] = new_api_name
            for selection_data in field_data.get('selections', []):
                selection_data['api_name'] = create_api_name(
                    FieldTemplateSelection.api_name_prefix,
                )
            updated_fields_data.append(field_data)
        fieldset_data['fields'] = updated_fields_data

        updated_rules_data = []
        for ruleset_data in fieldset_data.get('rulesets', []):
            ruleset_data['api_name'] = create_api_name(
                FieldSetTemplateRuleSet.api_name_prefix,
            )
            for group_or_data in ruleset_data.get('groups_or', []):
                group_or_data['api_name'] = create_api_name(
                    FieldSetTemplateRuleGroupOr.api_name_prefix,
                )
                for group_and_data in group_or_data.get('groups_and', []):
                    group_and_data['api_name'] = create_api_name(
                        FieldSetTemplateRuleGroupAnd.api_name_prefix,
                    )
            ruleset_data['fields'] = [
                fields_map[old_api_name]
                for old_api_name in ruleset_data.get('fields', [])
            ]
            updated_rules_data.append(ruleset_data)
        fieldset_data['rulesets'] = updated_rules_data
        return fieldset_data

    def get_new_fieldset_data(
        self,
        shared_fieldset_data: dict,
        api_name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:

        fieldset_data = self._replace_api_names(shared_fieldset_data)
        if api_name:
            fieldset_data['api_name'] = api_name
        if title is not None:
            fieldset_data['title'] = title
        if description is not None:
            fieldset_data['description'] = description
        fieldset_data.pop('order', None)
        fieldset_data.pop('id', None)
        return fieldset_data

    def create_ruleset(
        self,
        ruleset_data: dict,
    ) -> FieldSetTemplateRuleSet:

        service = FieldsetTemplateRuleSetService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type,
        )
        try:
            return service.create(
                fieldset_id=self.instance.id,
                template_id=self.instance.template_id,
                **ruleset_data,
            )
        except IntegrityError as ex:
            if 'fieldsetruleset_fieldset_api_name_unique' not in str(ex):
                raise
            api_name = ruleset_data.get('api_name')
            raise_validation_error(
                api_name=api_name,
                message=MSG_FS_0014(
                    name=self._get_step_name(),
                    api_name=api_name,
                ),
            )

    def create_rulesets(
        self,
        rulesets_data: List[Dict],
    ):
        for ruleset_data in rulesets_data:
            self.create_ruleset(ruleset_data)

    def update_rulesets(
        self,
        rulesets_data: List[Dict],
    ):
        """ All rulesets will be updated """

        existing_rulesets = {
            ruleset.api_name: ruleset
            for ruleset in self.instance.rulesets.all()
        }
        ruleset_api_names = set()
        for ruleset_data in rulesets_data:
            ruleset_data_dict = dict(ruleset_data)
            ruleset_api_name = ruleset_data_dict.get('api_name')
            if ruleset_api_name and ruleset_api_name in existing_rulesets:
                service = FieldsetTemplateRuleSetService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type,
                    instance=existing_rulesets[ruleset_api_name],
                )
                service.partial_update(**ruleset_data)
                ruleset_api_names.add(ruleset_api_name)
            else:
                ruleset = self.create_ruleset(ruleset_data)
                ruleset_api_names.add(ruleset.api_name)

        self.instance.rulesets.exclude(
            api_name__in=ruleset_api_names,
        ).delete()

    @staticmethod
    def to_json(fieldset: FieldsetTemplate) -> dict:
        if fieldset.is_shared:
            from src.processes.serializers.templates.fieldset import (
                SharedFieldsetTemplateSerializer,
            )
            slz_cls = SharedFieldsetTemplateSerializer
        else:
            from src.processes.serializers.templates.fieldset import (
                FieldsetTemplateSerializer,
            )
            slz_cls = FieldsetTemplateSerializer
        return dict(slz_cls(fieldset).data)

    def get_clone(self) -> FieldsetTemplate:

        """ Creates a shared FieldSetTemplate clone of self.instance """

        instance_data = self.to_json(self.instance)
        clone_data = self.get_new_fieldset_data(
            shared_fieldset_data=instance_data,
        )
        clone_data['name'] = clone_data['name'] + ' - clone'
        return self.create_shared_fieldset(**clone_data)
