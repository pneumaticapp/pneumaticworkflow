import re

from django.conf import settings
from django.db.models import Q
from rest_framework.permissions import BasePermission

from src.accounts.enums import UserType
from src.processes.enums import OwnerRole, OwnerType, PresetType
from src.processes.messages.template import (
    MSG_PT_0023,
    MSG_PT_0069,
    MSG_PT_0070,
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


class TemplateAdminOwnerPermission(BasePermission):

    """
    For template editing operations.
    Only admin users who are template owners can edit.
    Non-admin owners have viewer-level access only.
    """

    message = MSG_PT_0023

    def has_permission(self, request, view):
        try:
            template_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        if request.user.is_account_owner:
            return True

        if not request.user.is_admin:
            return False

        template_owner_qst = (
            Template.objects
            .by_id(template_id)
            .on_account(request.user.account_id)
            .with_template_owner(request.user.id)
        )
        return template_owner_qst.exists()


class TemplateOwnerPermission(BasePermission):

    """ Allow access for template owners, viewers, and starters """

    message = MSG_PT_0069

    def has_permission(self, request, view):
        try:
            template_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        # Account owner always has access
        if request.user.is_account_owner:
            return True

        # Check if user has any access (starter, viewer, or owner)
        template_access_qst = (
            Template.objects
            .by_id(template_id)
            .on_account(request.user.account_id)
            .with_template_access(request.user.id)
        )
        return template_access_qst.exists()


class TemplateOwnerOrViewerPermission(BasePermission):

    """ Allow access for template owners or template viewers (read-only) """

    message = MSG_PT_0070

    def has_permission(self, request, view):
        try:
            template_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        if request.user.is_account_owner:
            return True

        return (
            Template.objects
            .by_id(template_id)
            .on_account(request.user.account_id)
            .with_template_owner_or_viewer(request.user.id)
            .exists()
        )


class UserCanAccessHighlightsPermission(BasePermission):

    """ Allow admin, account owner, template owner, template viewer,
        or template starter (of any template on account) to access
        highlights/dashboard. """

    def has_permission(self, request, view):
        if getattr(request.user, 'is_admin', False):
            return True
        if getattr(request.user, 'is_account_owner', False):
            return True
        return (
            Template.objects
            .on_account(request.user.account_id)
            .with_template_access(request.user.id)
            .exists()
        )


class WorkflowMemberOrViewerPermission(BasePermission):

    """
    Allow for workflow members, template owners or template viewers.
    Template owners (including non-admins) get read-only access.
    """

    def has_permission(self, request, view):
        member_permission = WorkflowMemberPermission()
        if member_permission.has_permission(request, view):
            return True

        try:
            workflow_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        return (
            Workflow.objects
            .filter(
                pk=workflow_id,
                account_id=request.user.account_id,
            )
            .with_template_owner_or_viewer(request.user.id)
            .exists()
        )


class WorkflowOwnerPermission(BasePermission):

    """
    For workflow editing operations.
    Only admin users who are workflow owners can edit.
    Non-admin workflow owners have viewer-level access only.
    """

    def has_permission(self, request, view):
        try:
            workflow_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        if request.user.is_account_owner:
            return True

        if not request.user.is_admin:
            return False

        workflow_owner_qst = Workflow.objects.filter(
            owners=request.user,
            pk=workflow_id,
            account_id=request.user.account_id,
        )
        return workflow_owner_qst.exists()


class WorkflowMemberPermission(BasePermission):

    """
    Allow access for:
    - Account owner
    - Guests (non-user type)
    - Workflow starter (user who launched the workflow)
    - Task performers (actual performers on tasks)
    - Workflow members (performers, mentioned users)
    - Admin template owners

    Note: Template starters who are ONLY starters (not owners/viewers/members)
    should not have access to workflows they didn't start.
    This is enforced by checking that starters are not in workflow.members
    unless they are also performers or were mentioned.
    """

    def has_permission(self, request, view):
        try:
            workflow_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        user = request.user

        if user.type != UserType.USER:
            return True

        if user.is_account_owner:
            return True

        workflow = Workflow.objects.filter(
            pk=workflow_id,
            account_id=user.account_id,
        ).first()

        if not workflow:
            return False

        if workflow.workflow_starter_id == user.id:
            return True

        is_performer = TaskPerformer.objects.filter(
            task__workflow_id=workflow_id,
            task__account_id=user.account_id,
        ).filter(
            Q(user_id=user.id) |
            Q(group__users__id=user.id),
        ).exists()

        if is_performer:
            return True

        is_member = workflow.members.filter(id=user.id).exists()
        if is_member:
            return True

        template = workflow.template
        if template and user.is_admin:
            is_template_owner = template.owners.filter(
                Q(type=OwnerType.USER, user_id=user.id)
                | Q(type=OwnerType.GROUP, group__users__id=user.id),
                role=OwnerRole.OWNER,
                is_deleted=False,
            ).exists()
            if is_template_owner:
                return True

        return False


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

    """
    For task editing operations (performers, due_date).
    Only admin users who are workflow owners can edit.
    Non-admin workflow owners have viewer-level access only.
    """

    def has_permission(self, request, view):
        try:
            task_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        if request.user.is_account_owner:
            return True

        if not request.user.is_admin:
            return False

        workflow_owner_qst = Task.objects.filter(
            workflow__owners=request.user,
            pk=task_id,
            account_id=request.user.account_id,
        )
        return workflow_owner_qst.exists()


class TaskWorkflowMemberPermission(BasePermission):

    """
    Allow access for:
    - Account owner
    - Guests (non-user type)
    - Workflow starter (user who launched the workflow)
    - Task performers (actual performers on tasks in this workflow)
    - Workflow members (performers, mentioned users)
    - Admin template owners
    """

    def has_permission(self, request, view):
        try:
            task_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        user = request.user

        if user.type != UserType.USER:
            return True

        if user.is_account_owner:
            return True

        task = Task.objects.filter(
            id=task_id,
            account_id=user.account_id,
        ).select_related('workflow', 'workflow__template').first()

        if not task:
            # If task doesn't exist, let Django handle 404 response
            # by allowing permission and letting get_object_or_404 fail
            return True

        workflow = task.workflow

        if workflow.workflow_starter_id == user.id:
            return True

        is_performer = TaskPerformer.objects.filter(
            task__workflow_id=workflow.id,
            task__account_id=user.account_id,
        ).filter(
            Q(user_id=user.id) |
            Q(group__users__id=user.id),
        ).exists()

        if is_performer:
            return True

        is_member = workflow.members.filter(id=user.id).exists()
        if is_member:
            return True

        template = workflow.template
        if template and user.is_admin:
            is_template_owner = template.owners.filter(
                Q(type=OwnerType.USER, user_id=user.id)
                | Q(type=OwnerType.GROUP, group__users__id=user.id),
                role=OwnerRole.OWNER,
                is_deleted=False,
            ).exists()
            if is_template_owner:
                return True

        return False


class TaskWorkflowMemberOrViewerPermission(BasePermission):

    """Task retrieve/events: workflow members, template owners or viewers."""

    def has_permission(self, request, view):
        member_permission = TaskWorkflowMemberPermission()
        if member_permission.has_permission(request, view):
            return True
        try:
            task_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        return (
            Workflow.objects
            .filter(
                tasks__id=task_id,
                account_id=request.user.account_id,
            )
            .with_template_owner_or_viewer(request.user.id)
            .exists()
        )


class TaskCommentPermission(BasePermission):

    """
    Allow task comments for:
    - Account owners and admins
    - Workflow members
    - Template owners
    - Template viewers
    - Task performers
    """

    def has_permission(self, request, view):
        try:
            task_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        if request.user.is_account_owner or request.user.is_admin:
            return True

        if request.user.type == UserType.GUEST:
            return True

        user_id = request.user.id
        account_id = request.user.account_id

        # Check workflow member or owner (single query)
        is_workflow_member = Workflow.objects.filter(
            tasks__id=task_id,
            account_id=account_id,
        ).filter(
            Q(members=user_id) | Q(owners=user_id),
        ).exists()
        if is_workflow_member:
            return True

        # Check task performer
        is_performer = (
            TaskPerformer.objects
            .by_task(task_id)
            .filter(task__account_id=account_id)
            .by_user_or_group(user_id)
            .exists()
        )
        if is_performer:
            return True

        # Check template owner or viewer
        return (
            Workflow.objects
            .filter(tasks__id=task_id, account_id=account_id)
            .with_template_owner_or_viewer(user_id)
            .exists()
        )


class WorkflowCommentPermission(BasePermission):

    """
    Allow workflow comments for:
    - Account owners and admins
    - Workflow members
    - Template owners
    - Template viewers
    """

    def has_permission(self, request, view):
        try:
            workflow_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

        if request.user.is_account_owner or request.user.is_admin:
            return True

        if request.user.type == UserType.GUEST:
            return True

        user_id = request.user.id
        account_id = request.user.account_id
        base_qst = Workflow.objects.by_id(workflow_id).on_account(account_id)

        # Check workflow member or owner (single query)
        is_workflow_member = base_qst.filter(
            Q(members=user_id) | Q(owners=user_id),
        ).exists()
        if is_workflow_member:
            return True

        # Check template owner or viewer
        return base_qst.with_template_owner_or_viewer(user_id).exists()


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

    """
    Allow comment reactions/watched for:
    - Account owners and admins
    - Workflow members
    - Template owners
    - Template viewers
    - Guests (for their task)
    """

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

        if user.is_account_owner or user.is_admin:
            return qst.exists()

        if user.type == UserType.GUEST:
            return qst.by_task(request.task_id).exists()

        # Check workflow members
        is_member = qst.filter(
            Q(workflow__members=user.id) |
            Q(workflow__tasks__taskperformer__user_id=user.id) |
            Q(workflow__tasks__taskperformer__group__users=user.id),
        ).exists()
        if is_member:
            return True

        # Check template owner or viewer via workflow
        workflow_id = qst.values_list('workflow_id', flat=True).first()
        if workflow_id is None:
            return False

        return (
            Workflow.objects
            .by_id(workflow_id)
            .on_account(user.account_id)
            .with_template_owner_or_viewer(user.id)
            .exists()
        )


class StoragePermission(BasePermission):

    message = MSG_PW_0001

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['STORAGE']


class TemplatePresetPermission(BasePermission):

    """
    Permission for preset editing/deletion.
    For ACCOUNT presets: only admin template owners can edit.
    Non-admin owners have viewer-level access only.
    """

    def has_permission(self, request, view):
        try:
            preset_id = int(view.kwargs.get('pk'))
        except (ValueError, TypeError):
            return False

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
            if not user.is_admin:
                return False
            return preset.template.owners.filter(user_id=user.id).exists()
        return False
