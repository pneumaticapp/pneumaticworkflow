from io import StringIO

import pytest
from django.core.management import call_command
from django_celery_beat.models import IntervalSchedule, PeriodicTask

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'task_path, task_name, interval',
    (
        (
            'src.logs.events.tasks.consume_events',
            'Deliver events to log backend',
            5,
        ),
        (
            'src.ai.tasks.dispatch_ai_agent_new_tasks',
            'Dispatch AI agent tasks',
            30,
        ),
        (
            'src.ai.tasks.dispatch_ai_agent_new_notifications',
            'Dispatch AI agent mentions',
            10,
        ),
    ),
)
def test_handle__ok__periodic_task_created(task_path, task_name, interval):

    # arrange
    stdout = StringIO()

    # act
    call_command('init_periodic_tasks', stdout=stdout)

    # assert
    task = PeriodicTask.objects.get(task=task_path)
    assert task.name == task_name
    assert task.interval.every == interval
    assert task.interval.period == IntervalSchedule.SECONDS
