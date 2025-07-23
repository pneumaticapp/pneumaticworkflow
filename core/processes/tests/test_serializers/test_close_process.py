import pytest
from rest_framework.exceptions import ValidationError

from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.processes.models.templates.owner import TemplateOwner
from pneumatic_backend.processes.enums import (
    OwnerType,
    WorkflowStatus,
)
from pneumatic_backend.processes.serializers.workflow import (
    WorkflowFinishSerializer,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_invited_user,
    create_test_account,
    create_test_template
)


pytestmark = pytest.mark.django_db


class TestWorkflowCloseSerializer:

    def test_final__user_is_account_owner__ok(self):

        user = create_test_user(is_account_owner=True)
        workflow = create_test_workflow(user, finalizable=True)
        workflow.save()
        serializer = WorkflowFinishSerializer(
            instance=workflow,
            data={},
            context={
                'user': user,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        assert workflow.status == WorkflowStatus.DONE

    def test_final__user_is_template_owner__ok(self):

        user = create_test_user()
        workflow = create_test_workflow(user, finalizable=True)
        workflow.save()
        serializer = WorkflowFinishSerializer(
            instance=workflow,
            data={},
            context={
                'user': user,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert user in workflow.owners.all()
        assert workflow.status == WorkflowStatus.DONE

    def test_final__user_is_current_task_performer__ok(self):

        user = create_test_user()
        workflow = create_test_workflow(user, finalizable=True)
        workflow.save()
        serializer = WorkflowFinishSerializer(
            instance=workflow,
            data={},
            context={
                'user': user,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        assert user in workflow.current_task_instance.performers.all()
        assert workflow.status == WorkflowStatus.DONE

    def test_final_workflow_is_not_finalizable__validation_error(self):

        user = create_test_user()
        workflow = create_test_workflow(user, finalizable=False)
        serializer = WorkflowFinishSerializer(
            instance=workflow,
            data={},
            context={
                'user': user,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)

        with pytest.raises(ValidationError) as ex:
            serializer.save()

        # assert
        assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
        assert ex.value.detail['message'] == messages.MSG_PW_0009

    def test_final__user_cant_be_finish__validation_error(self):

        account = create_test_account()
        template_owner = create_test_user(account=account)
        invited = create_invited_user(template_owner)
        template = create_test_template(
            user=template_owner,
            is_active=True,
            tasks_count=1,
            finalizable=True
        )
        workflow = create_test_workflow(
            user=template_owner,
            template=template,
        )
        TemplateOwner.objects.filter(
            template=template,
            type=OwnerType.USER,
            user_id=invited.id
        ).delete()
        serializer = WorkflowFinishSerializer(
            instance=workflow,
            data={},
            context={
                'user': invited,
                'is_superuser': False,
                'auth_type': AuthTokenType.USER
            }
        )
        serializer.is_valid(raise_exception=True)

        with pytest.raises(ValidationError) as ex:
            serializer.save()

        # assert
        assert ex.value.detail['code'] == ErrorCode.VALIDATION_ERROR
        assert ex.value.detail['message'] == messages.MSG_PW_0009
