# pylint: disable=broad-except,
from typing import List, Dict, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.api_v2.services import WorkflowService
from pneumatic_backend.processes.api_v2.services.exceptions import (
    WorkflowServiceException
)
from pneumatic_backend.processes.models import (
    Template,
    SystemTemplate,
)
from pneumatic_backend.processes.enums import (
    FieldType,
)
from pneumatic_backend.processes.utils.common import (
    insert_fields_values_to_text
)
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel
)
from pneumatic_backend.processes.api_v2.services import TemplateService
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)


UserModel = get_user_model()


class SystemWorkflowService:

    def __init__(
        self,
        user: UserModel = None,
        is_superuser: bool = False,
        auth_type: AuthTokenType = AuthTokenType.USER,
        sync: bool = False
    ):
        self.user = user
        self.account = user.account if user else None
        self.is_superuser = is_superuser
        self.auth_type = auth_type
        self.sync = sync
        self.template_service = TemplateService(
            user=user,
            is_superuser=is_superuser,
            auth_type=auth_type
        )

    def _get_onboarding_templates_for_user(self) -> List[Template]:
        qst = self.account.template_set.active()
        if self.user.is_account_owner:
            qst = qst.onboarding_owner()
        elif self.user.is_admin:
            qst = qst.onboarding_admin()
        else:
            qst = qst.onboarding_not_admin()
        return qst

    def _get_system_workflow_kickoff_data(
        self,
        system_template: SystemTemplate
    ) -> QuerySet:

        qst = system_template.system_workflow_kickoff_data.active()
        if self.user.is_account_owner:
            qst = qst.onboarding_owner()
        elif self.user.is_admin:
            qst = qst.onboarding_admin()
        else:
            qst = qst.onboarding_not_admin()
        return qst.only_data()

    def _resolve_exception(self, ex: Exception, **kwargs):
        if settings.CONFIGURATION_CURRENT in {
            settings.CONFIGURATION_PROD,
            settings.CONFIGURATION_STAGING,
        }:
            capture_sentry_message(
                message=(
                    f'Onboarding from '
                    f'"One-of-task" cannot start (account {self.account.id})'
                ),
                data={
                    'account_id': self.account.id,
                    'account_name': self.account.name,
                    'user_id': self.user.id,
                    'user_email': self.user.email,
                    'exception': str(ex),
                    **kwargs
                },
                level=SentryLogLevel.INFO
            )
        else:
            raise ex

    def get_kickoff_fields_values(
        self,
        template: Template,
        fields_data: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:

        if fields_data is None:
            fields_data = {}
        user_vars = self.user.get_dynamic_mapping()
        result = {}

        for field in template.kickoff_instance.fields.all():
            if field.type == FieldType.USER:
                result[field.api_name] = str(self.user.id)
            elif fields_data.get(field.api_name):
                result[field.api_name] = fields_data[field.api_name]
            elif field.default is not None:
                result[field.api_name] = insert_fields_values_to_text(
                    text=field.default,
                    fields_values=user_vars
                )
        return result

    def create_library_templates(self):

        for system_template in self.account.system_templates.library(
        ).active():
            try:
                self.template_service.create_template_from_sys_template(
                    system_template=system_template
                )
            except Exception as ex:
                self._resolve_exception(ex)

    def create_onboarding_templates(self):

        for system_template in (
            SystemTemplate.objects.onboarding().active()
        ):
            try:
                self.template_service.create_template_from_sys_template(
                    system_template=system_template
                )
            except Exception as ex:
                self._resolve_exception(ex)

    def create_onboarding_workflows(self):
        service = WorkflowService(
            user=self.user,
            is_superuser=self.is_superuser,
            auth_type=self.auth_type
        )
        for template in self._get_onboarding_templates_for_user():
            kickoff_fields_data = self.get_kickoff_fields_values(template)
            try:
                workflow = service.create(
                    instance_template=template,
                    kickoff_fields_data=kickoff_fields_data,
                    workflow_starter=self.user,
                    redefined_performer=self.user,
                )
            except WorkflowServiceException as ex:
                self._resolve_exception(ex)
            else:
                workflow_action_service = WorkflowActionService(
                    user=self.user,
                    is_superuser=self.is_superuser,
                    auth_type=self.auth_type
                )
                workflow_action_service.start_workflow(workflow)

    def create_activated_templates(self):

        for system_template in SystemTemplate.objects.activated().active():
            try:
                self.template_service.create_template_from_sys_template(
                    system_template=system_template,
                )
            except Exception as ex:
                self._resolve_exception(ex)

    def create_activated_workflows(self):

        for system_template in SystemTemplate.objects.activated().active():
            system_kickoffs = self._get_system_workflow_kickoff_data(
                system_template
            )
            if system_kickoffs.exists():
                try:
                    template = self.account.template_set.get(
                        system_template_id=system_template.id
                    )
                except ObjectDoesNotExist as ex:
                    self._resolve_exception(
                        ex=ex,
                        system_template_id=system_template.id,
                        system_template_name=system_template.name,
                    )
                else:
                    service = WorkflowService(
                        user=self.user,
                        is_superuser=self.is_superuser,
                        auth_type=self.auth_type
                    )
                    for kickoff_data in system_kickoffs:
                        kickoff_fields_data = self.get_kickoff_fields_values(
                            template=template,
                            fields_data=kickoff_data.get('kickoff', {})
                        )
                        try:
                            workflow = service.create(
                                instance_template=template,
                                user_provided_name=kickoff_data.get('name'),
                                kickoff_fields_data=kickoff_fields_data,
                                workflow_starter=self.user,
                                is_urgent=kickoff_data.get('is_urgent'),
                            )
                        except WorkflowServiceException as ex:
                            self._resolve_exception(
                                ex=ex,
                                system_template_id=system_template.id,
                                system_template_name=system_template.name,
                            )
                            break
                        else:
                            workflow_action_service = WorkflowActionService(
                                user=self.user,
                                is_superuser=self.is_superuser,
                                auth_type=self.auth_type

                            )
                            workflow_action_service.start_workflow(workflow)
