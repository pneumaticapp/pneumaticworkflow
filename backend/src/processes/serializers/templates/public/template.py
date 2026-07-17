from typing import Any, Dict

from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    CharField,
    ModelSerializer,
    SerializerMethodField,
)

from src.processes.models.templates.template import Template
from src.processes.serializers.templates.public.kickoff import (
    PublicKickoffSerializer,
)

UserModel = get_user_model()


class PublicTemplateSerializer(ModelSerializer):

    class Meta:
        model = Template
        fields = (
            'name',
            'description',
            'kickoff',
        )

    description = CharField(allow_blank=True, default='')
    kickoff = SerializerMethodField()

    def get_kickoff(self, instance: Template):
        # PublicTemplateSerializer cannot return a single Kickoff
        # object because the Template related with Kickoff by
        # foreign key instead of one to one relation.
        # Getting the object manually:
        kickoff_slz = PublicKickoffSerializer(
            instance=instance.kickoff_instance,
        )
        return kickoff_slz.data

    def to_representation(self, data: Dict[str, Any]):

        data = super().to_representation(data)
        if data.get('description') is None:
            data['description'] = ''
        return data
