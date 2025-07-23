from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.processes.api_v2.serializers.template.template import (
    TemplateAiSerializer
)
from pneumatic_backend.services.throttling import StepsByDescriptionThrottle
from pneumatic_backend.processes.api_v2.services.templates.ai import (
    AnonOpenAiService
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    OpenAiServiceException
)
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.generics.mixins.views import AnonymousMixin
from pneumatic_backend.services.permissions import AIPermission


class ServicesViewSet(
    AnonymousMixin,
    CustomViewSetMixin,
    GenericViewSet,
):

    permission_classes = (
        AIPermission,
    )
    action_serializer_classes = {
        'steps_by_description': TemplateAiSerializer,
    }

    @property
    def throttle_classes(self):
        if self.action == 'steps_by_description':
            return (StepsByDescriptionThrottle,)
        else:
            return ()

    @action(methods=['GET'], detail=False, url_path='steps-by-description')
    def steps_by_description(self, request, *args, **kwargs):

        request_slz = self.get_serializer(data=request.GET)
        request_slz.is_valid(raise_exception=True)
        description = request_slz.validated_data['description']
        service = AnonOpenAiService(
            ident=self.get_user_ip(request),
            user_agent=self.get_user_agent(request)
        )
        try:
            data = service.get_short_template_data(
                user_description=description
            )
        except OpenAiServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok(data)
