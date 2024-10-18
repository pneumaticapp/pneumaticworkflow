from django.db import transaction
from django.http import Http404
from django.conf import settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from pneumatic_backend.accounts.permissions import (
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
    ExpiredSubscriptionPermission,
)
from pneumatic_backend.executor import RawSqlExecutor
from pneumatic_backend.services.permissions import AIPermission
from pneumatic_backend.accounts.services import AccountService
from pneumatic_backend.generics.filters import PneumaticFilterBackend
from pneumatic_backend.processes.api_v2.serializers.template. \
    integrations import TemplateIntegrationsFilterSerializer
from pneumatic_backend.processes.api_v2.serializers.template.task import (
    TemplateStepFilterSerializer,
    TemplateStepNameSerializer,
)
from pneumatic_backend.processes.models import (
    Template,
    TaskTemplate,
    SystemTemplate,
)
from pneumatic_backend.processes.api_v2.serializers.template.template import (
    TemplateSerializer,
    TemplateListFilterSerializer,
    TemplateOnlyFieldsSerializer,
    TemplateListSerializer,
    TemplateTitlesRequestSerializer,
    TemplateTitlesEventsRequestSerializer,
    TemplateAiSerializer,
    TemplateByStepsSerializer,
    TemplateByNameSerializer,
)
from pneumatic_backend.processes.serializers.template import (
    TemplateTitlesSerializer
)
from pneumatic_backend.processes.serializers.workflow import (
    WorkflowCreateSerializer,
    WorkflowDetailsSerializer,
)
from pneumatic_backend.processes.filters import (
    TemplateFilter,
)
from pneumatic_backend.processes.api_v2.services.templates.template import (
    TemplateService
)
from pneumatic_backend.processes.api_v2.services.clone import (
    CloneService
)
from pneumatic_backend.processes.tasks.update_workflow import (
    update_workflows,
)
from pneumatic_backend.generics.mixins.views import (
    CustomViewSetMixin,
)
from pneumatic_backend.processes.queries import (
    TemplateStepsQuery,
    TemplateTitlesEventsQuery,
    TemplateTitlesQuery,
)
from pneumatic_backend.processes.permissions import (
    TemplateOwnerPermission,
)
from pneumatic_backend.analytics.services import AnalyticService
from pneumatic_backend.processes.api_v2.services import (
    WorkflowService,
    TemplateIntegrationsService,
)
from pneumatic_backend.generics.permissions import (
    UserIsAuthenticated,
    PaymentCardPermission,
)
from pneumatic_backend.processes.api_v2.services.templates.ai import (
    OpenAiService
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.utils.common import get_user_agent
from pneumatic_backend.processes.api_v2.services.exceptions import (
    OpenAiServiceException,
    TemplateServiceException,
    WorkflowServiceException,
)
from pneumatic_backend.utils.validation import raise_validation_error
from pneumatic_backend.processes.throttling import AiTemplateGenThrottle
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)


class TemplateViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    pagination_class = LimitOffsetPagination
    filter_backends = (PneumaticFilterBackend,)
    filterset_class = TemplateFilter
    serializer_class = TemplateSerializer
    action_serializer_classes = {
        'list': TemplateListSerializer,
        'run': WorkflowCreateSerializer,
        'steps': TemplateStepNameSerializer,
        'ai': TemplateAiSerializer,
        'by_steps': TemplateByStepsSerializer,
        'by_name': TemplateByNameSerializer,
        'titles': TemplateTitlesSerializer,
        'titles_by_events': TemplateTitlesSerializer,
    }

    def get_permissions(self):
        if self.action in (
            'retrieve',
            'update',
            'clone',
            'destroy',
            'discard_changes',
        ):
            return (
                UserIsAuthenticated(),
                PaymentCardPermission(),
                UsersOverlimitedPermission(),
                UserIsAdminOrAccountOwner(),
                TemplateOwnerPermission(),
                ExpiredSubscriptionPermission(),
            )
        elif self.action == 'run':
            return (
                UserIsAuthenticated(),
                PaymentCardPermission(),
                UsersOverlimitedPermission(),
                TemplateOwnerPermission(),
                ExpiredSubscriptionPermission(),
            )
        elif self.action in (
            'list',
            'fields',
            'titles',
            'titles_by_events',
            'steps',
        ):
            return (
                UserIsAuthenticated(),
                PaymentCardPermission(),
                ExpiredSubscriptionPermission()
            )
        elif self.action == 'ai':
            return (
                AIPermission(),
                UserIsAuthenticated(),
                PaymentCardPermission(),
                UsersOverlimitedPermission(),
                UserIsAdminOrAccountOwner(),
                ExpiredSubscriptionPermission(),
            )
        else:
            return (
                UserIsAuthenticated(),
                PaymentCardPermission(),
                UsersOverlimitedPermission(),
                UserIsAdminOrAccountOwner(),
                ExpiredSubscriptionPermission(),
            )

    @property
    def throttle_classes(self):
        if self.action == 'ai':
            return (AiTemplateGenThrottle,)
        else:
            return ()

    def get_queryset(self):
        user = self.request.user
        qst = Template.objects.on_account(user.account_id).exclude_onboarding()
        if self.action == 'steps':
            if not self.request.user.is_account_owner:
                qst = qst.with_template_owners(user.id)
        elif self.action in {'list', 'fields'}:
            qst = qst.with_template_owners(user.id)
        return qst

    def prefetch_queryset(self, queryset, **kwargs):
        if self.action == 'run':
            queryset = queryset.prefetch_related(
                'tasks__delay',
                'tasks__due_date'
                'tasks__raw_performers',
                'tasks__conditions__rules__predicates',
                'tasks__checklists',
                'tasks__fields__selections'
                'kickoff__fields__selections'
            )
        return queryset

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user'] = self.request.user
        context['account'] = self.request.user.account
        context['is_superuser'] = self.request.is_superuser
        context['auth_type'] = self.request.token_type
        return context

    def retrieve(self, request, *args, **kwargs):
        template = self.get_object()
        serializer = self.get_serializer(instance=template)
        if self.request.token_type == AuthTokenType.API:
            service = TemplateIntegrationsService(
                account=request.user.account,
                is_superuser=request.is_superuser,
                user=request.user
            )
            service.api_request(
                template=template,
                user_agent=get_user_agent(request)
            )
        return self.response_ok(serializer.get_response_data())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        with transaction.atomic():
            if request.data.get('is_active'):
                serializer.is_valid(raise_exception=True)
                template = serializer.save()
            else:
                template = serializer.save_as_draft()
        AnalyticService.templates_kickoff_created(
            user=request.user,
            template=template,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        AnalyticService.templates_created(
            user=request.user,
            template=template,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
            **serializer.get_analytics_counters(),
        )
        if self.request.token_type == AuthTokenType.API:
            service = TemplateIntegrationsService(
                account=request.user.account,
                is_superuser=request.is_superuser,
                user=request.user
            )
            service.api_request(
                template=template,
                user_agent=get_user_agent(request)
            )
        return self.response_ok(serializer.get_response_data())

    def update(self, request, *args, **kwargs):
        template = self.get_object()
        serializer = self.get_serializer(
            instance=template,
            data=request.data
        )
        with transaction.atomic():
            if request.data.get('is_active'):
                serializer.is_valid(raise_exception=True)
                template = serializer.save()
            else:
                template = serializer.save_as_draft()
        service = TemplateIntegrationsService(
            account=request.user.account,
            is_superuser=request.is_superuser,
            user=request.user
        )
        service.template_updated(template=template)
        if self.request.token_type == AuthTokenType.API:
            service.api_request(
                template=template,
                user_agent=get_user_agent(request)
            )
        if template.is_active:
            update_workflows.delay(
                template_id=template.id,
                version=template.version,
                updated_by=request.user.id,
                auth_type=request.token_type,
                is_superuser=request.is_superuser
            )
            AnalyticService.templates_kickoff_updated(
                user=request.user,
                template=template,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
            AnalyticService.templates_updated(
                user=request.user,
                template=template,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
                **serializer.get_analytics_counters(),
            )
        return self.response_ok(serializer.get_response_data())

    @action(methods=['POST'], detail=True)
    def clone(self, request, *args, **kwargs):
        template = self.get_object()
        template_data_clone = CloneService.get_template_draft_clone(
            template.get_draft()
        )
        serializer = self.get_serializer(data=template_data_clone)
        with transaction.atomic():
            serializer.save_as_draft()
        return self.response_ok(serializer.get_response_data())

    def list(self, request, *args, **kwargs):

        """ Explanation for pagination:
            A paginated_response call is needed for return response data
            in pagination format (count, result...), but
            pagination occurs at the Python level (not SQL)

            SQL pagination (by LIMIT, OFFSET) is not possible because
            it is impossible to calculate response 'count' value """

        filter_slz = TemplateListFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        service = TemplateService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        data = filter_slz.validated_data
        search_text = data.get('search')
        templates_data = service.get_templates_data(
            ordering=data.get('ordering'),
            search=search_text,
            is_active=data.get('is_active'),
            is_public=data.get('is_public'),
            is_template_owner=(data.get('is_template_owner'))
        )
        if search_text:
            AnalyticService.search_search(
                user_id=request.user.id,
                page='templates',
                search_text=search_text,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
        return self.paginated_response(templates_data)

    @action(methods=['POST'], detail=True)
    def run(self, request, *args, **kwargs):

        template = self.get_object()
        request_slz = self.get_serializer(
            data=request.data,
            extra_fields={'template': template}
        )
        request_slz.is_valid(raise_exception=True)
        data = request_slz.validated_data
        service = WorkflowService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        try:
            workflow = service.create(
                instance_template=template,
                kickoff_fields_data=data['kickoff'],
                workflow_starter=self.request.user,
                user_provided_name=data.get('name'),
                is_external=False,
                is_urgent=data['is_urgent'],
                due_date=data['due_date'],
                ancestor_task=data.get('ancestor_task_id'),
                user_agent=get_user_agent(request)
            )
        except WorkflowServiceException as ex:
            raise_validation_error(ex.message)

        workflow_action_service = WorkflowActionService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        workflow_action_service.start_workflow(workflow)

        # TODO Deprecated
        first_task = workflow.current_task_instance
        slz = WorkflowDetailsSerializer(instance=workflow)
        response_data = slz.data
        response_data['workflow_id'] = workflow.id
        response_data['first_task_performers'] = list(
            first_task.performers.exclude_directly_deleted().values_list(
                'id', flat=True
            )
        )
        return self.response_ok(response_data)

    def destroy(self, request, *args, **kwargs):

        template = self.get_object()
        with transaction.atomic():
            template.workflows.update(
                is_legacy_template=True,
                legacy_template_name=template.name,
            )
            template.delete()
            account_service = AccountService(
                instance=request.user.account,
                user=request.user
            )
            account_service.update_active_templates()
        AnalyticService.templates_deleted(
            user=request.user,
            template=template,
            auth_type=request.token_type,
            is_superuser=request.is_superuser
        )
        if self.request.token_type == AuthTokenType.API:
            service = TemplateIntegrationsService(
                account=request.user.account,
                is_superuser=request.is_superuser,
                user=request.user
            )
            service.api_request(
                template=template,
                user_agent=get_user_agent(request)
            )
        return self.response_ok()

    @action(methods=['GET'], detail=False, url_path='titles')
    def titles(self, request, *args, **kwargs):
        request_slz = TemplateTitlesRequestSerializer(data=request.GET)
        request_slz.is_valid(raise_exception=True)
        query = TemplateTitlesQuery(
            user=request.user,
            **request_slz.validated_data
        )
        data = RawSqlExecutor.fetch(
            *query.get_sql(),
            db=settings.REPLICA
        )
        response_slz = self.get_serializer(data, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['GET'], detail=False, url_path='titles-by-events')
    def titles_by_events(self, request, *args, **kwargs):
        request_slz = TemplateTitlesEventsRequestSerializer(data=request.GET)
        request_slz.is_valid(raise_exception=True)
        query = TemplateTitlesEventsQuery(
            user=request.user,
            **request_slz.validated_data
        )
        data = RawSqlExecutor.fetch(
            *query.get_sql(),
            db=settings.REPLICA
        )
        response_slz = self.get_serializer(data, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['GET'], detail=True, url_path='steps')
    def steps(self, request, pk, *args, **kwargs):

        """ Returns all tasks of specified template if user in template owners.

            Params:
                - with_tasks_in_progress: bool - filter tasks by running
                workflows where the user is performer
                (not necessarily template owner).
                - is_running_workflows: bool - filter tasks where there are
                running workflows are on this task """

        filter_slz = TemplateStepFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        data = filter_slz.validated_data
        self.queryset = TaskTemplate.objects.execute_raw(
            TemplateStepsQuery(
                user=request.user,
                template_id=pk,
                with_tasks_in_progress=data.get('with_tasks_in_progress'),
                is_running_workflows=data.get('is_running_workflows'),
            )
        )
        serializer = self.get_serializer(self.queryset, many=True)
        return self.response_ok(serializer.data)

    @action(methods=['GET'], detail=True, url_path='fields')
    def fields(self, *args, **kwargs):
        template = self.get_object()
        serializer = TemplateOnlyFieldsSerializer(instance=template)
        return self.response_ok(serializer.data)

    @action(methods=['GET'], detail=True)
    def integrations(self, request, pk, *args, **kwargs):
        template = self.get_object()
        service = TemplateIntegrationsService(
            account=request.user.account,
            is_superuser=request.is_superuser,
            user=request.user
        )
        data = service.get_template_integrations_data(
            template_id=template.id
        )
        return self.response_ok(data=data)

    @action(methods=['POST'], detail=False)
    def ai(self, request, *args, **kwargs):
        request_slz = self.get_serializer(data=request.data)
        request_slz.is_valid(raise_exception=True)
        description = request_slz.validated_data['description']
        service = OpenAiService(
            ident=request.user.id,
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        try:
            data = service.get_template_data(user_description=description)
        except OpenAiServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok(data)

    @action(methods=['POST'], detail=False, url_path='by-steps')
    def by_steps(self, request, *args, **kwargs):
        request_slz = self.get_serializer(data=request.data)
        request_slz.is_valid(raise_exception=True)
        service = TemplateService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        try:
            template = service.create_template_by_steps(
                **request_slz.validated_data
            )
        except TemplateServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            slz = TemplateSerializer(instance=template)
            return self.response_ok(slz.get_response_data())

    @action(methods=['POST'], detail=False, url_path='by-name')
    def by_name(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)
        try:
            system_template = SystemTemplate.objects.library().active().get(
                name=slz.validated_data['name']
            )
        except SystemTemplate.DoesNotExist:
            capture_sentry_message(
                message='Library template not found during registration',
                level=SentryLogLevel.ERROR,
                data={
                    'name': slz.validated_data['name'],
                    'user_id': self.request.user.id,
                    'account_id': self.request.user.account_id,
                }
            )
            raise Http404
        service = TemplateService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type
        )
        try:
            template = service.create_template_from_library_template(
                system_template=system_template
            )
        except TemplateServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            slz = TemplateSerializer(instance=template)
            return self.response_ok(slz.get_response_data())

    @action(methods=['POST'], detail=True, url_path='discard-changes')
    def discard_changes(self, request, pk, *args, **kwargs):
        template = self.get_object()
        if template.tasks_count != 0:
            slz = self.get_serializer(instance=template)
            slz.discard_changes()
            return self.response_ok()
        template.delete()
        return self.response_ok()


class TemplateIntegrationsViewSet(
    CustomViewSetMixin,
    GenericViewSet
):
    permission_classes = (
        UserIsAuthenticated,
        UserIsAdminOrAccountOwner,
        PaymentCardPermission,
        ExpiredSubscriptionPermission,
        UsersOverlimitedPermission,
    )

    def get_queryset(self):
        return Template.objects.on_account(
            self.request.user.account_id
        ).exclude_onboarding()

    def list(self, request, *args, **kwargs):
        slz = TemplateIntegrationsFilterSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        service = TemplateIntegrationsService(
            account=request.user.account,
            is_superuser=request.is_superuser,
            user=request.user
        )
        data = service.get_integrations(
            **slz.validated_data
        )
        return self.response_ok(data=data)
