from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import (
    FieldRuleOperator,
    FieldRuleType,
    FieldType,
)
from src.processes.messages.workflow import (
    MSG_PW_0092,
)
from src.processes.models.workflows.fields import (
    FieldRuleGroupAnd,
    FieldRuleGroupOr,
    FieldRuleSet,
    TaskField,
)
from src.processes.services.exceptions import (
    FieldRuleCheckServiceException,
)
from src.processes.services.tasks.fields.field_ruleset_check import (
    FieldRuleCheckService,
    FieldRuleOperations,
)
from src.processes.services.workflow_action import (
    WorkflowActionService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestFieldRuleOperations:

    def test_equal(self):
        assert FieldRuleOperations.equal('abc', 'abc') is True
        assert FieldRuleOperations.equal('abc', 'def') is False
        assert FieldRuleOperations.equal(10, 10) is True
        assert FieldRuleOperations.equal(None, None) is True
        assert FieldRuleOperations.equal('abc', None) is False

    def test_not_equal(self):
        assert FieldRuleOperations.not_equal('abc', 'def') is True
        assert FieldRuleOperations.not_equal('abc', 'abc') is False

    def test_greater_than(self):
        assert FieldRuleOperations.greater_than(10, 5) is True
        assert FieldRuleOperations.greater_than(5, 10) is False
        assert FieldRuleOperations.greater_than(5, 5) is False
        assert FieldRuleOperations.greater_than(None, 5) is False
        assert FieldRuleOperations.greater_than(5, None) is False
        assert FieldRuleOperations.greater_than('abc', 5) is False

    def test_less_than(self):
        assert FieldRuleOperations.less_than(5, 10) is True
        assert FieldRuleOperations.less_than(10, 5) is False
        assert FieldRuleOperations.less_than(5, 5) is False
        assert FieldRuleOperations.less_than(None, 5) is False
        assert FieldRuleOperations.less_than(5, None) is False
        assert FieldRuleOperations.less_than('abc', 5) is False

    def test_exists(self):
        assert FieldRuleOperations.exists('value') is True
        assert FieldRuleOperations.exists(0) is True
        assert FieldRuleOperations.exists(Decimal(0)) is True
        assert FieldRuleOperations.exists('') is False
        assert FieldRuleOperations.exists(None) is False
        assert FieldRuleOperations.exists([]) is False
        assert FieldRuleOperations.exists(['item']) is True

    def test_not_exists(self):
        assert FieldRuleOperations.not_exists(None) is True
        assert FieldRuleOperations.not_exists('') is True
        assert FieldRuleOperations.not_exists('val') is False
        assert FieldRuleOperations.not_exists(0) is False

    def test_contains(self):
        assert FieldRuleOperations.contains('hello world', 'world') is True
        assert FieldRuleOperations.contains('hello world', 'xyz') is False
        assert FieldRuleOperations.contains(['a', 'b'], 'a') is True
        assert FieldRuleOperations.contains(['a', 'b'], 'c') is False
        assert FieldRuleOperations.contains(None, 'a') is False
        assert FieldRuleOperations.contains('abc', None) is False
        assert FieldRuleOperations.contains('abc', '') is False

    def test_not_contains(self):
        assert FieldRuleOperations.not_contains('hello', 'xyz') is True
        assert FieldRuleOperations.not_contains('hello', 'ell') is False
        assert FieldRuleOperations.not_contains(['a'], 'b') is True
        assert FieldRuleOperations.not_contains(None, 'a') is False
        assert FieldRuleOperations.not_contains('abc', None) is False


class TestFieldRuleCheckService:

    def test_show_rule__satisfied__field_is_visible(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        source_field = TaskField.objects.create(
            name='Source Field',
            api_name='source-field',
            type=FieldType.STRING,
            value='approved',
            workflow=workflow,
            task=task,
            account=account,
        )
        target_field = TaskField.objects.create(
            name='Target Field',
            api_name='target-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=True,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Show target',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-1',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-1',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=source_field.api_name,
            operator=FieldRuleOperator.EQUAL,
            value='approved',
            api_name='group-and-1',
        )

        # act
        FieldRuleCheckService(workflow_id=workflow.id).apply_rulesets(
            [ruleset],
        )

        # assert
        target_field.refresh_from_db()
        assert target_field.is_hidden is False

    def test_show_rule__not_satisfied__field_is_hidden(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        source_field = TaskField.objects.create(
            name='Source Field',
            api_name='source-field',
            type=FieldType.STRING,
            value='rejected',
            workflow=workflow,
            task=task,
            account=account,
        )
        target_field = TaskField.objects.create(
            name='Target Field',
            api_name='target-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=False,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Show target',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-1',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-1',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=source_field.api_name,
            operator=FieldRuleOperator.EQUAL,
            value='approved',
            api_name='group-and-1',
        )

        # act
        FieldRuleCheckService(workflow_id=workflow.id).apply_rulesets(
            [ruleset],
        )

        # assert
        target_field.refresh_from_db()
        assert target_field.is_hidden is True

    def test_show_rule__multiple_rulesets__any_satisfied_shows_field(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        source_1 = TaskField.objects.create(
            name='Source 1',
            api_name='source-1',
            type=FieldType.STRING,
            value='no',
            workflow=workflow,
            task=task,
            account=account,
        )
        source_2 = TaskField.objects.create(
            name='Source 2',
            api_name='source-2',
            type=FieldType.STRING,
            value='yes',
            workflow=workflow,
            task=task,
            account=account,
        )
        target_field = TaskField.objects.create(
            name='Target Field',
            api_name='target-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=True,
        )

        ruleset_1 = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Rule 1',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-1',
        )
        group_or_1 = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset_1,
            api_name='group-or-1',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or_1,
            field=source_1.api_name,
            operator=FieldRuleOperator.EQUAL,
            value='yes',
            api_name='group-and-1',
        )

        ruleset_2 = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Rule 2',
            type=FieldRuleType.SHOW,
            order=2,
            api_name='ruleset-2',
        )
        group_or_2 = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset_2,
            api_name='group-or-2',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or_2,
            field=source_2.api_name,
            operator=FieldRuleOperator.EQUAL,
            value='yes',
            api_name='group-and-2',
        )

        # act
        FieldRuleCheckService(workflow_id=workflow.id).apply_rulesets(
            [ruleset_1, ruleset_2],
        )

        # assert
        target_field.refresh_from_db()
        assert target_field.is_hidden is False

    def test_show_rule__source_field_missing__field_is_hidden(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        target_field = TaskField.objects.create(
            name='Target Field',
            api_name='target-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=False,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Rule with missing source',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-missing-src',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-ms',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field='non-existent-source-field',
            operator=FieldRuleOperator.EQUAL,
            value='yes',
            api_name='group-and-ms',
        )

        # act
        FieldRuleCheckService(workflow_id=workflow.id).apply_rulesets(
            [ruleset],
        )

        # assert
        target_field.refresh_from_db()
        assert target_field.is_hidden is True

    def test_validator_rule__satisfied__passes(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        field = TaskField.objects.create(
            name='Age Field',
            api_name='age-field',
            type=FieldType.NUMBER,
            value='25',
            workflow=workflow,
            task=task,
            account=account,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=field,
            name='Age must be >= 18',
            type=FieldRuleType.VALIDATOR,
            message='Age must be greater than 17',
            order=1,
            api_name='ruleset-v1',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-v1',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=field.api_name,
            operator=FieldRuleOperator.GREATER_THAN,
            value='17',
            api_name='group-and-v1',
        )

        # act & assert: does not raise
        FieldRuleCheckService(workflow_id=workflow.id).apply_rulesets(
            [ruleset],
        )

    def test_validator_rule__not_satisfied__raises_exception(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        field = TaskField.objects.create(
            name='Age Field',
            api_name='age-field',
            type=FieldType.NUMBER,
            value='16',
            workflow=workflow,
            task=task,
            account=account,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=field,
            name='Age must be > 17',
            type=FieldRuleType.VALIDATOR,
            message='Age must be greater than 17',
            order=1,
            api_name='ruleset-v1',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-v1',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=field.api_name,
            operator=FieldRuleOperator.GREATER_THAN,
            value='17',
            api_name='group-and-v1',
        )

        # act & assert
        with pytest.raises(FieldRuleCheckServiceException) as exc_info:
            FieldRuleCheckService(workflow_id=workflow.id).apply_rulesets(
                [ruleset],
            )

        assert exc_info.value.field_api_name == 'age-field'
        assert exc_info.value.message == 'Age must be greater than 17'

    def test_validator_rule__not_satisfied_no_message__raises_default_message(
        self,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        field = TaskField.objects.create(
            name='Age Field',
            api_name='age-field',
            type=FieldType.NUMBER,
            value='16',
            workflow=workflow,
            task=task,
            account=account,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=field,
            name='Age must be > 17',
            type=FieldRuleType.VALIDATOR,
            message=None,
            order=1,
            api_name='ruleset-v1',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-v1',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=field.api_name,
            operator=FieldRuleOperator.GREATER_THAN,
            value='17',
            api_name='group-and-v1',
        )

        # act & assert
        with pytest.raises(FieldRuleCheckServiceException) as exc_info:
            FieldRuleCheckService(workflow_id=workflow.id).apply_rulesets(
                [ruleset],
            )

        assert exc_info.value.field_api_name == 'age-field'
        assert exc_info.value.message == MSG_PW_0092

    def test_validator_rule__hidden_field__skipped(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        field = TaskField.objects.create(
            name='Hidden Field',
            api_name='hidden-field',
            type=FieldType.NUMBER,
            value='10',
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=True,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=field,
            name='Validator on hidden',
            type=FieldRuleType.VALIDATOR,
            message='Should not fail because field is hidden',
            order=1,
            api_name='ruleset-hidden',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-h',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=field.api_name,
            operator=FieldRuleOperator.GREATER_THAN,
            value='100',
            api_name='group-and-h',
        )

        # act & assert: does not raise because field is hidden
        FieldRuleCheckService(workflow_id=workflow.id).apply_rulesets(
            [ruleset],
        )


class TestFieldRuleActionIntegration:

    def test_complete_task__validator_failed__raises_exception(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        mocker.patch(
            'src.processes.services.workflow_action.WorkflowEventService'
            '.task_complete_event',
        )
        mocker.patch(
            'src.processes.services.workflow_action.AnalyticService'
            '.task_completed',
        )
        mocker.patch(
            'src.processes.services.workflow_action'
            '.send_task_completed_websocket.delay',
        )

        field = TaskField.objects.create(
            name='Score',
            api_name='score-field',
            type=FieldType.NUMBER,
            value='5',
            workflow=workflow,
            task=task,
            account=account,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=field,
            name='Score validator',
            type=FieldRuleType.VALIDATOR,
            message='Score must be greater than 10',
            order=1,
            api_name='ruleset-score',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-s',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=field.api_name,
            operator=FieldRuleOperator.GREATER_THAN,
            value='10',
            api_name='group-and-s',
        )

        service = WorkflowActionService(
            workflow=workflow,
            user=user,
        )

        # act & assert
        with pytest.raises(FieldRuleCheckServiceException) as exc_info:
            service.complete_task_for_user(
                task=task,
                fields_values={'score-field': '8'},
            )

        assert exc_info.value.field_api_name == 'score-field'
        assert exc_info.value.message == 'Score must be greater than 10'

    def test_complete_task__validator_passed_and_show_rules_applied(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=2)
        task_1 = workflow.tasks.get(number=1)

        mocker.patch(
            'src.processes.services.workflow_action.WorkflowEventService'
            '.task_complete_event',
        )
        mocker.patch(
            'src.processes.services.workflow_action.AnalyticService'
            '.task_completed',
        )
        mocker.patch(
            'src.processes.services.workflow_action'
            '.send_task_completed_websocket.delay',
        )

        field_1 = TaskField.objects.create(
            name='Choice',
            api_name='choice-field',
            type=FieldType.STRING,
            value='',
            workflow=workflow,
            task=task_1,
            account=account,
        )
        field_2 = TaskField.objects.create(
            name='Dependent Field',
            api_name='dep-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task_1,
            account=account,
            is_hidden=True,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=field_2,
            name='Show dependent when Choice is yes',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-show-dep',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-dep',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=field_1.api_name,
            operator=FieldRuleOperator.EQUAL,
            value='yes',
            api_name='group-and-dep',
        )

        service = WorkflowActionService(
            workflow=workflow,
            user=user,
        )

        # act
        service.complete_task_for_user(
            task=task_1,
            fields_values={'choice-field': 'yes'},
        )

        # assert
        field_2.refresh_from_db()
        assert field_2.is_hidden is False

    def test_complete_task__show_rules_applied_to_subsequent_tasks(
        self,
        mocker,
    ):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=2)
        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)

        mocker.patch(
            'src.processes.services.workflow_action.WorkflowEventService'
            '.task_complete_event',
        )
        mocker.patch(
            'src.processes.services.workflow_action.AnalyticService'
            '.task_completed',
        )
        mocker.patch(
            'src.processes.services.workflow_action'
            '.send_task_completed_websocket.delay',
        )

        field_1 = TaskField.objects.create(
            name='Choice on Task 1',
            api_name='choice-field-1',
            type=FieldType.STRING,
            value='',
            workflow=workflow,
            task=task_1,
            account=account,
        )
        field_2 = TaskField.objects.create(
            name='Dependent on Task 2',
            api_name='dep-field-2',
            type=FieldType.STRING,
            workflow=workflow,
            task=task_2,
            account=account,
            is_hidden=True,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=field_2,
            name='Show task 2 field when task 1 choice is yes',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-show-task2-dep',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-task2-dep',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=field_1.api_name,
            operator=FieldRuleOperator.EQUAL,
            value='yes',
            api_name='group-and-task2-dep',
        )

        service = WorkflowActionService(
            workflow=workflow,
            user=user,
        )

        # act
        service.complete_task_for_user(
            task=task_1,
            fields_values={'choice-field-1': 'yes'},
        )

        # assert
        field_2.refresh_from_db()
        assert field_2.is_hidden is False

    def test_show_rule__checkbox_comma_space__contain_second_option(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        source_field = TaskField.objects.create(
            name='Checkbox Source',
            api_name='checkbox-source',
            type=FieldType.CHECKBOX,
            value='first option, second option',
            workflow=workflow,
            task=task,
            account=account,
        )
        target_field = TaskField.objects.create(
            name='Target Field',
            api_name='target-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=True,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Show when contains second option',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-chk-contain',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-chk',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=source_field.api_name,
            operator=FieldRuleOperator.CONTAIN,
            value='second option',
            api_name='group-and-chk',
        )

        # act
        FieldRuleCheckService(
            workflow_id=workflow.id,
        ).apply_rulesets([ruleset])

        # assert
        target_field.refresh_from_db()
        assert target_field.is_hidden is False

    def test_show_rule__checkbox_comma_space__equal_all_options(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        source_field = TaskField.objects.create(
            name='Checkbox Source',
            api_name='checkbox-source',
            type=FieldType.CHECKBOX,
            value='first option, second option',
            workflow=workflow,
            task=task,
            account=account,
        )
        target_field = TaskField.objects.create(
            name='Target Field',
            api_name='target-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=True,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Show when equals all options',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-chk-equal',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-chk-eq',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=source_field.api_name,
            operator=FieldRuleOperator.EQUAL,
            value='second option, first option',
            api_name='group-and-chk-eq',
        )

        # act
        FieldRuleCheckService(
            workflow_id=workflow.id,
        ).apply_rulesets([ruleset])

        # assert
        target_field.refresh_from_db()
        assert target_field.is_hidden is False

    def test_show_rule__user_field_with_group_id__equal(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        source_field = TaskField.objects.create(
            name='User Source',
            api_name='user-source',
            type=FieldType.USER,
            group_id=42,
            user_id=None,
            workflow=workflow,
            task=task,
            account=account,
        )
        target_field = TaskField.objects.create(
            name='Target Field',
            api_name='target-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=True,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Show when group is 42',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-usr-grp',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-usr',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=source_field.api_name,
            operator=FieldRuleOperator.EQUAL,
            value='42',
            api_name='group-and-usr',
        )

        # act
        FieldRuleCheckService(
            workflow_id=workflow.id,
        ).apply_rulesets([ruleset])

        # assert
        target_field.refresh_from_db()
        assert target_field.is_hidden is False

    def test_show_rule__user_field_with_group_id__not_equal(self):
        # arrange
        account = create_test_account()
        user = create_test_owner(account=account)
        workflow = create_test_workflow(user=user, tasks_count=1)
        task = workflow.tasks.first()

        source_field = TaskField.objects.create(
            name='User Source',
            api_name='user-source',
            type=FieldType.USER,
            group_id=42,
            user_id=None,
            workflow=workflow,
            task=task,
            account=account,
        )
        target_field = TaskField.objects.create(
            name='Target Field',
            api_name='target-field',
            type=FieldType.STRING,
            workflow=workflow,
            task=task,
            account=account,
            is_hidden=True,
        )
        ruleset = FieldRuleSet.objects.create(
            account=account,
            workflow=workflow,
            field=target_field,
            name='Show when group is not 99',
            type=FieldRuleType.SHOW,
            order=1,
            api_name='ruleset-usr-grp-neq',
        )
        group_or = FieldRuleGroupOr.objects.create(
            account=account,
            workflow=workflow,
            ruleset=ruleset,
            api_name='group-or-usr-neq',
        )
        FieldRuleGroupAnd.objects.create(
            account=account,
            workflow=workflow,
            group_or=group_or,
            field=source_field.api_name,
            operator=FieldRuleOperator.NOT_EQUAL,
            value='99',
            api_name='group-and-usr-neq',
        )

        # act
        FieldRuleCheckService(
            workflow_id=workflow.id,
        ).apply_rulesets([ruleset])

        # assert
        target_field.refresh_from_db()
        assert target_field.is_hidden is False
