import re

from django.conf import settings
from django.db.models import Count, Q
from rest_framework.permissions import BasePermission

from src.accounts.enums import UserType
from src.processes.enums import PresetType
from src.processes.messages.template import (
    MSG_PT_0023,
)
from src.processes.messages.workflow import (
    MSG_PW_0001,
)
from src.processes.models.templates.preset import TemplatePreset
from src.processes.models.templates.template import Template
from src.processes.models.workflows.checklist import Checklist
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.task import (
    Task,
    TaskPerformer,
)
from src.processes.models.workflows.workflow import Workflow


class TemplateOwnerPermission(BasePermission):

    """ For template details API """

    message = MSG_PT_0023

    def has_permission(self, request, view):
        try:
            template_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False
        else:
            template_owner_qst = (
                Template.objects
                .by_id(template_id)
                .on_account(request.user.account_id)
                .with_template_owner(request.user.id)
            )
            return (
                request.user.is_account_owner
                or template_owner_qst.exists()
            )


class WorkflowOwnerPermission(BasePermission):

    """ For workflow details API """

    def has_permission(self, request, view):
        try:
            workflow_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False
        else:
            workflow_owner_qst = Workflow.objects.filter(
                owners=request.user,
                pk=workflow_id,
                account_id=request.user.account_id,
            )
            return (
                request.user.is_account_owner or
                workflow_owner_qst.exists()
            )


class WorkflowMemberPermission(BasePermission):

    """ Allow for account owner, guests and workflow members
        Use for workflow API only  """

    def has_permission(self, request, view):
        try:
            workflow_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False
        else:
            if request.user.type != UserType.USER:
                return True

            # Verifying that the user belongs to group that is performer
            workflow_access_query = Workflow.objects.by_id(
                workflow_id).on_account(request.user.account_id).filter(
                Q(members=request.user.id) |
                Q(tasks__taskperformer__group__users=request.user.id),
            ).distinct()
            return (
                request.user.is_account_owner or
                workflow_access_query.exists()
            )


class TaskRevertPermission(BasePermission):

    def has_permission(self, request, view):
        if request.user.is_guest:
            return False
        try:
            task_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False
        else:
            task_performer_qst = (
                TaskPerformer.objects
                .by_task(task_id)
                .by_user_or_group(request.user.id)
                .exclude_directly_deleted()
            )
            return (
                request.user.is_account_owner or
                task_performer_qst.exists()
            )


class TaskCompletePermission(BasePermission):

    def has_permission(self, request, view):
        try:
            task_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False
        else:
            if request.user.is_guest and request.task_id != task_id:
                return False
            task_performer_qst = (
                TaskPerformer.objects
                .by_task(task_id)
                .by_user_or_group(request.user.id)
                .exclude_directly_deleted()
            )
            return (
                request.user.is_account_owner or
                task_performer_qst.exists()
            )


class TaskWorkflowOwnerPermission(BasePermission):

    """ For tasks details API """

    def has_permission(self, request, view):
        try:
            task_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False
        else:
            workflow_owner_qst = Task.objects.filter(
                workflow__owners=request.user,
                pk=task_id,
                account_id=request.user.account_id,
            )
            return (
                request.user.is_account_owner or
                workflow_owner_qst.exists()
            )


class TaskWorkflowMemberPermission(BasePermission):

    """ Use for task detail API only """

    def has_permission(self, request, view):
        try:
            task_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        if request.user.type != UserType.USER or request.user.is_account_owner:
            return True

        query = Task.objects.filter(
            id=task_id,
            account_id=request.user.account_id,
        ).annotate(
            is_member=Count(
                'workflow__members',
                filter=Q(workflow__members=request.user.id),
            ),
        )
        is_member = query.values('is_member').first()
        if is_member is None:
            # Task not found
            return True
        # Task found - check membership
        return bool(is_member['is_member'])


class GuestWorkflowPermission(BasePermission):

    """ Checks that authenticated guest has permission to requested workflow.
        request.task_id exists only for guests """

    workflow_urls_pattern = (
        r'^\/workflows\/(?P<workflow_id>\d+)\/'
        r'(comment|task-complete)\/{0,1}$'
    )

    def has_permission(self, request, view):
        if request.user.type == UserType.GUEST:
            match = re.match(self.workflow_urls_pattern, request.path)
            if match is None:
                return False
            workflow_id = int(match.group('workflow_id'))
            return Task.objects.filter(
                id=request.task_id,
                workflow_id=workflow_id,
            ).active().exists()
        return True


class GuestWorkflowEventsPermission(BasePermission):

    def has_permission(self, request, view):
        if request.user.type == UserType.GUEST:
            try:
                workflow_id = int(view.kwargs.get('pk'))
            except (ValueError, TypeError):
                return False
            else:
                return Task.objects.filter(
                    id=request.task_id,
                    workflow_id=workflow_id,
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
    task_actions_urls_pattern = (
        r'^\/v2\/tasks\/(?P<task_id>\d+)\/(events|comment)\/?$'
    )
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

    def _request_to_actions(self, request):
        """ Allow requests to the events endpoint:
            /v2/tasks/<task_id:int>/events """

        match = re.match(self.task_actions_urls_pattern, request.path)
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
            id=int(match.group('checklist_id')),
        ).exists()

    def has_permission(self, request, view):

        """ Allow guests to access only specified endpoints """

        if request.user.type == UserType.GUEST:
            return (
                self._request_to_task(request)
                or self._request_to_checklist(request)
                or self._request_to_actions(request)
            )
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
            id=comment_id,
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
        if request.user.type == UserType.GUEST:
            return qst.by_task(request.task_id).exists()
        return qst.filter(
            Q(workflow__members=request.user.id) |
            Q(workflow__tasks__taskperformer__group__users=request.user.id),
        ).exists()


class StoragePermission(BasePermission):

    message = MSG_PW_0001

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['STORAGE']


class TemplatePresetPermission(BasePermission):

    def has_permission(self, request, view):
        try:
            preset_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False
        else:
            user = request.user
            preset = TemplatePreset.objects.filter(
                id=preset_id,
                account_id=user.account_id,
            ).first()
            if not preset:
                return False
            if preset.author_id == user.id or user.is_account_owner:
                return True
            if preset.type == PresetType.ACCOUNT:
                return preset.template.owners.filter(user_id=user.id).exists()
            return False
