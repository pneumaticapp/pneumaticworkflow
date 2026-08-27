from pathlib import Path

import pytest
from celery.bin.celery import celery as celery_cli
from celery.states import SUCCESS
from click.testing import CliRunner

from src.accounts.tasks import process_vacations
from src.processes.tasks.delay import continue_delayed_workflows
from src.storage.tasks import sync_workflow_attachment_permissions

pytestmark = pytest.mark.django_db


def test_beat__pidfile_as_global_option__error():

    """ Celery 5 rejects --pidfile before the beat command. """

    # arrange
    runner = CliRunner()

    # act
    result = runner.invoke(
        celery_cli,
        ['--pidfile=', 'beat'],
    )

    # assert
    error_line = result.output.splitlines()[-1]
    assert result.exit_code == 2
    assert error_line == 'Error: No such option: --pidfile'


def test_beat__compose_options__help_ok():

    """ Compose beat flags are valid Celery 5 beat options. """

    # arrange
    runner = CliRunner()

    # act
    result = runner.invoke(
        celery_cli,
        ['beat', '-l', 'warning', '-S', 'django', '--help'],
    )

    # assert
    usage_line = result.output.splitlines()[0]
    assert result.exit_code == 0
    assert usage_line == 'Usage: celery beat [OPTIONS]'


@pytest.mark.parametrize(
    'relative_path',
    (
        'docker-compose.yml',
        'docker-compose.src.yml',
        'backend/docker-compose.yml',
        'frontend/docker-compose.yml',
    ),
)
def test_beat_command__compose_file__celery5_argv(relative_path):

    """ Beat argv must not put --pidfile before the beat command. """

    # arrange
    backend_dir = Path(__file__).resolve().parents[4]
    compose_file = backend_dir.parent / relative_path
    if (
        not compose_file.is_file()
        and relative_path == 'backend/docker-compose.yml'
    ):
        compose_file = backend_dir / 'docker-compose.yml'
    if not compose_file.is_file():
        pytest.skip('Compose file is not in the test image.')
    expected = (
        'celery --app src.celery_app:app beat -l warning -S django'
    )

    # act
    content = compose_file.read_text()

    # assert
    assert 'celery --pidfile=' not in content
    assert expected in content


def test_sync_workflow_attachment_permissions__missing_wf__ok():

    """ Missing workflow is a no-op, not a worker crash. """

    # arrange
    workflow_id = -1

    # act
    result = sync_workflow_attachment_permissions.apply(
        args=(workflow_id,),
    )

    # assert
    assert result.status == SUCCESS


def test_continue_delayed_workflows__empty_queue__ok():

    """ Beat delay task runs against an empty queue. """

    # arrange
    task = continue_delayed_workflows

    # act
    result = task.apply()

    # assert
    assert result.status == SUCCESS


def test_process_vacations__no_vacations__ok():

    """ Beat vacation task runs when nobody is on vacation. """

    # arrange
    task = process_vacations

    # act
    result = task.apply()

    # assert
    assert result.status == SUCCESS
