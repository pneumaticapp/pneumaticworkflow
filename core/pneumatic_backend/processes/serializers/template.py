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
            'template_owners',
            'name',
            'is_active',
            'wf_name_template',
        )

    template_owners = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
    )
