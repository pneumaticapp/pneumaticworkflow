from typing import Dict, Any, List, Optional, Set
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.serializers import Serializer
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.processes.messages.template import MSG_PT_0041

UserModel = get_user_model()


class CreateOrUpdateInstanceMixin:

    def _get_create_or_update_fields(self) -> Set[str]:
        value = getattr(self.Meta, 'create_or_update_fields', None)
        if value is None:
            raise Exception(
                f'You should set a Meta.create_or_update_fields value for'
                f' the {str(self.__class__)}'
            )
        if not isinstance(value, set):
            raise Exception(
                '"create_or_update_fields" must be of type "Set".'
            )
        if 'id' in value:
            raise Exception(
                '"create_or_update_fields" contains "id" field. '
                'It should be removed from the list.'
            )
        return value

    def _get_create_or_update_data(
        self,
        validated_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        data = {}
        create_or_update_fields = self._get_create_or_update_fields()
        for field_name in create_or_update_fields:
            try:
                data[field_name] = validated_data[field_name]
            except KeyError:
                pass
        return data

    def _update(
        self,
        instance,
        validated_data: Dict[str, Any]
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
            instance = self.Meta.model.objects.create(**data)
        return instance

    def create_or_update_instance(
        self,
        validated_data: Dict[str, Any],
        instance: Optional = None,
        not_unique_exception_msg: Optional[str] = None
    ) -> Any:

        try:
            if instance:
                self._update(
                    instance=instance,
                    validated_data=validated_data
                )
            else:
                instance = self._create(
                    validated_data=validated_data
                )
        except IntegrityError as ex:
            if not_unique_exception_msg:
                raise_validation_error(
                    api_name=validated_data.get('api_name'),
                    message=not_unique_exception_msg
                )
            raise ex
        return instance


class CreateOrUpdateRelatedMixin:

    def _get_api_primary_field(self, slz_cls) -> str:
        api_primary_field = getattr(slz_cls.Meta, 'api_primary_field', None)
        if api_primary_field is None:
            raise Exception(
                f'You should set a Meta.api_primary_field value for'
                f' the {str(slz_cls)}'
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
        slz_context=None
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
                ancestors_data=ancestors_data
            )
            slz.is_valid(raise_exception=True)
            obj = slz.save()
            existent_ids.add(obj.id)
        model_cls = slz_cls.Meta.model
        model_cls.objects.filter(**ancestors_data).exclude(
            id__in=existent_ids
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
                **{f'{api_primary_field}__in': existent_ids}
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
        if self.instance:
            if not value or self.instance.api_name != value:
                raise_validation_error(
                    message=MSG_PT_0041(
                        old_api_name=self.instance.api_name,
                        new_api_name=value
                    )
                )
