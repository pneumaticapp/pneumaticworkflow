import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import (
    ConditionAction,
    FieldType,
    PredicateOperator,
    PredicateType,
    TaskStatus,
)
from src.processes.models.workflows.attachment import FileAttachment
from src.processes.models.workflows.conditions import (
    Condition,
    Predicate,
    Rule,
)
from src.processes.models.workflows.fields import (
    FieldSelection,
    TaskField,
)
from src.processes.services.condition_check.service import (
    ConditionCheckService,
)
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_user,
    create_test_workflow,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestConditionCheckService:

    @pytest.mark.parametrize(
        ('operator', 'predicate_value', 'field_value', 'result'),
        [
            (PredicateOperator.EQUAL, '100', '100', True),
            (PredicateOperator.EQUAL, '100.00', '100', True),
            (PredicateOperator.EQUAL, '1.01', '1.0', False),
            (PredicateOperator.EQUAL, '1.5', '', False),
            (PredicateOperator.EQUAL, '', '0', False),
            (PredicateOperator.NOT_EQUAL, '1.0000000000000000001', '1', True),
            (PredicateOperator.NOT_EQUAL, '1.5', '', True),
            (PredicateOperator.NOT_EQUAL, '1.0000000000000000000', '1', False),
            (PredicateOperator.EXIST, None, '0', True),
            (PredicateOperator.EXIST, None, '0.1', True),
            (PredicateOperator.EXIST, None, '', False),
            (PredicateOperator.NOT_EXIST, None, '', True),
            (PredicateOperator.NOT_EXIST, None, '0', False),
            (PredicateOperator.MORE_THAN, '0', '1', True),
            (PredicateOperator.MORE_THAN, '0.0000000000000001', '0', False),
            (PredicateOperator.MORE_THAN, '2.0', '2', False),
            (PredicateOperator.MORE_THAN, '', '22', False),
            (PredicateOperator.MORE_THAN, '22', '', False),
            (PredicateOperator.LESS_THAN, '0.0000000000000001', '0', True),
            (PredicateOperator.LESS_THAN, '2.0', '2', False),
            (PredicateOperator.LESS_THAN, '', '22', False),
            (PredicateOperator.LESS_THAN, '22', '', False),
        ],
    )
    def test_check__number(
        self,
        operator,
        predicate_value,
        field_value,
        result,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        first_task = workflow.tasks.first()
        second_task = workflow.tasks.last()
        first_field = TaskField.objects.create(
            name='Hero',
            api_name='hero-1',
            task=first_task,
            type=FieldType.NUMBER,
            value=field_value,
            workflow=workflow,
        )
        condition = Condition.objects.create(
            task=second_task,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=first_rule,
            operator=operator,
            field_type=first_field.type,
            field=first_field.api_name,
            value=predicate_value,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is result

    @pytest.mark.parametrize(
        ('operator', 'predicate_value', 'field_value', 'result'),
        [
            (
                PredicateOperator.EQUAL,
                'Captain Marvel', 'Captain Marvel', True,
            ),
            (
                PredicateOperator.EQUAL,
                'Captain Marvel', 'CaptainMarvel', False,
            ),
            (PredicateOperator.EQUAL, None, 'Captain Marvel', False),
            (PredicateOperator.NOT_EQUAL, 'Captain Marvel', '', True),
            (PredicateOperator.EXIST, None, 'Captain Marvel', True),
            (PredicateOperator.EXIST, None, '', False),
            (PredicateOperator.NOT_EXIST, None, 'Captain Marvel', False),
            (PredicateOperator.CONTAIN, 'Captain Marvel', 'Marvel', False),
            (PredicateOperator.CONTAIN, None, 'Captain Marvel', False),
            (PredicateOperator.CONTAIN, 'Marvel', 'Captain Marvel', True),
            (PredicateOperator.CONTAIN, 'Captain Marvel', 'Iran Many', False),
            (PredicateOperator.NOT_CONTAIN, None, 'Captain Marvel', False),
            (
                    PredicateOperator.NOT_CONTAIN,
                    'Captain Marvel', 'Iran Many', True,
            ),
        ],
    )
    def test_check__string(
        self,
        operator,
        predicate_value,
        field_value,
        result,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        first_task = workflow.tasks.first()
        second_task = workflow.tasks.last()
        first_field = TaskField.objects.create(
            name='Hero',
            api_name='hero-1',
            task=first_task,
            type=FieldType.STRING,
            value=field_value,
            workflow=workflow,
        )
        condition = Condition.objects.create(
            task=second_task,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=first_rule,
            operator=operator,
            field_type=first_field.type,
            field=first_field.api_name,
            value=predicate_value,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is result

    @pytest.mark.parametrize(
        ('operator', 'predicate_value', 'field_value', 'result'),
        [
            (PredicateOperator.EXIST, None, 'some png url', True),
            (PredicateOperator.EXIST, None, '', False),
            (PredicateOperator.NOT_EXIST, None, '', True),
            (PredicateOperator.NOT_EXIST, None, 'Captain Marvel', False),
        ],
    )
    def test_check__file(
        self,
        operator,
        predicate_value,
        field_value,
        result,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        first_task = workflow.tasks.first()
        second_task = workflow.tasks.last()
        first_field = TaskField.objects.create(
            name='Hero',
            api_name='hero-1',
            task=first_task,
            type=FieldType.FILE,
            value=field_value,
            workflow=workflow,
        )
        FileAttachment.objects.create(
            name='john.cena',
            url='https://john.cena/john.cena',
            size=1488,
            account_id=user.account_id,
            output=first_field if field_value else None,
        )

        condition = Condition.objects.create(
            task=second_task,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=first_rule,
            operator=operator,
            field_type=first_field.type,
            field=first_field.api_name,
            value=predicate_value,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is result

    @pytest.mark.parametrize(
        (
            'operator',
            'predicate_value',
            'is_selected_first',
            'is_selected_second',
            'result',
        ),
        [
            (PredicateOperator.EQUAL, 'select-1', True, False, True),
            (PredicateOperator.EQUAL, 'select-1', False, False, False),
            (PredicateOperator.EQUAL, None, True, False, False),
            (PredicateOperator.NOT_EQUAL, 'select-1', False, True, True),
            (PredicateOperator.EXIST, None, True, False, True),
            (PredicateOperator.EXIST, None, False, False, False),
            (PredicateOperator.NOT_EXIST, None, True, False, False),
        ],
    )
    def test_check__dropdown(
        self,
        operator,
        predicate_value,
        is_selected_first,
        is_selected_second,
        result,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        first_task = workflow.tasks.first()
        second_task = workflow.tasks.last()
        first_field = TaskField.objects.create(
            name='Hero',
            api_name='hero-1',
            task=first_task,
            type=FieldType.DROPDOWN,
            value='',
            workflow=workflow,
        )
        FieldSelection.objects.create(
            field=first_field,
            api_name='select-1',
            value='1',
            is_selected=is_selected_first,
        )
        FieldSelection.objects.create(
            field=first_field,
            api_name='select-2',
            is_selected=is_selected_second,
            value='2',
        )

        condition = Condition.objects.create(
            task=second_task,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=first_rule,
            operator=operator,
            field_type=first_field.type,
            field=first_field.api_name,
            value=predicate_value,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is result

    @pytest.mark.parametrize(
        (
            'operator',
            'predicate_value',
            'is_selected_first',
            'is_selected_second',
            'result',
        ),
        [
            (PredicateOperator.EQUAL, 'select-1', True, False, True),
            (PredicateOperator.EQUAL, 'select-1', False, False, False),
            (PredicateOperator.EQUAL, 'select-1', True, True, False),
            (PredicateOperator.EQUAL, None, True, False, False),
            (PredicateOperator.NOT_EQUAL, 'select-1', False, True, True),
            (PredicateOperator.EXIST, None, True, False, True),
            (PredicateOperator.EXIST, None, False, False, False),
            (PredicateOperator.NOT_EXIST, None, True, False, False),
            (PredicateOperator.CONTAIN, 'select-1', True, False, True),
            (PredicateOperator.CONTAIN, 'select-1', True, True, True),
            (PredicateOperator.CONTAIN, 'select-1', False, True, False),
            (PredicateOperator.CONTAIN, None, False, True, False),
            (PredicateOperator.NOT_CONTAIN, None, False, True, False),
            (PredicateOperator.NOT_CONTAIN, 'select-1', True, True, False),
        ],
    )
    def test_check__checkbox(
        self,
        operator,
        predicate_value,
        is_selected_first,
        is_selected_second,
        result,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        first_task = workflow.tasks.first()
        second_task = workflow.tasks.last()
        first_field = TaskField.objects.create(
            name='Hero',
            api_name='hero-1',
            task=first_task,
            type=FieldType.CHECKBOX,
            value='',
            workflow=workflow,
        )
        FieldSelection.objects.create(
            field=first_field,
            api_name='select-1',
            value='1',
            is_selected=is_selected_first,
        )
        FieldSelection.objects.create(
            field=first_field,
            api_name='select-2',
            is_selected=is_selected_second,
            value='2',
        )

        condition = Condition.objects.create(
            task=second_task,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=first_rule,
            operator=operator,
            field_type=first_field.type,
            field=first_field.api_name,
            value=predicate_value,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is result

    @pytest.mark.parametrize(
        ('operator', 'predicate_value', 'field_value', 'result'),
        [
            (PredicateOperator.EQUAL, '1740087999', 'Captain Marvel', False),
            (PredicateOperator.EQUAL, '1740087999', 1740087999, True),
            (PredicateOperator.EQUAL, None, '1740087999', False),
            (PredicateOperator.EQUAL, '1740087999', '1740087999', True),
            (PredicateOperator.NOT_EQUAL, 'Captain Marvel', '', False),
            (PredicateOperator.NOT_EQUAL, '1740087999', '1740087999', False),
            (PredicateOperator.NOT_EQUAL, '1740087999', '1740087998', True),
            (PredicateOperator.EXIST, None, 'Captain Marvel', False),
            (PredicateOperator.EXIST, None, '1740087999', True),
            (PredicateOperator.NOT_EXIST, None, 'C', True),
            (PredicateOperator.MORE_THAN, '1740087999', '1740097999', True),
            (PredicateOperator.MORE_THAN, '1740087999', '1740077999', False),
            (PredicateOperator.LESS_THAN, '1740087999', '1740097999', False),
            (PredicateOperator.LESS_THAN, '1740087999', '1740077999', True),
        ],
    )
    def test_check__date(
        self,
        operator,
        predicate_value,
        field_value,
        result,
    ):
        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        first_task = workflow.tasks.first()
        second_task = workflow.tasks.last()
        first_field = TaskField.objects.create(
            name='Hero',
            api_name='hero-1',
            task=first_task,
            type=FieldType.DATE,
            value=field_value,
            workflow=workflow,
        )
        condition = Condition.objects.create(
            task=second_task,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=first_rule,
            operator=operator,
            field_type=first_field.type,
            field=first_field.api_name,
            value=predicate_value,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is result

    @pytest.mark.parametrize(
        ('operator', 'predicate_value', 'field_value', 'result'),
        [
            (
                PredicateOperator.EQUAL,
                'test@pneumatic.app',
                'second_test@pneumatic.app',
                False,
            ),
            (
                PredicateOperator.EQUAL,
                'test@pneumatic.app',
                'test@pneumatic.app',
                True,
            ),
            (PredicateOperator.EQUAL, None, 'test@pneumatic.app', False),
            (PredicateOperator.NOT_EQUAL, 'Captain Marvel', '', False),
            (PredicateOperator.NOT_EQUAL, '03/23/2021', '03/23/2021', False),
            (PredicateOperator.EXIST, None, 'test@pneumatic.app', True),
        ],
    )
    def test_check__user(
        self,
        operator,
        predicate_value,
        field_value,
        result,
    ):
        # arrange
        user = create_test_user()
        create_test_user(
            email='second_test@pneumatic.app',
            account=user.account,
        )
        create_test_user(email='another@pneumatic.app')
        workflow = create_test_workflow(user, tasks_count=2)
        first_task = workflow.tasks.first()
        second_task = workflow.tasks.last()
        selected_user = UserModel.objects.filter(email=field_value).first()
        predicate_user = UserModel.objects.filter(
            email=predicate_value,
        ).first()
        first_field = TaskField.objects.create(
            name='Hero',
            api_name='hero-1',
            task=first_task,
            type=FieldType.USER,
            value=selected_user.get_full_name() if selected_user else '',
            workflow=workflow,
            user_id=selected_user.id if selected_user else None,
        )
        condition = Condition.objects.create(
            task=second_task,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=first_rule,
            operator=operator,
            field_type=first_field.type,
            field=first_field.api_name,
            value=predicate_user.id if predicate_user else None,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is result

    @pytest.mark.parametrize(
        ('operator', 'predicate_value', 'field_value', 'result'),
        [
            (PredicateOperator.EQUAL, '1', 1, True),
            (PredicateOperator.EQUAL, '1', 2, False),
            (PredicateOperator.EQUAL, None, 1, False),
            (PredicateOperator.NOT_EQUAL, '1', 2, True),
            (PredicateOperator.NOT_EQUAL, '1', 1, False),
            (PredicateOperator.EXIST, None, 1, True),
            (PredicateOperator.EXIST, None, None, False),
            (PredicateOperator.NOT_EXIST, None, None, True),
            (PredicateOperator.NOT_EXIST, None, 1, False),
        ],
    )
    def test_check__group(
        self,
        operator,
        predicate_value,
        field_value,
        result,
    ):
        # arrange
        user = create_test_owner()
        workflow = create_test_workflow(user, tasks_count=2)
        first_task = workflow.tasks.get(number=1)
        second_task = workflow.tasks.get(number=2)
        first_field = TaskField.objects.create(
            name='Group',
            api_name='group-1',
            task=first_task,
            type=FieldType.USER,
            value=str(field_value) if field_value else '',
            workflow=workflow,
            group_id=field_value,
        )
        condition = Condition.objects.create(
            task=second_task,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=first_rule,
            operator=operator,
            field_type=PredicateType.GROUP,
            field=first_field.api_name,
            value=predicate_value,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is result

    def test_check__task_completed__return_true(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        task_1 = workflow.tasks.get(number=1)
        task_1.status = TaskStatus.COMPLETED
        task_1.save()
        task_2 = workflow.tasks.get(number=2)
        condition = Condition.objects.create(
            task=task_2,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=rule,
            operator=PredicateOperator.COMPLETED,
            field_type=PredicateType.TASK,
            field=task_1.api_name,
            value=None,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is True

    def test_check__task_not_completed__return_false(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=2)
        task_1 = workflow.tasks.get(number=1)
        task_2 = workflow.tasks.get(number=2)
        condition = Condition.objects.create(
            task=task_2,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=rule,
            operator=PredicateOperator.COMPLETED,
            field_type=PredicateType.TASK,
            field=task_1.api_name,
            value=None,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is False

    def test_check__kickoff_completed__return_true(self):

        # arrange
        user = create_test_user()
        workflow = create_test_workflow(user, tasks_count=1)
        task_1 = workflow.tasks.get(number=1)
        condition = Condition.objects.create(
            task=task_1,
            action=ConditionAction.SKIP_TASK,
            order=1,
        )
        rule = Rule.objects.create(
            condition=condition,
        )
        Predicate.objects.create(
            rule=rule,
            operator=PredicateOperator.COMPLETED,
            field_type=PredicateType.KICKOFF,
            field=None,
            value=None,
        )

        # act
        response = ConditionCheckService.check(condition, workflow.id)

        # assert
        assert response is True
