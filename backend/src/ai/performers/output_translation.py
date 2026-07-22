import logging
import math
import re
from datetime import (
    datetime,
    timezone,
)
from typing import (
    Any,
    Dict,
    List,
    Union,
)
from urllib.parse import urlparse

from src.ai.performers.output_fields import (
    STRING_MAX_LENGTH,
    OutputField,
    is_choice_type,
)
from src.processes.enums import FieldType

logger = logging.getLogger(__name__)


class IncompleteOutputError(Exception):

    """The model left a required field unusable, so the task can't be
    completed."""

    def __init__(self, problems: List[str]):
        super().__init__(f'model output unusable: {"; ".join(problems)}')
        self.problems = problems


_BARE_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# A file value reaching this point was already rewritten by the
# document-generation step into markdown links; anything else is a bug
# upstream.
_MARKDOWN_LINK = re.compile(r'^\[[^\]]+\]\(https?://\S+\)$')


def _is_blank(value: Any) -> bool:
    return value is None or (
        isinstance(value, str) and value.strip() == ''
    )


def _to_timestamp(value: Any) -> float:
    # Pneumatic wants a Unix timestamp; the model is asked for an
    # ISO 8601 date. A bare date is pinned to noon UTC — midnight
    # renders as the previous day in any timezone west of UTC.
    text = str(value).strip()
    if _BARE_DATE.match(text):
        text = f'{text}T12:00:00+00:00'
    elif text.endswith('Z'):
        text = f'{text[:-1]}+00:00'
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(
            f'not an ISO 8601 date: {value!r}',
        ) from None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _to_url(value: Any) -> str:
    text = str(value).strip()
    parsed = urlparse(text)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f'not an absolute URL: {value!r}')
    return text


def _to_number(value: Any) -> Union[int, float]:
    if isinstance(value, bool):
        raise ValueError(f'not a number: {value!r}')
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'not a number: {value!r}') from None
    if not math.isfinite(parsed):
        raise ValueError(f'not a number: {value!r}')
    if isinstance(value, (int, float)):
        return value
    return int(parsed) if parsed.is_integer() else parsed


def _to_file_links(value: Any) -> List[str]:
    links = value if isinstance(value, list) else [value]
    valid = links and all(
        isinstance(link, str) and _MARKDOWN_LINK.match(link)
        for link in links
    )
    if not valid:
        raise ValueError(
            f'not an array of [name](url) links: {str(value)[:120]}',
        )
    return links


def _to_selection_value(field: OutputField, value: Any) -> str:
    # Task completion validates choice fields against the selections'
    # *display values* and stores the value string directly — so a
    # valid display value passes through as-is.
    if value not in field.selections:
        raise ValueError(
            f'{value!r} is not one of: {", ".join(field.selections)}',
        )
    return value


def _coerce(field: OutputField, value: Any) -> Any:
    if field.type == FieldType.STRING:
        # The schema can only *ask* for the limit; Pneumatic errors
        # past it, so the value is hard-truncated here.
        return str(value)[:STRING_MAX_LENGTH]
    if field.type == FieldType.TEXT:
        return str(value)
    if field.type == FieldType.URL:
        return _to_url(value)
    if field.type == FieldType.DATE:
        return _to_timestamp(value)
    if field.type == FieldType.NUMBER:
        return _to_number(value)
    if field.type in FieldType.TYPES_WITH_SELECTION:
        return _to_selection_value(field, value)
    if field.type == FieldType.CHECKBOX:
        if not isinstance(value, list):
            raise ValueError(f'expected an array, got {value!r}')
        return [_to_selection_value(field, entry) for entry in value]
    if field.type == FieldType.FILE:
        return _to_file_links(value)
    raise ValueError(f'unsupported field type "{field.type}"')


def to_pneumatic_output(
    fields: List[OutputField],
    data: Dict[str, Any],
) -> Dict[str, Any]:

    """Translates the model's JSON (keyed by field api_name, choice
    fields as display values) into the fields_values shape task
    completion expects.

    Optional fields the model skipped, or filled with something
    unusable, are dropped. The same problem on a required field fails
    the whole task, which is left active for a human rather than
    completed with a hole in it."""

    output = {}
    problems = []

    for field in fields:
        raw = (data or {}).get(field.api_name)

        # A checkbox with nothing ticked is blank, not an empty
        # selection.
        blank = _is_blank(raw) or (
            is_choice_type(field.type)
            and isinstance(raw, list)
            and not raw
        )
        if blank:
            if field.is_required:
                problems.append(
                    f'required field "{field.name}" was left empty',
                )
            continue

        try:
            output[field.api_name] = _coerce(field, raw)
        except ValueError as ex:
            if field.is_required:
                problems.append(
                    f'required field "{field.name}": {ex}',
                )
            else:
                logger.warning(
                    'dropping optional field "%s": %s', field.name, ex,
                )

    if problems:
        raise IncompleteOutputError(problems)
    return output
