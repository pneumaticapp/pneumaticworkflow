"""Tests for Content-Type sanitization."""

import pytest

from src.shared_kernel.security import sanitize_content_type

# --- Allowed types passthrough ---


@pytest.mark.parametrize('content_type', [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'application/pdf',
    'text/plain',
    'text/csv',
    'video/mp4',
    'application/json',
    'application/octet-stream',
    'application/zip',
    'audio/mpeg',
])
def test_sanitize__allowed_type__passthrough(content_type):

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == content_type


# --- Blocked dangerous types ---


@pytest.mark.parametrize('content_type', [
    'text/html',
    'text/xml',
    'application/xhtml+xml',
    'application/javascript',
    'text/javascript',
    'image/svg+xml',
    'application/ecmascript',
    'application/x-javascript',
])
def test_sanitize__dangerous_type__blocked(content_type):

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == 'application/octet-stream'


# --- Edge cases ---


def test_sanitize__none__octet_stream():

    # act
    result = sanitize_content_type(content_type=None)

    # assert
    assert result == 'application/octet-stream'


def test_sanitize__empty__octet_stream():

    # act
    result = sanitize_content_type(content_type='')

    # assert
    assert result == 'application/octet-stream'


def test_sanitize__unknown__octet_stream():

    # arrange
    content_type = 'application/x-custom-dangerous'

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == 'application/octet-stream'


def test_sanitize__html_with_charset__blocked():

    # arrange
    content_type = 'text/html; charset=utf-8'

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == 'application/octet-stream'


def test_sanitize__uppercase_html__blocked():

    # arrange
    content_type = 'TEXT/HTML'

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == 'application/octet-stream'


def test_sanitize__mixed_case_jpeg__passthrough():

    # arrange
    content_type = 'Image/JPEG'

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == 'image/jpeg'


def test_sanitize__jpeg_with_boundary__passthrough():

    # arrange
    content_type = 'image/jpeg; boundary=something'

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == 'image/jpeg'


def test_sanitize__whitespace_around__handled():

    # arrange
    content_type = '  image/png  '

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == 'image/png'


def test_sanitize__svg_mixed_case__blocked():

    # arrange
    content_type = 'Image/SVG+XML'

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == 'application/octet-stream'


def test_sanitize__docx__passthrough():

    # arrange
    content_type = (
        'application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.document'
    )

    # act
    result = sanitize_content_type(content_type=content_type)

    # assert
    assert result == content_type
