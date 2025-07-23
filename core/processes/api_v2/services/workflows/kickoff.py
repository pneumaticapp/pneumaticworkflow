from pneumatic_backend.processes.api_v2.services.base import (
    BaseWorkflowService,
)
from pneumatic_backend.processes.models import (
    KickoffValue,
)


class KickoffService(BaseWorkflowService):

    def _create_instance(
        self,
        instance_template: KickoffValue,
        **kwargs
    ):

        # TODO move from KickoffCreateSerializer

        pass

    def _create_related(
        self,
        instance_template: KickoffValue,
        **kwargs
    ):
        pass
