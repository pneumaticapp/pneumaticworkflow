import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from src.ai.services.performers import (
    AIPerformerService,
    AITransientError,
)

logger = logging.getLogger(__name__)

RETRY_BACKOFF_BASE_SEC = 30


@shared_task(bind=True, max_retries=5)
def run_ai_performer(self, task_id: int, agent_id: int):

    """ Execute one AI performer run for an active task.

        Dispatched from WorkflowActionService._start_ai_performers.
        Transient provider/network errors are retried with backoff;
        every other outcome is recorded on the AITaskRun row. """

    service = AIPerformerService.load(task_id=task_id, agent_id=agent_id)
    if service is None:
        return
    run = service.claim()
    if run is None:
        return
    try:
        service.run(run)
    except AITransientError as ex:
        countdown = 2 ** self.request.retries * RETRY_BACKOFF_BASE_SEC
        try:
            raise self.retry(exc=ex, countdown=countdown)
        except MaxRetriesExceededError:
            service.mark_failed(run, reason=str(ex))
