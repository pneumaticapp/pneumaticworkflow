from typing import List, Optional

from django.db import DataError, transaction
from django.db.models import Prefetch
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet

from src.accounts.permissions import (
    AccountOwnerPermission,
    BillingPlanPermission,
    ExpiredSubscriptionPermission,
    UserIsAdminOrAccountOwner,
    UsersOverlimitedPermission,
)
from src.analysis.services import AnalyticService
from src.authentication.enums import AuthTokenType
from src.executor import RawSqlExecutor
from src.generics.filters import PneumaticFilterBackend
from src.generics.mixins.views import (
    CustomViewSetMixin,
)
from src.generics.permissions import UserIsAuthenticated
from src.processes.filters import TemplateFilter
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.preset import TemplatePreset
from src.processes.models.templates.system_template import SystemTemplate
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.models.templates.owner import TemplateOwner
from src.processes.permissions import (
    TemplateAccessPermission,
    TemplateAdminOwnerPermission,
    TemplateFieldsPermission,
)
from src.processes.queries import (
    TemplateStepsQuery,
    TemplateTitlesByWorkflowsQuery,
    TemplateTitlesByEventsQuery,
    TemplateTitlesByTasksQuery,
)
from src.processes.serializers.templates.integrations import (
    TemplateIntegrationsFilterSerializer,
)
from src.processes.serializers.templates.preset import (
    TemplatePresetSerializer,
)
from src.processes.serializers.templates.task import (
    TemplateStepFilterSerializer,
    TemplateStepNameSerializer,
)
from src.processes.serializers.templates.template import (
    TemplateAiSerializer,
    TemplateByNameSerializer,
    TemplateByStepsSerializer,
    TemplateExportFilterSerializer,
    TemplateListFilterSerializer,
    TemplateListSerializer,
    TemplateOnlyFieldsSerializer,
    TemplateSerializer,
    TemplateTitlesByEventsSerializer,
    TemplateTitlesByTasksSerializer,
    TemplateTitlesByWorkflowsSerializer,
    TemplateTitlesSerializer,
)
from src.processes.serializers.workflows.workflow import (
    WorkflowCreateSerializer,
    WorkflowDetailsSerializer,
)
from src.processes.services.clone import (
    CloneService,
)
from src.processes.services.exceptions import (
    OpenAiServiceException,
    TemplatePresetServiceException,
    TemplateServiceException,
    WorkflowServiceException,
)
from src.generics.exceptions import BaseServiceException
from src.processes.serializers.templates.fieldset import (
    FieldsetTemplateSerializer,
)
from src.processes.models.templates.fieldset import FieldsetTemplate
from src.processes.services.templates.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.services.templates.ai import (
    OpenAiService,
)
from src.processes.services.templates.preset import TemplatePresetService
from src.processes.services.templates.template import (
    TemplateService,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.services.workflows.workflow import (
    TemplateIntegrationsService,
    WorkflowService,
)
from src.processes.tasks.update_workflow import (
    update_workflows,
)
from src.processes.throttling import AiTemplateGenThrottle
from src.processes.utils.common import get_user_agent
from src.services.permissions import AIPermission
from src.utils.logging import (
    SentryLogLevel,
    capture_sentry_message,
)
from src.utils.validation import raise_validation_error


class TemplateViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    pagination_class = LimitOffsetPagination
    filter_backends = (PneumaticFilterBackend,)
    filterset_class = TemplateFilter
    serializer_class = TemplateSerializer
    action_serializer_classes = {
        'list': TemplateListSerializer,
        'titles_by_owners': TemplateListSerializer,
        'run': WorkflowCreateSerializer,
        'steps': TemplateStepNameSerializer,
        'ai': TemplateAiSerializer,
        'by_steps': TemplateByStepsSerializer,
        'by_name': TemplateByNameSerializer,
        'titles_by_workflows': TemplateTitlesSerializer,
        'titles_by_events': TemplateTitlesSerializer,
        'titles_by_tasks': TemplateTitlesSerializer,
        'fields': TemplateOnlyFieldsSerializer,
        'presets': TemplatePresetSerializer,
        'preset': TemplatePresetSerializer,
        'list_fieldsets': FieldsetTemplateSerializer,
        'create_fieldset': FieldsetTemplateSerializer,
    }

    def get_permissions(self):
        if self.action in (
            'update',
            'clone',
            'destroy',
            'discard_changes',
            'preset',
            'create_fieldset',
        ):
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
                UserIsAdminOrAccountOwner(),
                TemplateAdminOwnerPermission(),
            )
        if self.action == 'presets':
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
                TemplateAccessPermission(),
            )
        if self.action in ('retrieve', 'list_fieldsets'):
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
                UserIsAdminOrAccountOwner(),
                TemplateAdminOwnerPermission(),
            )
        if self.action == 'run':
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
                TemplateAccessPermission(),
            )
        if self.action in (
            'list',
            'titles',
            'titles_by_events',
            'titles_by_owners',
            'titles_by_workflows',
            'titles_by_tasks',
            'steps',
        ):
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
            )
        if self.action == 'fields':
            return (
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                TemplateFieldsPermission(),
            )
        if self.action == 'ai':
            return (
                AIPermission(),
                UserIsAuthenticated(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
                UsersOverlimitedPermission(),
                UserIsAdminOrAccountOwner(),
            )
        if self.action == 'export':
            return (
                AccountOwnerPermission(),
                ExpiredSubscriptionPermission(),
                BillingPlanPermission(),
            )
        return (
            UserIsAuthenticated(),
            ExpiredSubscriptionPermission(),
            BillingPlanPermission(),
            UsersOverlimitedPermission(),
            UserIsAdminOrAccountOwner(),
        )

    @property
    def throttle_classes(self):
        if self.action == 'ai':
            return (AiTemplateGenThrottle,)
        return ()

    def get_queryset(self):
        user = self.request.user
        qst = Template.objects.on_account(user.account_id).exclude_onboarding()
        return self.prefetch_queryset(qst)

    def prefetch_queryset(
        self,
        queryset,
        extra_fields: Optional[List[str]] = None,
    ):

        # Original method "prefetch_queryset"
        # does not working with custom defined Prefetch(...) fields

        if self.action in ('retrieve', 'update'):
            owners_qs = TemplateOwner.objects.filter(
                is_deleted=False,
            ).order_by('role', 'type', 'id')
            queryset = queryset.prefetch_related(
                'kickoff',
                'kickoff__fields',
                'kickoff__fields__selections',
                'kickoff__fieldsets',
                Prefetch('owners', queryset=owners_qs),
                Prefetch(
                    lookup='tasks',
                    queryset=(
                        TaskTemplate.objects
                        .select_related('raw_due_date')
                        .prefetch_related(
                            'fields',
                            'fields__selections',
                            'fieldsets',
                            'checklists',
                            'checklists__selections',
                            'conditions',
                            'conditions__rules',
                            'conditions__rules__predicates',
                            'raw_performers',
                        )
                    ),
                ),
            )
        elif self.action == 'fields':
            queryset = queryset.prefetch_related(
                Prefetch(
                    lookup='kickoff',
                    queryset=(
                        Kickoff.objects.all()
                        .prefetch_related(
                            Prefetch(
                                lookup='fields',
                                queryset=(
                                    FieldTemplate.objects.all()
                                    .order_by('-order')
                                ),
                            ),
                            'fieldsets',
                        )
                    ),
                ),
                Prefetch(
                    lookup='tasks',
                    queryset=(
                        TaskTemplate.objects.all()
                        .order_by('template_id', 'number')
                        .prefetch_related(
                            Prefetch(
                                lookup='fields',
                                queryset=(
                                    FieldTemplate.objects.all()
                                    .order_by('-order')
                                ),
                            ),
                            'fieldsets',
                        )
                    ),
                ),
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
                user=request.user,
            )
            service.api_request(
                template=template,
                user_agent=get_user_agent(request),
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
            **serializer.get_analysis_counters(),
        )
        if self.request.token_type == AuthTokenType.API:
            service = TemplateIntegrationsService(
                account=request.user.account,
                is_superuser=request.is_superuser,
                user=request.user,
            )
            service.api_request(
                template=template,
                user_agent=get_user_agent(request),
            )
        return self.response_ok(serializer.get_response_data())

    def update(self, request, *args, **kwargs):
        template = self.get_object()
        serializer = self.get_serializer(
            instance=template,
            data=request.data,
        )
        with transaction.atomic():
            if request.data.get('is_active'):
                serializer.is_valid(raise_exception=True)
                template = serializer.save()
            else:
                template = serializer.save_as_draft()
        template = self.get_queryset().get(pk=template.pk)
        service = TemplateIntegrationsService(
            account=request.user.account,
            is_superuser=request.is_superuser,
            user=request.user,
        )
        service.template_updated(template=template)
        if self.request.token_type == AuthTokenType.API:
            service.api_request(
                template=template,
                user_agent=get_user_agent(request),
            )
        if template.is_active:
            update_workflows.delay(
                template_id=template.id,
                version=template.version,
                updated_by=request.user.id,
                auth_type=request.token_type,
                is_superuser=request.is_superuser,
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
                **serializer.get_analysis_counters(),
            )
        response_serializer = self.get_serializer(instance=template)
        return self.response_ok(response_serializer.get_response_data())

    @action(methods=['POST'], detail=True)
    def clone(self, request, *args, **kwargs):
        template = self.get_object()
        template_data_clone = CloneService.get_template_draft_clone(
            template.get_draft(),
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

        data = filter_slz.validated_data
        search_text = data.get('search')
        user = request.user
        queryset = Template.objects.raw_list_query(
            user_id=user.id,
            account_id=user.account_id,
            ordering=data.get('ordering'),
            search=search_text,
            is_active=data.get('is_active'),
            is_public=data.get('is_public'),
        )
        if search_text:
            AnalyticService.search_search(
                user=request.user,
                page='templates',
                search_text=search_text,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
        return self.paginated_response(queryset)

    @action(methods=['GET'], detail=False, url_path='titles-by-owners')
    def titles_by_owners(self, request, *args, **kwargs):
        """
        Returns templates where the current user is a Template Owner
        (directly or via group membership).
        """
        filter_slz = TemplateListFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)

        data = filter_slz.validated_data
        search_text = data.get('search')
        user = request.user
        queryset = Template.objects.raw_list_by_owners_query(
            user_id=user.id,
            account_id=user.account_id,
            ordering=data.get('ordering'),
            search=search_text,
            is_active=data.get('is_active'),
            is_public=data.get('is_public'),
        )
        if search_text:
            AnalyticService.search_search(
                user=request.user,
                page='templates',
                search_text=search_text,
                is_superuser=request.is_superuser,
                auth_type=request.token_type,
            )
        return self.paginated_response(queryset)

    @action(methods=['POST'], detail=True)
    def run(self, request, *args, **kwargs):

        template = self.get_object()
        request_slz = self.get_serializer(
            data=request.data,
            extra_fields={'template': template},
        )
        request_slz.is_valid(raise_exception=True)
        data = request_slz.validated_data
        service = WorkflowService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            workflow = service.create(
                instance_template=template,
                kickoff_fields_data=data['kickoff'],
                workflow_starter=self.request.user,
                user_provided_name=data.get('name'),
                is_external=False,
                is_urgent=data['is_urgent'],
                due_date=data.get('due_date_tsp'),
                ancestor_task=data.get('ancestor_task_id'),
                user_agent=get_user_agent(request),
            )
        except WorkflowServiceException as ex:
            raise_validation_error(ex.message)

        workflow_action_service = WorkflowActionService(
            workflow=workflow,
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        workflow_action_service.start_workflow()
        slz = WorkflowDetailsSerializer(instance=workflow)
        return self.response_ok(slz.data)

    def destroy(self, request, *args, **kwargs):

        template = self.get_object()
        with transaction.atomic():
            template.workflows.update(
                is_legacy_template=True,
                legacy_template_name=template.name,
            )
            template.delete()
        AnalyticService.templates_deleted(
            user=request.user,
            template=template,
            auth_type=request.token_type,
            is_superuser=request.is_superuser,
        )
        return self.response_ok()

    @action(methods=['GET'], detail=False, url_path='titles-by-workflows')
    def titles_by_workflows(self, request, *args, **kwargs):
        request_slz = TemplateTitlesByWorkflowsSerializer(data=request.GET)
        request_slz.is_valid(raise_exception=True)
        query = TemplateTitlesByWorkflowsQuery(
            user=request.user,
            **request_slz.validated_data,
        )
        data = RawSqlExecutor.fetch(*query.get_sql())
        response_slz = self.get_serializer(data, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['GET'], detail=False, url_path='titles-by-events')
    def titles_by_events(self, request, *args, **kwargs):
        request_slz = TemplateTitlesByEventsSerializer(data=request.GET)
        request_slz.is_valid(raise_exception=True)
        query = TemplateTitlesByEventsQuery(
            user=request.user,
            **request_slz.validated_data,
        )
        data = RawSqlExecutor.fetch(*query.get_sql())
        response_slz = self.get_serializer(data, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['GET'], detail=False, url_path='titles-by-tasks')
    def titles_by_tasks(self, request, *args, **kwargs):
        request_slz = TemplateTitlesByTasksSerializer(data=request.GET)
        request_slz.is_valid(raise_exception=True)
        query = TemplateTitlesByTasksQuery(
            user=request.user,
            **request_slz.validated_data,
        )
        data = RawSqlExecutor.fetch(*query.get_sql())
        response_slz = self.get_serializer(data, many=True)
        return self.response_ok(response_slz.data)

    @action(methods=['GET'], detail=True, url_path='steps')
    def steps(self, request, pk, *args, **kwargs):

        """ Returns all tasks of specified template if user in template owners.

            Params:
                - with_tasks_in_progress: bool - filter tasks by running
                workflows where the user is performer
                (not necessarily template owner). """

        filter_slz = TemplateStepFilterSerializer(data=request.GET)
        filter_slz.is_valid(raise_exception=True)
        self.queryset = TaskTemplate.objects.execute_raw(
            TemplateStepsQuery(
                user=request.user,
                template_id=pk,
                **filter_slz.validated_data,
            ),
        )
        serializer = self.get_serializer(self.queryset, many=True)
        try:
            data = serializer.data
        except DataError as ex:
            raise Http404 from ex
        return self.response_ok(data)

    @action(methods=['GET'], detail=True, url_path='fields')
    def fields(self, *args, **kwargs):
        template = self.get_object()
        slz = self.get_serializer(instance=template)
        return self.response_ok(slz.data)

    @action(methods=['GET'], detail=True)
    def integrations(self, request, pk, *args, **kwargs):
        template = self.get_object()
        service = TemplateIntegrationsService(
            account=request.user.account,
            is_superuser=request.is_superuser,
            user=request.user,
        )
        data = service.get_template_integrations_data(
            template_id=template.id,
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
            auth_type=request.token_type,
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
            auth_type=request.token_type,
        )
        try:
            template = service.create_template_by_steps(
                **request_slz.validated_data,
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
                name=slz.validated_data['name'],
            )
        except SystemTemplate.DoesNotExist as ex:
            capture_sentry_message(
                message='Library template not found during registration',
                level=SentryLogLevel.ERROR,
                data={
                    'name': slz.validated_data['name'],
                    'user_id': self.request.user.id,
                    'account_id': self.request.user.account_id,
                },
            )
            raise Http404 from ex
        service = TemplateService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            template = service.create_template_from_library_template(
                system_template=system_template,
            )
        except TemplateServiceException as ex:
            raise_validation_error(message=ex.message)
        else:
            slz = TemplateSerializer(instance=template)
            return self.response_ok(slz.get_response_data())

    @action(methods=['POST'], detail=True, url_path='discard-changes')
    def discard_changes(self, request, pk, *args, **kwargs):
        template = self.get_object()
        if template.tasks.all().count() != 0:
            slz = self.get_serializer(instance=template)
            slz.discard_changes()
            return self.response_ok()
        template.delete()
        return self.response_ok()

    @action(methods=['GET'], detail=False, url_path='export')
    def export(self, request, *args, **kwargs):
        user = request.user
        filter_slz = TemplateExportFilterSerializer(
            data=request.query_params,
            context={'account_id': user.account.id},
        )
        filter_slz.is_valid(raise_exception=True)
        queryset = Template.objects.raw_export_query(
            user_id=user.id,
            account_id=user.account_id,
            **filter_slz.validated_data,
        )
        return self.paginated_response(queryset)

    @action(methods=['GET'], detail=True, url_path='presets')
    def presets(self, request, *args, **kwargs):
        template = self.get_object()
        user_presets = (
            TemplatePreset.objects
            .by_user(request.user, template.id)
            .select_related('author', 'template')
            .prefetch_related('fields')
        )
        serializer = self.get_serializer(user_presets, many=True)
        return self.response_ok(serializer.data)

    @action(methods=['POST'], detail=True, url_path='preset')
    def preset(self, request, *args, **kwargs):
        template = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = TemplatePresetService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )

        try:
            preset = service.create(
                template=template,
                **serializer.validated_data,
            )
        except TemplatePresetServiceException as ex:
            raise_validation_error(message=ex.message)

        return self.response_ok(self.get_serializer(preset).data)

    @action(methods=['GET'], detail=True, url_path='fieldsets')
    def list_fieldsets(self, request, *args, **kwargs):
        template = self.get_object()
        queryset = FieldsetTemplate.objects.on_account(
            request.user.account_id,
        ).filter(template_id=template.id)
        return self.paginated_response(queryset)

    @list_fieldsets.mapping.post
    def create_fieldset(self, request, *args, **kwargs):
        template = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = FieldSetTemplateService(
            user=request.user,
            is_superuser=request.is_superuser,
            auth_type=request.token_type,
        )
        try:
            fieldset = service.create(
                template_id=template.id,
                **serializer.validated_data,
            )
        except BaseServiceException as ex:
            raise_validation_error(message=ex.message)
        response_serializer = FieldsetTemplateSerializer(fieldset)
        return self.response_created(response_serializer.data)


class TemplateIntegrationsViewSet(
    CustomViewSetMixin,
    GenericViewSet,
):
    permission_classes = (
        UserIsAuthenticated,
        UserIsAdminOrAccountOwner,
        ExpiredSubscriptionPermission,
        BillingPlanPermission,
        UsersOverlimitedPermission,
    )

    def get_queryset(self):
        return Template.objects.on_account(
            self.request.user.account_id,
        ).exclude_onboarding()

    def list(self, request, *args, **kwargs):
        slz = TemplateIntegrationsFilterSerializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        service = TemplateIntegrationsService(
            account=request.user.account,
            is_superuser=request.is_superuser,
            user=request.user,
        )
        data = service.get_integrations(
            **slz.validated_data,
        )
        return self.response_ok(data=data)
