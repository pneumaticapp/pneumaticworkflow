import base64
from io import BytesIO
from typing import Dict

import mammoth
from pdfminer.high_level import extract_text as pdf_extract_text

# Downloads larger than this are not even offered to the model
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
# Extracted text is cut here so one huge document can't blow
# the context window
MAX_EXTRACTED_CHARS = 80_000

PDF_TYPE = 'application/pdf'
DOCX_TYPE = (
    'application/vnd.openxmlformats-officedocument.'
    'wordprocessingml.document'
)

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
    'pdf': PDF_TYPE,
    'docx': DOCX_TYPE,
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


def _extract_pdf(data: bytes) -> Dict:
    try:
        text = pdf_extract_text(BytesIO(data))
    except Exception:  # noqa: BLE001 — extraction must never crash a run
        return {
            'kind': 'unsupported',
            'reason': 'the PDF could not be parsed',
        }
    text = text.strip()
    if not text:
        # A PDF of page images has no text layer to extract
        return {
            'kind': 'unsupported',
            'reason': (
                'the PDF contains no extractable text '
                '(a scanned document?)'
            ),
        }
    return {'kind': 'text', 'text': _truncate(text)}


def _extract_docx(data: bytes) -> Dict:
    try:
        result = mammoth.convert_to_markdown(BytesIO(data))
        text = result.value.strip()
    except Exception:  # noqa: BLE001 — extraction must never crash a run
        return {
            'kind': 'unsupported',
            'reason': 'the Word document could not be parsed',
        }
    if not text:
        return {
            'kind': 'unsupported',
            'reason': 'the Word document contains no text',
        }
    return {'kind': 'text', 'text': _truncate(text)}


def extract_content(name: str, content_type: str, data: bytes) -> Dict:

    """ Turns a downloaded attachment into something a model can
        consume: text (verbatim, or extracted from PDF/docx), an image
        data URL for vision input, or an "unsupported" entry the model
        is told about. """

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
    if file_type == PDF_TYPE:
        return _extract_pdf(data)
    if file_type == DOCX_TYPE:
        return _extract_docx(data)
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
