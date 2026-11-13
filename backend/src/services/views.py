from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet

from src.generics.mixins.views import (
    AnonymousMixin,
    CustomViewSetMixin,
)
from src.openapi.parameters import AI_DESCRIPTION_PARAMS
from src.openapi.responses import (
    FORBIDDEN,
    TOO_MANY_REQUESTS,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)
from src.openapi.template_services_serializers import (
    GeneratedTemplateStepsSerializer,
)
from src.processes.serializers.templates.template import (
    TemplateAiSerializer,
)
from src.processes.services.exceptions import (
    OpenAiServiceException,
)
from src.processes.services.templates.ai import (
    AnonOpenAiService,
)
from src.services.permissions import AIPermission
from src.services.throttling import StepsByDescriptionThrottle
from src.utils.validation import raise_validation_error


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
        return ()

    @extend_schema(
        tags=['Services'],
        summary='Generate steps from description (AI)',
        description=(
            'No user session is required. The AI feature must be enabled '
            'for this deployment. description supplies the workflow goal; '
            'the response contains a suggested template name and task '
            'steps. Generation is throttled using the configured rate '
            'for this anonymous endpoint.'
        ),
        auth=[],
        parameters=AI_DESCRIPTION_PARAMS,
        responses={
            200: GeneratedTemplateStepsSerializer,
            400: VALIDATION_ERROR,
            401: UNAUTHORIZED,
            403: FORBIDDEN,
            429: TOO_MANY_REQUESTS,
        },
    )
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
