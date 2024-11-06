import pytest
from django.contrib.auth import get_user_model

from pneumatic_backend.processes.models import (
    Condition,
    Rule,
    Predicate,
    TaskField,
    FieldSelection,
    FileAttachment,
)
from pneumatic_backend.processes.services.condition_check.service import (
    ConditionCheckService,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_workflow,
)
from pneumatic_backend.processes.enums import (
    FieldType,
    PredicateOperator
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class TestConditionCheckService:
    @pytest.mark.parametrize(
        ('operator', 'predicate_value', 'field_value', 'result'),
        [
            (
                PredicateOperator.EQUAL,
                'Captain Marvel', 'Captain Marvel', True
            ),
            (
                PredicateOperator.EQUAL,
                'Captain Marvel', 'CaptainMarvel', False
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
                    'Captain Marvel', 'Iran Many', True
            ),
        ]
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
            workflow=workflow
        )
        condition = Condition.objects.create(
            task=second_task,
            action=Condition.SKIP_TASK,
            order=1,
            template_id=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
            template_id=1,
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
        ]
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
            workflow=workflow
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
            action=Condition.SKIP_TASK,
            order=1,
            template_id=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
            template_id=1,
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
        ]
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
            workflow=workflow
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
            action=Condition.SKIP_TASK,
            order=1,
            template_id=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
            template_id=1,
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
        ]
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
            workflow=workflow
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
            action=Condition.SKIP_TASK,
            order=1,
            template_id=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
            template_id=1,
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
            (PredicateOperator.EQUAL, '03/23/2021', 'Captain Marvel', False),
            (PredicateOperator.EQUAL, '03/23/2021', '2021-03-23', True),
            (PredicateOperator.EQUAL, None, '03/23/2021', False),
            (PredicateOperator.EQUAL, '03/23/2021', '03/23/2021', True),
            (PredicateOperator.NOT_EQUAL, 'Captain Marvel', '', False),
            (PredicateOperator.NOT_EQUAL, '03/23/2021', '03/23/2021', False),
            (PredicateOperator.NOT_EQUAL, '02/23/2021', '03/23/2021', True),
            (PredicateOperator.EXIST, None, 'Captain Marvel', False),
            (PredicateOperator.EXIST, None, '03/23/2021', True),
            (PredicateOperator.NOT_EXIST, None, 'C', True),
            (PredicateOperator.MORE_THAN, '02/23/2021', '03/23/2021', True),
            (PredicateOperator.MORE_THAN, '03/23/2021', '02/23/2021', False),
            (PredicateOperator.LESS_THAN, '02/23/2021', '03/23/2021', False),
            (PredicateOperator.LESS_THAN, '03/23/2021', '02/23/2021', True),
        ]
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
            workflow=workflow
        )
        condition = Condition.objects.create(
            task=second_task,
            action=Condition.SKIP_TASK,
            order=1,
            template_id=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
            template_id=1,
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
        ]
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
            email=predicate_value
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
            action=Condition.SKIP_TASK,
            order=1,
            template_id=1,
        )
        first_rule = Rule.objects.create(
            condition=condition,
            template_id=1,
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
