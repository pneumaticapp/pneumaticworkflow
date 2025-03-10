from rest_framework import serializers
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import Template

UserModel = get_user_model()


class TemplateTitlesSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    workflows_count = serializers.IntegerField(read_only=True)


class TemplateDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Template
        fields = (
            'id',
            # TODO remove in https://my.pneumatic.app/workflows/34402
            'template_owners',
            'name',
            'is_active',
            'wf_name_template',
        )

    template_owners = serializers.SerializerMethodField()

    def get_template_owners(self, instance: Template):

        # TODO remove in https://my.pneumatic.app/workflows/34402

        return list(
            instance.owners
            .order_by('id')
            .values_list('user_id', flat=True)
        )


class WorkflowTemplateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Template
        fields = (
            'id',
            'name',
            'is_active',
            # TODO remove in https://my.pneumatic.app/workflows/34402
            'template_owners',
        )

    template_owners = serializers.SerializerMethodField()

    def get_template_owners(self, instance: Template):

        # TODO remove in https://my.pneumatic.app/workflows/34402
        if hasattr(instance, 'tmp_owners'):
            return list(el.user_id for el in instance.tmp_owners)
        else:
            return list(
                instance.owners
                .order_by('id')
                .values_list('user_id', flat=True)
            )
