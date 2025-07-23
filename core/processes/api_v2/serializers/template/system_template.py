import re
from rest_framework import serializers
from pneumatic_backend.processes.entities import LibraryTemplateData
from pneumatic_backend.processes.enums import (
    DueDateRule,
    FieldType,
)
from pneumatic_backend.processes.models import (
    SystemTemplate,
    SystemTemplateCategory,
    TaskTemplate,
)
from pneumatic_backend.generics.serializers import CustomValidationErrorMixin
from pneumatic_backend.processes.utils.common import create_api_name


class SystemTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SystemTemplate
        fields = (
            'id',
            'name',
            'description',
            'category',
        )


class SystemTemplateCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SystemTemplateCategory
        fields = (
            'id',
            'order',
            'name',
            'icon',
            'color',
            'template_color',
        )


class DueInSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    days = serializers.IntegerField(min_value=0)
    hours = serializers.IntegerField(min_value=0)
    minutes = serializers.IntegerField(min_value=0)


class StepSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    step_name = serializers.CharField(max_length=280)
    step_description = serializers.CharField()
    due_in = DueInSerializer(required=False, allow_null=False)


class LibraryTemplateImportSerializer(
    CustomValidationErrorMixin,
    serializers.Serializer
):

    title = serializers.CharField(max_length=64)
    intro = serializers.CharField()
    category = serializers.CharField(max_length=64)
    steps = StepSerializer(
        required=True,
        allow_null=False,
        allow_empty=False,
        many=True
    )
    kickoff = serializers.DictField(
        required=False,
        allow_empty=True,
        allow_null=False,
        child=serializers.ChoiceField(
            choices=(
                ('text', 'text'),
                ('largeText', 'largeText'),
                ('user', 'user'),
                ('date', 'date'),
            )
        )
    )

    def validate(self, attrs) -> LibraryTemplateData:

        """ Returns valid template structure
            Crutch for resolve camelCase fields names """

        kickoff_fields = attrs.get('kickoff')
        if not kickoff_fields:
            attrs['kickoff'] = {}
        else:
            types_map = {
                'text': FieldType.STRING,
                'largeText': FieldType.TEXT,
                'date': FieldType.DATE,
                'user': FieldType.USER
            }
            attrs['kickoff'] = {'fields': []}
            # Normalize camelCase field names
            for order, (field, value) in enumerate(
                kickoff_fields.items(), start=1
            ):
                name = re.sub(r'(?<!^)(?=[A-Z])', ' ', field)
                name = re.sub(r'\s\s+', ' ', name).lower().capitalize()
                field_type = types_map[value]
                attrs['kickoff']['fields'].append({
                    "order": order,
                    "name": name,
                    "type": field_type,
                    "is_required": field_type == FieldType.USER
                })

        tasks = []
        for number, step in enumerate(attrs['steps'], start=1):
            task_api_name = create_api_name(
                prefix=TaskTemplate.api_name_prefix
            )
            task_data = {
                'number': number,
                'name': step['step_name'],
                'description': step['step_description'],
                'api_name': task_api_name
            }
            due_in = step.get('due_in')
            if due_in:
                days = str(int(due_in['days'])).zfill(2)
                hours = str(int(due_in['hours'])).zfill(2)
                minutes = str(int(due_in['minutes'])).zfill(2)
                task_data['raw_due_date'] = {
                    'rule':  DueDateRule.AFTER_TASK_STARTED,
                    'duration_months': 0,
                    'duration': f'{days} {hours}:{minutes}:00',
                    'source_id': task_api_name
                }
            tasks.append(task_data)

        attrs['tasks'] = tasks
        attrs['name'] = attrs['title']
        del attrs['title']
        attrs['description'] = attrs['intro']
        del attrs['intro']
        del attrs['steps']
        return attrs
