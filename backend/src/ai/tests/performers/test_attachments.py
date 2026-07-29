import base64
import zipfile
from io import BytesIO

from src.ai.performers.attachments import (
    DOCX_TYPE,
    MAX_ATTACHMENT_BYTES,
    MAX_EXTRACTED_CHARS,
    extract_content,
    render_attachment,
)


def _minimal_pdf(text: str) -> bytes:

    """ A one-page PDF built by hand — enough for pdfminer to parse """

    stream = f'BT /F1 12 Tf 72 720 Td ({text}) Tj ET'.encode()
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        (
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
            b'/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>'
        ),
        b'<< /Length %d >>\nstream\n%s\nendstream' % (len(stream), stream),
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ]
    out = bytearray(b'%PDF-1.4\n')
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b'%d 0 obj\n%s\nendobj\n' % (number, obj)
    xref_pos = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objects) + 1)
    for offset in offsets:
        out += b'%010d 00000 n \n' % offset
    out += (
        b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF'
        % (len(objects) + 1, xref_pos)
    )
    return bytes(out)


def _minimal_docx(text: str) -> bytes:
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/'
        'wordprocessingml/2006/main">'
        f'<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>'
        '</w:document>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
        'content-types">'
        '<Default Extension="rels" ContentType="application/'
        'vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType='
        '"application/vnd.openxmlformats-officedocument.'
        'wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/'
        'package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
        'officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        '</Relationships>'
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('[Content_Types].xml', content_types)
        archive.writestr('_rels/.rels', rels)
        archive.writestr('word/document.xml', document)
    return buffer.getvalue()


def test_extract_content__plain_text__verbatim():
    result = extract_content(
        name='notes.txt',
        content_type='text/plain',
        data=b'hello world',
    )

    assert result == {'kind': 'text', 'text': 'hello world'}


def test_extract_content__long_text__truncated():
    result = extract_content(
        name='big.txt',
        content_type='text/plain',
        data=b'x' * (MAX_EXTRACTED_CHARS + 100),
    )

    assert result['kind'] == 'text'
    assert 'document truncated' in result['text']
    assert len(result['text']) < MAX_EXTRACTED_CHARS + 100


def test_extract_content__image__data_url():
    data = b'\x89PNG fake bytes'

    result = extract_content(
        name='chart.png',
        content_type='image/png',
        data=data,
    )

    assert result['kind'] == 'image'
    encoded = base64.b64encode(data).decode('ascii')
    assert result['data_url'] == f'data:image/png;base64,{encoded}'


def test_extract_content__octet_stream_with_md_extension__text():
    result = extract_content(
        name='README.md',
        content_type='application/octet-stream',
        data=b'# title',
    )

    assert result == {'kind': 'text', 'text': '# title'}


def test_extract_content__content_type_with_charset__text():
    result = extract_content(
        name='data.csv',
        content_type='text/csv; charset=utf-8',
        data=b'a,b',
    )

    assert result == {'kind': 'text', 'text': 'a,b'}


def test_extract_content__too_large__unsupported():
    result = extract_content(
        name='huge.txt',
        content_type='text/plain',
        data=b'x' * (MAX_ATTACHMENT_BYTES + 1),
    )

    assert result['kind'] == 'unsupported'
    assert 'too large' in result['reason']


def test_extract_content__pdf__text_extracted():
    result = extract_content(
        name='contract.pdf',
        content_type='application/pdf',
        data=_minimal_pdf('Twelve month term'),
    )

    assert result['kind'] == 'text'
    assert 'Twelve month term' in result['text']


def test_extract_content__pdf_octet_stream_extension__text_extracted():
    result = extract_content(
        name='contract.pdf',
        content_type='application/octet-stream',
        data=_minimal_pdf('Renewal clause'),
    )

    assert result['kind'] == 'text'
    assert 'Renewal clause' in result['text']


def test_extract_content__broken_pdf__unsupported():
    result = extract_content(
        name='contract.pdf',
        content_type='application/pdf',
        data=b'not really a pdf at all',
    )

    assert result['kind'] == 'unsupported'
    assert 'could not be parsed' in result['reason']


def test_extract_content__docx__text_extracted():
    result = extract_content(
        name='resume.docx',
        content_type=DOCX_TYPE,
        data=_minimal_docx('Senior Python developer'),
    )

    assert result['kind'] == 'text'
    assert 'Senior Python developer' in result['text']


def test_extract_content__docx_octet_stream_extension__text_extracted():
    result = extract_content(
        name='resume.docx',
        content_type='application/octet-stream',
        data=_minimal_docx('Ten years of experience'),
    )

    assert result['kind'] == 'text'
    assert 'Ten years of experience' in result['text']


def test_extract_content__broken_docx__unsupported():
    result = extract_content(
        name='resume.docx',
        content_type=DOCX_TYPE,
        data=b'not a zip archive',
    )

    assert result['kind'] == 'unsupported'
    assert 'could not be parsed' in result['reason']


def test_extract_content__legacy_doc__unsupported():
    result = extract_content(
        name='resume.doc',
        content_type='application/msword',
        data=b'\xd0\xcf\x11\xe0 legacy binary',
    )

    assert result['kind'] == 'unsupported'
    assert 'application/msword' in result['reason']


def test_extract_content__unknown_binary__unsupported():
    result = extract_content(
        name='archive.zip',
        content_type='application/zip',
        data=b'PK',
    )

    assert result['kind'] == 'unsupported'


def test_render_attachment__text__delimited_section():
    rendered = render_attachment({
        'kind': 'text',
        'name': 'notes.txt',
        'text': 'content here',
    })

    assert rendered == (
        '--- Attached document: notes.txt ---\n'
        'content here\n'
        '--- End of notes.txt ---'
    )


def test_render_attachment__image__mentioned():
    rendered = render_attachment({
        'kind': 'image',
        'name': 'chart.png',
        'data_url': 'data:image/png;base64,x',
    })

    assert rendered == 'The image "chart.png" is attached to this message.'


def test_render_attachment__unsupported__disclosed():
    rendered = render_attachment({
        'kind': 'unsupported',
        'name': 'archive.zip',
        'reason': 'unreadable type "application/zip"',
    })

    assert 'archive.zip' in rendered
    assert 'could not be read' in rendered
