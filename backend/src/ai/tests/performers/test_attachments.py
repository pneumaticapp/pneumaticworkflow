import base64

from src.ai.performers.attachments import (
    MAX_ATTACHMENT_BYTES,
    MAX_EXTRACTED_CHARS,
    extract_content,
    render_attachment,
)


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


def test_extract_content__pdf__unsupported_for_now():
    result = extract_content(
        name='contract.pdf',
        content_type='application/pdf',
        data=b'%PDF-1.4',
    )

    assert result['kind'] == 'unsupported'
    assert 'application/pdf' in result['reason']


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
