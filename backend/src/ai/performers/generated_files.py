import logging
import re
from typing import (
    Any,
    Callable,
    Dict,
    List,
)

from src.ai.performers.output_fields import OutputField
from src.ai.performers.output_translation import IncompleteOutputError
from src.processes.enums import FieldType

logger = logging.getLogger(__name__)

GENERATED_CONTENT_TYPE = 'text/markdown'

# The value becomes a "[filename](url)" markdown link, so the name must
# not be able to close the bracket early; path separators go too since
# this names a stored file.
_FORBIDDEN_CHARS = re.compile(r'[\[\]()\\/:*?"<>|\x00-\x1f\x7f-\x9f]')


def sanitize_filename(filename: Any, fallback: str) -> str:
    cleaned = _FORBIDDEN_CHARS.sub('', str(filename or '')).strip()
    name = cleaned or fallback
    if not name.lower().endswith('.md'):
        name = f'{name}.md'
    return name


def is_document(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get('filename'), str)
        and isinstance(value.get('content'), str)
        and value['content'].strip() != ''
    )


def resolve_generated_files(
    fields: List[OutputField],
    data: Dict[str, Any],
    upload: Callable[[str, str], str],
) -> Dict[str, Any]:

    """Uploads the documents the model wrote for file fields and
    rewrites those values into the ["[filename](public_url)"] shape
    task completion expects. Other fields pass through untouched for
    to_pneumatic_output.

    Shape problems follow the usual contract: a required field the
    model botched raises IncompleteOutputError (a rerun buys the same
    verdict), an optional one is dropped. Upload failures propagate —
    whether they deserve a retry is the caller's call."""

    resolved = dict(data or {})
    problems = []

    for field in fields:
        if field.type != FieldType.FILE:
            continue
        raw = resolved.get(field.api_name)
        if raw is None:
            continue

        if not is_document(raw):
            if field.is_required:
                problems.append(
                    f'required field "{field.name}" needs '
                    f'{{filename, content}}, got {str(raw)[:120]}',
                )
            else:
                logger.warning(
                    'dropping optional field "%s": not a '
                    '{filename, content} document',
                    field.name,
                )
                resolved[field.api_name] = None
            continue

        filename = sanitize_filename(
            raw['filename'],
            fallback=f'{field.api_name}.md',
        )
        public_url = upload(filename, raw['content'])
        resolved[field.api_name] = [f'[{filename}]({public_url})']

    if problems:
        raise IncompleteOutputError(problems)
    return resolved
