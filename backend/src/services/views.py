from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.processes.serializers.templates.template import (
    TemplateAiSerializer,
)
from src.services.throttling import StepsByDescriptionThrottle
from src.processes.services.templates.ai import (
    AnonOpenAiService,
)
from src.processes.services.exceptions import (
    OpenAiServiceException,
)
from src.utils.validation import raise_validation_error
from src.generics.mixins.views import AnonymousMixin
from src.services.permissions import AIPermission


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
            user_agent=self.get_user_agent(request),
        )
        try:
            data = service.get_short_template_data(
                user_description=description,
            )
        except OpenAiServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok(data)
