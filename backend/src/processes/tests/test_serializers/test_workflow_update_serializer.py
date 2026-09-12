from datetime import timedelta

import pytest
from django.utils import timezone

from src.processes.serializers.workflows.workflow import (
    WorkflowUpdateSerializer,
)
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_workflow,
)

pytestmark = pytest.mark.django_db


def test_get_changed_fields__new_name__name():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        name='Onboarding',
        name_template='Onboarding',
    )
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'name': 'Offboarding'},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == ['name']


def test_get_changed_fields__name_equals_name_template__empty():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        name='Onboarding',
        name_template='Onboarding',
    )
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'name': 'Onboarding'},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == []


def test_get_changed_fields__name_equals_name_not_template__name():

    """ update() writes the name into name_template: that is what the
        sent name is compared with, not the rendered name. """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        name='Order Acme',
        name_template='Order {{ client }}',
    )
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'name': 'Order Acme'},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == ['name']


def test_get_changed_fields__new_due_date__due_date():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    due_date = timezone.now() + timedelta(days=1)
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'due_date_tsp': due_date.timestamp()},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == ['due_date']


def test_get_changed_fields__same_due_date__empty():

    # arrange
    owner = create_test_owner()
    due_date = (timezone.now() + timedelta(days=1)).replace(microsecond=0)
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        due_date=due_date,
    )
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'due_date_tsp': due_date.timestamp()},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == []


def test_get_changed_fields__null_due_date_on_due_date__due_date():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        due_date=timezone.now() + timedelta(days=1),
    )
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'due_date_tsp': None},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == ['due_date']


def test_get_changed_fields__null_due_date_without_due_date__empty():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'due_date_tsp': None},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == []


def test_get_changed_fields__is_urgent_changed__is_urgent():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        is_urgent=True,
    )
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'is_urgent': False},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == ['is_urgent']


def test_get_changed_fields__same_is_urgent__empty():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(
        user=owner,
        tasks_count=1,
        is_urgent=True,
    )
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'is_urgent': True},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == []


def test_get_changed_fields__kickoff_sent__kickoff():

    """ update() writes every field of the kickoff it gets, so a sent
        kickoff is named without comparing its values. """

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'kickoff': {'client': 'Acme'}},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == ['kickoff']


def test_get_changed_fields__empty_kickoff__empty():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={'kickoff': {}},
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == []


def test_get_changed_fields__empty_data__empty():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    slz = WorkflowUpdateSerializer(instance=workflow, data={})
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == []


def test_get_changed_fields__all_changed__fixed_order():

    # arrange
    owner = create_test_owner()
    workflow = create_test_workflow(user=owner, tasks_count=1)
    due_date = timezone.now() + timedelta(days=1)
    slz = WorkflowUpdateSerializer(
        instance=workflow,
        data={
            'kickoff': {'client': 'Acme'},
            'is_urgent': True,
            'due_date_tsp': due_date.timestamp(),
            'name': 'Renamed workflow',
        },
    )
    slz.is_valid(raise_exception=True)

    # act
    result = slz.get_changed_fields()

    # assert
    assert result == ['name', 'due_date', 'is_urgent', 'kickoff']
