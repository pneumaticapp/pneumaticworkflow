from src.processes.enums import PredicateOperator
from src.processes.models.workflows.conditions import Predicate
from src.processes.models.workflows.fields import TaskField
from src.processes.services.condition_check.comparator import Comparator


class Resolver:
    predicate_value = None
    field_value = None
    _predicate = None
    _workflow_id = None

    def __init__(self, predicate: Predicate, workflow_id: int):
        self._predicate = predicate
        self._workflow_id = workflow_id
        self._prepare_args()

    def _get_field(self) -> TaskField:

        """ Matched by workflow, not by task or kickoff: a field inside
            a fieldset is linked to neither of them. """

        return TaskField.objects.get(
            workflow_id=self._workflow_id,
            api_name=self._predicate.field,
        )

    def _prepare_args(self):
        raise NotImplementedError

    def resolve(self):
        method = getattr(Comparator, self._predicate.operator)
        if self._predicate.operator in PredicateOperator.UNARY_OPERATORS:
            return method(self.field_value)

        return method(self.field_value, self.predicate_value)
