from celery import shared_task

from src.celery import periodic_lock
from src.processes.utils.workflows import (
    resume_delayed_workflows,
)


@shared_task(ignore_result=True)
def continue_delayed_workflows() -> None:
    with periodic_lock('continue_delayed_workflows') as acquired:
        if not acquired:
            return
        resume_delayed_workflows()
