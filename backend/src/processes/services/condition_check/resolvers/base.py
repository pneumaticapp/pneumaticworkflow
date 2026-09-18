import logging
from typing import Optional

from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist,
)

from src.processes.enums import PredicateOperator
from src.processes.models.workflows.conditions import Predicate
from src.processes.models.workflows.fields import TaskField
from src.processes.services.condition_check.comparator import (
    Comparator,
)

logger = logging.getLogger(__name__)


class Resolver:
    predicate_value = None
    field_value = None
    _predicate = None
    _workflow_id = None
    _field = None

    def __init__(
        self,
        predicate: Predicate,
        workflow_id: int,
        field: Optional[TaskField] = None,
    ):
        self._predicate = predicate
        self._workflow_id = workflow_id
        self._field = field
        self._field_missing = False
        try:
            self._prepare_args()
        except (AttributeError, TypeError, ValueError, ArithmeticError):
            self._field_missing = True

    def _get_field(self) -> Optional[TaskField]:

        """ Matched by workflow, not by task or kickoff: a field inside
            a fieldset is linked to neither of them. """

        if self._field is not None:
            return self._field
        try:
            return TaskField.objects.get(
                workflow_id=self._workflow_id,
                api_name=self._predicate.field,
            )
        except ObjectDoesNotExist:
            logger.warning(
                'Condition field %s not found in workflow %s',
                self._predicate.field,
                self._workflow_id,
            )
            return None
        except MultipleObjectsReturned:
            logger.warning(
                'Duplicate field %s in workflow %s, '
                'using first match',
                self._predicate.field,
                self._workflow_id,
            )
            return TaskField.objects.filter(
                workflow_id=self._workflow_id,
                api_name=self._predicate.field,
            ).first()

    def _prepare_args(self):
        raise NotImplementedError

    def resolve(self):
        if self._field_missing:
            return False
        method = getattr(Comparator, self._predicate.operator)
        if self._predicate.operator in PredicateOperator.UNARY_OPERATORS:
            return method(self.field_value)

        return method(self.field_value, self.predicate_value)
