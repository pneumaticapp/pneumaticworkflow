import contextlib
from typing import Any, Dict, List, Optional, Set

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.serializers import Serializer

from src.processes.messages.template import MSG_PT_0041
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.services.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.utils.validation import raise_validation_error

UserModel = get_user_model()


class CreateOrUpdateInstanceMixin:

    def _get_create_or_update_fields(self) -> Set[str]:
        value = getattr(self.Meta, 'create_or_update_fields', None)
        if value is None:
            raise Exception(
                f'You should set a Meta.create_or_update_fields value for'
                f' the {self.__class__!s}',
            )
        if not isinstance(value, set):
            raise Exception(
                '"create_or_update_fields" must be of type "Set".',
            )
        if 'id' in value:
            raise Exception(
                '"create_or_update_fields" contains "id" field. '
                'It should be removed from the list.',
            )
        return value

    def _get_create_or_update_data(
        self,
        validated_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        data = {}
        create_or_update_fields = self._get_create_or_update_fields()
        for field_name in create_or_update_fields:
            with contextlib.suppress(KeyError):
                data[field_name] = validated_data[field_name]
        return data

    def _update(
        self,
        instance,
        validated_data: Dict[str, Any],
    ):

        data = self._get_create_or_update_data(validated_data)
        for field_name, field_value in data.items():
            setattr(instance, field_name, field_value)
        with transaction.atomic():
            instance.save()

    def _create(
        self,
        validated_data: Dict[str, Any],
    ):
        data = self._get_create_or_update_data(validated_data)
        with transaction.atomic():
            return self.Meta.model.objects.create(**data)

    def create_or_update_instance(
        self,
        validated_data: Dict[str, Any],
        instance: Optional = None,
        not_unique_exception_msg: Optional[str] = None,
    ) -> Any:

        try:
            if instance:
                self._update(
                    instance=instance,
                    validated_data=validated_data,
                )
            else:
                instance = self._create(
                    validated_data=validated_data,
                )
        except IntegrityError as ex:
            if not_unique_exception_msg:
                raise_validation_error(
                    api_name=validated_data.get('api_name'),
                    message=not_unique_exception_msg,
                )
            raise ex
        return instance


class CreateOrUpdateRelatedMixin:

    def _get_api_primary_field(self, slz_cls) -> str:
        api_primary_field = getattr(slz_cls.Meta, 'api_primary_field', None)
        if api_primary_field is None:
            raise Exception(
                f'You should set a Meta.api_primary_field value for'
                f' the {slz_cls!s}',
            )
        return api_primary_field

    def _get_related_serializer(
        self,
        slz_cls,
        data,
        ancestors_data,
        slz_context=None,
    ) -> Serializer:

        """ This method checks existing of object either by id or api_name.
            If objects exists then returns serializer
            for update else for create. """

        slz_context = {} if slz_context is None else slz_context
        model_cls = slz_cls.Meta.model
        slz = None
        api_primary_field = self._get_api_primary_field(slz_cls)
        primary_value = data.get(api_primary_field)
        if primary_value:
            obj_filter = ancestors_data.copy()
            obj_filter[api_primary_field] = primary_value
            instance = model_cls.objects.filter(**obj_filter).first()
            if instance:
                slz = slz_cls(instance, data=data, context=slz_context)
        if slz is None:
            data.pop('id', None)
            for field_name, value in ancestors_data.items():
                data[field_name] = value
            slz = slz_cls(data=data, context=slz_context)
        return slz

    def _get_related_one_serializer(
        self,
        slz_cls,
        data,
        ancestors_data,
        slz_context=None,
    ):
        """ This method checks existing of one related object.
            If objects exists then returns serializer
            for update else for create. """

        slz_context = {} if slz_context is None else slz_context
        model_cls = slz_cls.Meta.model
        instance = model_cls.objects.filter(**ancestors_data).first()
        if instance:
            slz = slz_cls(instance, data=data, context=slz_context)
        else:
            data.pop('id', None)
            for field_name, value in ancestors_data.items():
                data[field_name] = value
            slz = slz_cls(data=data, context=slz_context)
        return slz

    def create_or_update_related_one(
        self,
        slz_cls,
        ancestors_data: Dict[str, Any],
        slz_context: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ):

        """ Create or update one to one related record
            and delete prev record
            If not the data - then all prev records are deleted """

        existent_ids = set()
        if data:
            slz = self._get_related_one_serializer(
                slz_cls=slz_cls,
                slz_context=slz_context,
                data=data,
                ancestors_data=ancestors_data,
            )
            slz.is_valid(raise_exception=True)
            obj = slz.save()
            existent_ids.add(obj.id)
        model_cls = slz_cls.Meta.model
        model_cls.objects.filter(**ancestors_data).exclude(
            id__in=existent_ids,
        ).delete()

    def create_or_update_related(
        self,
        slz_cls,
        ancestors_data: Dict[str, Any],
        slz_context: Optional[Dict[str, Any]] = None,
        data: Optional[List[Dict[str, Any]]] = None,
    ):

        """ Create or update foreign key related records
            in right order and delete prev record
            If not the data - then all prev records are deleted """

        model_cls = slz_cls.Meta.model
        if data:
            existent_ids = set()
            api_primary_field = self._get_api_primary_field(slz_cls)
            for elem in data:
                primary_value = elem.get(api_primary_field)
                if primary_value:
                    existent_ids.add(primary_value)
            model_cls.objects.filter(**ancestors_data).exclude(
                **{f'{api_primary_field}__in': existent_ids},
            ).delete()
        else:
            model_cls.objects.filter(**ancestors_data).delete()

        if data:
            for el in data:
                slz = self._get_related_serializer(
                    slz_cls=slz_cls,
                    slz_context=slz_context,
                    data=el,
                    ancestors_data=ancestors_data,
                )
                slz.is_valid(raise_exception=True)
                slz.save()


class CustomValidationApiNameMixin:

    def additional_validate_api_name(
        self,
        value: Any,
        **kwargs,
    ):
        if (
            self.instance
            and (
                not value
                or self.instance.api_name != value
            )
        ):
            raise_validation_error(
                message=MSG_PT_0041(
                    old_api_name=self.instance.api_name,
                    new_api_name=value,
                ),
            )


class FieldsetMixin:

    @staticmethod
    def create_or_update_fieldsets(
        fieldsets_data: List[Dict],
        template: Template,
        user: UserModel,
        task: Optional[TaskTemplate] = None,
        kickoff: Optional[Kickoff] = None,
    ):
        instance = task or kickoff
        existing_fieldsets = {f.api_name: f for f in instance.fieldsets.all()}
        fieldsets_api_names = set()
        for fieldset_data in fieldsets_data:
            fieldset_api_name = fieldset_data.get('api_name')
            if fieldset_api_name and fieldset_api_name in existing_fieldsets:
                fieldset = existing_fieldsets[fieldset_api_name]
                update_kwargs = {}
                if fieldset.order != fieldset_data['order']:
                    update_kwargs['order'] = fieldset_data['order']
                if fieldset.title != fieldset_data['title']:
                    update_kwargs['title'] = fieldset_data['title']
                if fieldset.description != fieldset_data['description']:
                    update_kwargs['description'] = fieldset_data['description']

                if update_kwargs:
                    service = FieldSetTemplateService(
                        instance=fieldset,
                        user=user,
                    )
                    service.partial_update_instance(
                        order=fieldset_data['order'],
                        title=fieldset_data.get('title'),
                        description=fieldset_data.get('description'),
                    )
                fieldsets_api_names.add(fieldset.api_name)
            else:
                shared_fieldset = fieldset_data['shared_fieldset_id']
                service = FieldSetTemplateService(user=user)
                fieldset = service.create_from_shared(
                    shared_fieldset_data=FieldSetTemplateService.to_json(
                        shared_fieldset,
                    ),
                    shared_fieldset_id=shared_fieldset.id,
                    template_id=template.id,
                    task_id=task.id if task else None,
                    kickoff_id=kickoff.id if kickoff else None,
                    order=fieldset_data['order'],
                    api_name=fieldset_data.get('api_name'),
                    title=fieldset_data.get('title'),
                    description=fieldset_data.get('description'),
                )
                fieldsets_api_names.add(fieldset.api_name)
        instance.fieldsets.exclude(api_name__in=fieldsets_api_names).delete()

    def get_draft_fieldsets(self, fieldsets_data: Any):
        result = []
        if isinstance(fieldsets_data, list):
            for fieldset_data in fieldsets_data:
                if fieldset_data.get('fields'):
                    result.append(fieldset_data)
                    # Fieldset already done
                    continue
                try:
                    shared_fieldset_id = int(fieldset_data.get(
                        'shared_fieldset_id',
                    ))
                    shared_fieldset = FieldsetTemplate.objects.get(
                        id=shared_fieldset_id,
                        is_shared=True,
                    )
                except (TypeError, ValueError, ObjectDoesNotExist):
                    # Remove invalid or not existent fieldset
                    continue
                order = fieldset_data.get('order', 0)
                service = FieldSetTemplateService()
                new_fieldset_data = service.get_new_fieldset_data(
                    shared_fieldset_data=FieldSetTemplateService.to_json(
                        shared_fieldset,
                    ),
                    api_name=fieldset_data.get('api_name'),
                    title=fieldset_data.get('title'),
                    description=fieldset_data.get('description'),
                )
                new_fieldset_data['order'] = order
                new_fieldset_data['shared_fieldset_id'] = shared_fieldset_id
                result.append(new_fieldset_data)
        return result
