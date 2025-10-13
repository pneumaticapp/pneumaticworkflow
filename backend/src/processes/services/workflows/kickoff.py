from src.processes.services.base import BaseWorkflowService
from src.processes.models.workflows.kickoff import KickoffValue


class KickoffService(BaseWorkflowService):

    def _create_instance(
        self,
        instance_template: KickoffValue,
        **kwargs,
    ):

        # TODO move from KickoffCreateSerializer

        pass

    def _create_related(
        self,
        instance_template: KickoffValue,
        **kwargs,
    ):
        pass
