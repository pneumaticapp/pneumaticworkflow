from src.ai.providers import ai_performers_active
from src.processes.enums import PerformerType
from src.processes.models.workflows.task import TaskPerformer


def dispatch_ai_performers(task, is_returned: bool = False):

    """ Dispatch a background run for every active AI performer on
        the task. Safe to call repeatedly: a run is claimed with an
        atomic QUEUED -> RUNNING transition, so finished or in-flight
        runs are never re-executed. A returned task resets existing
        runs so agents retry with the corrected inputs """

    if not ai_performers_active(task.account):
        return
    agent_ids = list(
        TaskPerformer.objects
        .by_task(task.id)
        .exclude_directly_deleted()
        .not_completed()
        .filter(
            type=PerformerType.AI,
            ai_agent__isnull=False,
            ai_agent__is_deleted=False,
            ai_agent__is_active=True,
        )
        .values_list('ai_agent_id', flat=True),
    )
    if not agent_ids:
        return
    # local imports: src.ai.tasks -> src.ai.services -> processes services
    from src.ai.models import AITaskRun
    from src.ai.tasks import run_ai_performer
    if is_returned:
        AITaskRun.objects.filter(
            task=task,
            agent_id__in=agent_ids,
        ).delete()
    for agent_id in agent_ids:
        run_ai_performer.delay(task_id=task.id, agent_id=agent_id)
