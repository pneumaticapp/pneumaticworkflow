import base64
from typing import Dict

# Downloads larger than this are not even offered to the model
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
# Extracted text is cut here so one huge document can't blow
# the context window
MAX_EXTRACTED_CHARS = 80_000

IMAGE_TYPES = frozenset({
    'image/png',
    'image/jpeg',
    'image/webp',
    'image/gif',
})

TEXT_TYPES = frozenset({
    'application/json',
    'application/xml',
    'application/x-yaml',
})

EXTENSION_TYPES = {
    'txt': 'text/plain',
    'md': 'text/markdown',
    'csv': 'text/csv',
    'json': 'application/json',
    'xml': 'application/xml',
    'yaml': 'application/x-yaml',
    'yml': 'application/x-yaml',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp',
    'gif': 'image/gif',
    'pdf': 'application/pdf',
}


def _effective_type(name: str, content_type: str) -> str:

    """ The file service stores unknown uploads as
        application/octet-stream, so the filename extension is the
        tiebreaker when the content type says nothing """

    if content_type and content_type != 'application/octet-stream':
        return content_type.split(';')[0].strip().lower()
    extension = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    return EXTENSION_TYPES.get(extension, content_type or '')


def _truncate(text: str) -> str:
    if len(text) <= MAX_EXTRACTED_CHARS:
        return text
    return (
        f'{text[:MAX_EXTRACTED_CHARS]}\n'
        f'[… document truncated at {MAX_EXTRACTED_CHARS} characters]'
    )


def extract_content(name: str, content_type: str, data: bytes) -> Dict:

    """ Turns a downloaded attachment into something a model can
        consume: text, an image data URL for vision input, or an
        "unsupported" entry the model is told about.

        PDF and docx extraction needs libraries the backend does not
        carry yet — those formats are disclosed as unreadable for now.
    """

    if len(data) > MAX_ATTACHMENT_BYTES:
        megabytes = round(len(data) / 1024 / 1024)
        return {
            'kind': 'unsupported',
            'reason': f'too large ({megabytes} MB)',
        }

    file_type = _effective_type(name, content_type)

    if file_type in IMAGE_TYPES:
        encoded = base64.b64encode(data).decode('ascii')
        return {
            'kind': 'image',
            'data_url': f'data:{file_type};base64,{encoded}',
        }
    if file_type.startswith('text/') or file_type in TEXT_TYPES:
        return {
            'kind': 'text',
            'text': _truncate(data.decode('utf-8', errors='replace')),
        }
    return {
        'kind': 'unsupported',
        'reason': f'unreadable type "{file_type or "unknown"}"',
    }


def render_attachment(attachment: Dict) -> str:
    name = attachment['name']
    if attachment['kind'] == 'text':
        return '\n'.join((
            f'--- Attached document: {name} ---',
            attachment['text'],
            f'--- End of {name} ---',
        ))
    if attachment['kind'] == 'image':
        return f'The image "{name}" is attached to this message.'
    reason = attachment['reason']
    return (
        f'(The attached document "{name}" could not be read: {reason}.)'
    )
