# pylint:disable=redefined-outer-name
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from pneumatic_backend.processes.messages import workflow as messages
from pneumatic_backend.processes.models import (
    Template,
    TaskTemplate,
    Workflow,
    Task,
    Kickoff,
    FieldTemplate,
    SystemTemplate,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
)
from pneumatic_backend.processes.enums import (
    FieldType,
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
        kickoff_field_sql
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
            is_active=True
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
            is_active=True
        )
        workflow = Workflow.objects.create(
            name=template.name,
            description=template.description,
            account_id=template.account_id,
            tasks_count=template.tasks_count,
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
            tasks_count=template.tasks_count,
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


class TestWorkflow:
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
    def task_sql(self):
        return """
          SELECT
            id,
            is_deleted
          FROM processes_task
          WHERE workflow_id = %(workflow_id)s
        """

    def test_delete(
        self,
        workflow_sql,
        task_sql,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user)

        # act
        workflow.delete()

        # assert
        assert Workflow.objects.raw(
            workflow_sql,
            {'workflow_id': workflow.id},
        )[0].is_deleted is True
        task_list = Task.objects.raw(
            task_sql,
            {'workflow_id': workflow.id}
        )
        assert task_list[0].is_deleted is True
        assert task_list[1].is_deleted is True
        assert task_list[2].is_deleted is True


class TestSystemTemplate:

    def test_validation_correct(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "api_name": "reasons-3",
                            "is_required": True
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False,
                    "description": "Tell client that everything is ok"
                },
                {
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
            is_active=True,
        )
        system_template.validate_template()

    def test_validation__empty_kickoff__ok(self):
        template = {
            "name": "Clients requests processing",
            "kickoff": {},
            "tasks": [
                {
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
            ],
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
            is_active=True,
        )
        system_template.validate_template()

    def test_validation__empty_kickoff_fields__ok(self):
        template = {
            "name": "Clients requests processing",
            "kickoff": {
                'fields': []
            },
            "tasks": [
                {
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
            ],
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
            is_active=True,
        )
        system_template.validate_template()

    def test_validation__kickoff_not_dict__raise(self):

        # arrange
        template = {
            "name": "Clients requests processing",
            "kickoff": [],
            "tasks": [
                {
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
            ],
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
            is_active=True,
        )

        # act
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        # assert
        assert ex.value.message == messages.MSG_PW_0061

    def test_validation_wrong_api_names(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True,
                    "description": "{{reasons-3}}"
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "api_name": "reasons-3",
                            "is_required": True
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-7",
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()
        assert ex.value.messages == [messages.MSG_PW_0064([1])]

    def test_selections_not_provided(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "api_name": "reasons-3",
                            "is_required": True
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-7",
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.messages == [messages.MSG_PW_0060]

    def test_api_name_not_provided_on_kickoff(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "api_name": "reasons-3",
                            "is_required": True
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.messages == [messages.MSG_PW_0065]

    def test_api_name_in_output(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "is_required": True
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "description": "",
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-6"
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.messages == [messages.MSG_PW_0065]

    def test_api_name_not_provided_on_output(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "is_required": True
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-6"
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.messages == [messages.MSG_PW_0065]

    def test_delay_in_the_first_task(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "delay": "00:00:10",
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "is_required": True,
                            "api_name": "reasons-5"
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-6"
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.messages == [messages.MSG_PW_0068]

    def test_incorrect_order(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 1,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "is_required": True,
                            "api_name": "reasons-5"
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-6"
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.messages == [messages.MSG_PW_0063]

    def test_validate__id_in_task__raise_admin_id_not_allowed(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "id": 3,
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "is_required": True,
                            "api_name": "reasons-5"
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-6"
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.message == messages.MSG_PW_0059

    def test_validate__id_in_kickoff__raise_admin_id_not_allowed(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "is_required": True,
                            "api_name": "reasons-5"
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "id": 3,
                "fields": [
                    {
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-6"
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.message == messages.MSG_PW_0059

    def test_validate__id_in_field__raise_admin_id_not_allowed(self):
        template = {
            "name": "Clients requests processing",
            "tasks": [
                {
                    "url": "https://google.com/forms",
                    "name": "Checking data",
                    "number": 1,
                    "require_completion_by_all": True
                },
                {
                    "url": "https://pneumatic.app/",
                    "name": "Finding reasons of request",
                    "number": 2,
                    "fields": [
                        {
                            "name": "Reasons",
                            "type": "text",
                            "is_required": True,
                            "api_name": "reasons-5"
                        }
                    ],
                    "require_completion_by_all": False
                },
                {
                    "url": "https://gmail.com/",
                    "name": "Responsing to client",
                    "number": 3,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://slack.com/",
                    "name": "Creating report",
                    "number": 4,
                    "require_completion_by_all": False
                },
                {
                    "url": "https://google.com/forms",
                    "name": "Create card",
                    "number": 5,
                    "require_completion_by_all": False
                }
            ],
            "kickoff": {
                "fields": [
                    {
                        "id": 5,
                        "name": "Client name",
                        "type": "string",
                        "required": True,
                        "description": "Enter client name",
                        "api_name": "client-name-5",
                    },
                    {
                        "name": "Kind of client activity",
                        "type": "checkbox",
                        "required": True,
                        "selections": [
                            {
                                "value": "Sales"
                            },
                            {
                                "value": "B2B"
                            },
                            {
                                "value": "IT"
                            },
                            {
                                "value": "Other"
                            }
                        ],
                        "description": "Select client activities",
                        "api_name": "kind-of-client-activity-6"
                    }
                ],
                "description": "Implement first parameters of task"
            },
            "finalizable": False
        }
        system_template = SystemTemplate.objects.create(
            template=template,
        )
        with pytest.raises(ValidationError) as ex:
            system_template.validate_template()

        assert ex.value.message == messages.MSG_PW_0059
