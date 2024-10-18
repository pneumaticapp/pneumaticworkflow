from django.conf import settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from pneumatic_backend.processes.models import (
    Template
)
from pneumatic_backend.processes.api_v2.serializers.template.\
    public.template import (
        PublicTemplateSerializer,
    )
from pneumatic_backend.processes.api_v2.serializers.workflow.\
    external.workflow import (
        ExternalWorkflowCreateSerializer,
        SecuredExternalWorkflowCreateSerializer,
    )
from pneumatic_backend.processes.permissions import PublicTemplatePermission
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
    AnonymousWorkflowMixin
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.utils.common import get_user_agent
from pneumatic_backend.processes.api_v2.services import (
    WorkflowService,
)
from pneumatic_backend.processes.api_v2.services.exceptions import (
    WorkflowServiceException,
)
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)


class PublicTemplateViewSet(
    CustomViewSetMixin,
    AnonymousWorkflowMixin,
    GenericViewSet,
):
    permission_classes = (PublicTemplatePermission,)
    queryset = Template.objects.all()
    action_serializer_classes = {
        'retrieve': PublicTemplateSerializer,
    }

    def get_object(self):
        obj = self.request.public_template
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        template = self.get_object()
        if not settings.PROJECT_CONF['CAPTCHA']:
            show_captcha = False
        else:
            workflow_exists = self.anonymous_user_workflow_exists(
                request=request,
                template=template,
            )
            show_captcha = workflow_exists in {True, None}
        serializer = self.get_serializer(instance=template)
        response_data = serializer.data
        response_data['show_captcha'] = show_captcha
        return self.response_ok(response_data)

    @action(methods=['post'], detail=False)
    def run(self, request, *args, **kwargs):
        template = self.get_object()
        account = template.account
        user = account.get_owner()
        workflow_exists = self.anonymous_user_workflow_exists(
            request=request,
            template=template,
        )
        captcha_required = workflow_exists in {True, None}
        if settings.PROJECT_CONF['CAPTCHA'] and captcha_required:
            serializer_cls = SecuredExternalWorkflowCreateSerializer
        else:
            request.data.pop('captcha', None)
            serializer_cls = ExternalWorkflowCreateSerializer
        serializer = serializer_cls(
            data=request.data,
            context={'request': request}  # for ReCaptchaV2Field
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        service = WorkflowService(
            user=user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        anonymous_id = self.request.data.get(
            'anonymous_id', self.get_user_ip(request)
        )
        try:
            workflow = service.create(
                instance_template=template,
                kickoff_fields_data=data['fields'],
                is_external=True,
                user_agent=get_user_agent(request),
                anonymous_id=anonymous_id
            )
        except WorkflowServiceException as ex:
            raise_validation_error(ex.message)

        workflow_action_service = WorkflowActionService(
            user=user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        workflow_action_service.start_workflow(workflow)

        self.inc_anonymous_user_workflow_counter(request, template)
        if request.token_type == AuthTokenType.PUBLIC:
            redirect_url = None
            if account.is_subscribed and template.public_success_url:
                redirect_url = template.public_success_url
            return self.response_ok(data={'redirect_url': redirect_url})
        else:
            return self.response_ok()
