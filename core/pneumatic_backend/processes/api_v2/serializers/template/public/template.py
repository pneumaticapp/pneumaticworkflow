from typing import Dict, Any
from rest_framework.serializers import (
    ModelSerializer,
    CharField
)
from django.contrib.auth import get_user_model
from pneumatic_backend.processes.models import (
    Template,
)
from pneumatic_backend.processes.api_v2.serializers.template\
    .public.kickoff import (
        PublicKickoffSerializer
    )

UserModel = get_user_model()


class PublicTemplateSerializer(ModelSerializer):

    class Meta:
        model = Template
        fields = (
            'name',
            'description',
            'kickoff'
        )

    description = CharField(allow_blank=True, default='')
    kickoff = PublicKickoffSerializer(required=False)

    def to_representation(self, data: Dict[str, Any]):

        data = super().to_representation(data)
        if data.get('description') is None:
            data['description'] = ''

        # PublicTemplateSerializer cannot return a single Kickoff object
        # because the Template related with Kickoff by foreign key
        # instead of one to one relation. Getting the object manually:
        kickoff_slz = PublicKickoffSerializer(
            instance=self.instance.kickoff_instance
        )
        data['kickoff'] = kickoff_slz.data
        return data
