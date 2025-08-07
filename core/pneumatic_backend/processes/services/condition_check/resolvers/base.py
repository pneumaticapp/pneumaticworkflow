from pneumatic_backend.processes.models import Predicate
from ..comparator import Comparator
from pneumatic_backend.processes.enums import PredicateOperator


class Resolver:
    predicate_value = None
    field_value = None
    _predicate = None
    _workflow_id = None

    def __init__(self, predicate: Predicate, workflow_id: int):
        self._predicate = predicate
        self._workflow_id = workflow_id
        self._prepare_args()

    def _prepare_args(self):
        raise NotImplementedError

    def resolve(self):
        method = getattr(Comparator, self._predicate.operator)
        if self._predicate.operator in PredicateOperator.UNARY_OPERATORS:
            return method(self.field_value)

        return method(self.field_value, self.predicate_value)
