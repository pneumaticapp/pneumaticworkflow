from io import StringIO

import pytest
from django.core.management import call_command
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from src.logs.enums import LogsBackend

pytestmark = pytest.mark.django_db


def test_handle__logs_disabled__consumer_task_created(settings):

    """ The task is registered whatever LOGS_BACKEND is: with the
        journal off it returns on its first line. """

    # arrange
    settings.LOGS_BACKEND = LogsBackend.NONE
    stdout = StringIO()

    # act
    call_command('init_periodic_tasks', stdout=stdout)

    # assert
    task = PeriodicTask.objects.get(
        task='src.logs.events.tasks.consume_events',
    )
    assert task.name == 'Deliver events to log backend'
    assert task.interval.every == 5
    assert task.interval.period == IntervalSchedule.SECONDS
