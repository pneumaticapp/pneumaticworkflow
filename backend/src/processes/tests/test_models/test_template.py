import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.processes.enums import (
    FieldType,
    OwnerType,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.kickoff import Kickoff
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.templates.template import Template
from src.processes.models.workflows.workflow import Workflow
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
)

UserModel = get_user_model()


pytestmark = pytest.mark.django_db


@pytest.fixture
def kickoff_sql():
    return """
      SELECT
        id,
        is_deleted
      FROM processes_kickoff
      WHERE id = %(kickoff_id)s
    """


@pytest.fixture
def kickoff_field_sql():
    return """
      SELECT
        id,
        is_deleted
      FROM processes_fieldtemplate
      WHERE kickoff_id = %(kickoff_id)s
    """


class TestKickoff:
    def test_delete(
        self,
        kickoff_sql,
        kickoff_field_sql,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(user)
        kickoff = Kickoff.objects.create(
            account_id=user.account_id,
        )
        FieldTemplate.objects.create(
            name='Name',
            type=FieldType.STRING,
            kickoff=kickoff,
            template=template,
        )

        # act
        kickoff.delete()

        # assert
        assert Kickoff.objects.raw(
            kickoff_sql,
            {'kickoff_id': kickoff.id},
        )[0].is_deleted is True
        assert FieldTemplate.objects.raw(
            kickoff_field_sql,
            {'kickoff_id': kickoff.id},
        )[0].is_deleted is True


class TestTemplate:

    @pytest.fixture
    def workflow_sql(self):
        return """
          SELECT
            id,
            is_deleted,
            template_id
          FROM processes_workflow
          WHERE id = %(workflow_id)s
        """

    @pytest.fixture
    def template_sql(self):
        return """
          SELECT
            id,
            is_deleted
          FROM processes_template
          WHERE id = %(template_id)s
        """

    @pytest.fixture
    def task_template_sql(self):
        return """
          SELECT
            id,
            is_deleted
          FROM processes_tasktemplate
          WHERE template_id = %(template_id)s
        """

    def test_delete__cascade_delete_tasks(
        self,
        template_sql,
        task_template_sql,
        kickoff_sql,
        kickoff_field_sql,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        kickoff = template.kickoff_instance

        FieldTemplate.objects.create(
            name='Name',
            type=FieldType.STRING,
            kickoff=kickoff,
            template=template,
        )

        # act
        template.delete()

        # assert
        assert Template.objects.raw(
            template_sql,
            {'template_id': template.id},
        )[0].is_deleted is True
        task_list = TaskTemplate.objects.raw(
            task_template_sql,
            {'template_id': template.id},
        )
        assert task_list[0].is_deleted is True
        assert task_list[1].is_deleted is True
        assert task_list[2].is_deleted is True
        assert Kickoff.objects.raw(
            kickoff_sql,
            {'kickoff_id': kickoff.id},
        )[0].is_deleted is True
        assert FieldTemplate.objects.raw(
            kickoff_field_sql,
            {'kickoff_id': kickoff.id},
        )[0].is_deleted is True

    def test_delete__workflow_template_set_null(
            self,
            workflow_sql,
            template_sql,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(
            user=user,
            is_active=True,
        )
        workflow = Workflow.objects.create(
            name=template.name,
            description=template.description,
            account_id=template.account_id,
            template=template,
            status_updated=timezone.now(),
        )
        template_id = template.id

        # act
        template.delete()

        # assert
        assert Template.objects.raw(
            template_sql,
            {'template_id': template_id},
        )[0].is_deleted
        w = Workflow.objects.raw(
            workflow_sql,
            {'workflow_id': workflow.id},
        )[0]
        assert w.is_deleted is False
        assert w.template_id is None

    def test_queryset_delete__with_workflow__set_legacy_template(
        self,
        template_sql,
    ):
        # arrange
        user = create_test_user()
        template = create_test_template(user)
        workflow = Workflow.objects.create(
            name=template.name,
            description=template.description,
            account_id=template.account_id,
            template=template,
            status_updated=timezone.now(),
        )
        template_id = template.id

        # act
        Template.objects.delete()

        workflow.refresh_from_db()

        # assert
        assert Template.objects.raw(
            template_sql,
            {'template_id': template_id},
        )[0].is_deleted
        assert workflow.is_deleted is False
        assert workflow.template_id is None
        assert workflow.is_legacy_template is True
        assert workflow.legacy_template_name == template.name

    def test_get_owners_as_users__empty_group__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.filter(user_id=user.id).delete()
        group = create_test_group(account)
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )

        # act
        owners = Template.objects.get_owners_as_users()

        # assert
        assert not owners

    def test_get_owners_as_users__empty_owner_template__ok(self):
        # arrange
        user = create_test_user()
        create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.filter(user_id=user.id).delete()

        # act
        owners = Template.objects.get_owners_as_users()

        # assert
        assert not owners

    def test_get_owners_as_users__user_in_group__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )
        TemplateOwner.objects.filter(user_id=user.id).delete()
        group = create_test_group(account, users=[user])
        TemplateOwner.objects.create(
            template=template,
            account=account,
            type=OwnerType.GROUP,
            group_id=group.id,
        )

        # act
        owners = Template.objects.get_owners_as_users()

        # assert
        assert list(owners) == [user.id]

    def test_get_owners_as_users__user__ok(self):
        # arrange
        user = create_test_user()
        create_test_template(
            user=user,
            is_active=True,
            tasks_count=1,
        )

        # act
        owners = Template.objects.get_owners_as_users()

        # assert
        assert list(owners) == [user.id]
