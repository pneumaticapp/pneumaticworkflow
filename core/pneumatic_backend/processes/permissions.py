import re
from django.db.models import Q
from django.conf import settings
from rest_framework.permissions import BasePermission
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0001
)
from pneumatic_backend.processes.messages.template import (
    MSG_PT_0023,
    MSG_PT_0024,
)
from pneumatic_backend.processes.models import (
    Template,
    Workflow,
    Task,
    WorkflowEvent,
    Checklist,
)
from pneumatic_backend.accounts.enums import UserType
from pneumatic_backend.processes.queries import (
    WorkflowCurrentTaskUserPerformerQuery,
    TaskWorkflowMemberQuery,
)
from pneumatic_backend.executor import RawSqlExecutor


class TemplateOwnerPermission(BasePermission):

    """ For template details API """

    message = MSG_PT_0023

    def has_permission(self, request, view):
        return request.user.is_account_owner or Template.objects.filter(
            id=view.kwargs.get('pk'),
            template_owners=request.user,
            account_id=request.user.account_id
        ).exists()


class WorkflowTemplateOwnerPermission(BasePermission):

    """ For workflow details API """

    def has_permission(self, request, view):
        return request.user.is_account_owner or Workflow.objects.filter(
            Q(
                Q(
                    is_legacy_template=True,
                    workflow_starter_id=request.user.id
                ) | Q(
                    template__template_owners=request.user
                )
            ),
            pk=view.kwargs.get('pk'),
            account_id=request.user.account_id,
        ).exists()


class TaskTemplateOwnerPermission(BasePermission):

    """ For tasks details API """

    def has_permission(self, request, view):
        return request.user.is_account_owner or Task.objects.filter(
            Q(
                Q(
                    workflow__is_legacy_template=True,
                    workflow__workflow_starter_id=request.user.id
                ) | Q(
                    workflow__template__template_owners=request.user
                )
            ),
            pk=view.kwargs.get('pk'),
            account_id=request.user.account_id,
        ).exists()


class WorkflowMemberPermission(BasePermission):

    """ Allow for account owner, guests and workflow members
        Use for workflow API only  """

    def has_permission(self, request, view):
        user = request.user
        if user.type == UserType.USER:
            if user.is_account_owner:
                return True
            else:
                workflow_id = view.kwargs.get('pk')
                if workflow_id:
                    return Workflow.members.through.objects.filter(
                        user_id=user.id,
                        workflow_id=workflow_id
                    ).exists()
                else:
                    raise Exception(MSG_PT_0024)
        else:
            return True


class TaskWorkflowMemberPermission(BasePermission):

    """ Use for task detail API only """

    def has_permission(self, request, view):
        if request.user.type == UserType.USER:
            if request.user.is_account_owner:
                return True
            else:
                query = TaskWorkflowMemberQuery(
                    user=request.user,
                    task_id=view.kwargs.get('pk')
                )
                return RawSqlExecutor.exists(*query.get_sql())
        else:
            return True


class UserTaskCompletePermission(BasePermission):

    """ Checks if the authenticated user has permission to complete task.

        If no target task is specified, the current workflow task
        will be checked. Otherwise, checks for requested task

        Checking that the current workflow task is not equal to the
        request task is performed at the validation level!
    """

    def has_permission(self, request, view):
        user = request.user
        if user.type == UserType.USER:
            if user.is_account_owner:
                return True
            else:
                query = WorkflowCurrentTaskUserPerformerQuery(
                    user=user,
                    workflow_id=view.kwargs['pk'],
                    task_id=request.data.get('task_id'),
                )
                result = next(RawSqlExecutor.fetch(*query.get_sql()), None)
                return bool(result)
        else:
            return True


class GuestWorkflowPermission(BasePermission):

    """ Checks that authenticated guest has permission to requested workflow.
        request.task_id exists only for guests """

    workflow_urls_pattern = (
        r'^\/workflows\/(?P<workflow_id>\d+)\/'
        r'(events|comment|task-complete)\/{0,1}$'
    )

    def has_permission(self, request, view):
        if request.user.type == UserType.GUEST:
            match = re.match(self.workflow_urls_pattern, request.path)
            if match is None:
                return False
            workflow_id = int(match.group('workflow_id'))
            return Task.objects.filter(
                id=request.task_id,
                workflow_id=workflow_id
            ).exists()
        else:
            return True


class PublicTemplatePermission(BasePermission):

    def has_permission(self, request, view):
        template = getattr(request, 'public_template', None)
        return bool(template)


class GuestTaskPermission(BasePermission):

    """ Checks that authenticated guest has permission to requested task.
        request.task_id exists only for guests """

    task_urls_pattern = r'^\/v2\/tasks\/(?P<task_id>\d+)\/?$'
    checklists_urls_pattern = (
        r'^\/v2\/tasks\/checklists\/(?P<checklist_id>\d+)'
        r'(\/|(\/(un)?mark\/?))?$'
    )

    def _request_to_task(self, request):

        """ Allow requests to the task endpoints:
            /v2/tasks/<task_id:int> """

        match = re.match(self.task_urls_pattern, request.path)
        if match is None:
            return False
        return int(match.group('task_id')) == request.task_id

    def _request_to_checklist(self, request):

        """ Allow requests to the checklists endpoints:
            /v2/tasks/checklists/<checklist_id:int>
            /v2/tasks/checklists/<checklist_id:int>/mark
            /v2/tasks/checklists/<checklist_id:int>/unmark """

        match = re.match(self.checklists_urls_pattern, request.path)
        if match is None:
            return False
        return Checklist.objects.filter(
            task_id=request.task_id,
            id=int(match.group('checklist_id'))
        ).exists()

    def has_permission(self, request, view):

        """ Allow guests to access only specified endpoints """

        if request.user.type == UserType.GUEST:
            return (
                self._request_to_task(request)
                or self._request_to_checklist(request)
            )
        return True


class GuestTaskCompletePermission(BasePermission):

    """ Checks that authenticated guest has permission to complete task.
        request.task_id exists only for guests """

    def has_permission(self, request, view):
        if request.user.type == UserType.GUEST:
            try:
                task_id = int(request.data.get('task_id'))
            except (TypeError, ValueError):
                return False
            else:
                return task_id == request.task_id
        return True


class CommentEditPermission(BasePermission):

    """ Checks that authenticated guest has permission to requested workflow.
        request.task_id exists only for guests """

    def has_permission(self, request, view):
        try:
            comment_id = int(view.kwargs['pk'])
        except (TypeError, ValueError):
            return False
        qst = WorkflowEvent.objects.filter(
            user_id=request.user.id,
            id=comment_id
        ).type_comment()
        if request.user.type == UserType.GUEST:
            qst = qst.by_task(request.task_id)
        return qst.exists()


class CommentReactionPermission(BasePermission):

    """ Checks that authenticated guest has permission to requested workflow.
        request.task_id exists only for guests """

    def has_permission(self, request, view):
        try:
            comment_id = int(view.kwargs['pk'])
        except (TypeError, ValueError):
            return False
        user = request.user
        qst = WorkflowEvent.objects.filter(
            id=comment_id,
            account_id=user.account_id,
        ).type_comment()
        if request.user.is_account_owner:
            return qst.exists()
        elif request.user.type == UserType.GUEST:
            return qst.by_task(request.task_id).exists()
        else:
            return qst.filter(workflow__members=user).exists()


class StoragePermission(BasePermission):

    message = MSG_PW_0001

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['STORAGE']
