"""Exercise the production HTTP parser and pinned connection boundary."""

import asyncio
import socket
import ssl
import threading
from collections.abc import Callable
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, call

import httpcore
import pytest
from pytest_mock import MockerFixture

from src.infra.url_importer import (
    UnsafeImportError,
    URLImporter,
    is_public_address,
    resolve_public_ip,
    validate_url,
)


@pytest.mark.parametrize(
    'url',
    [
        'http://example.com/a',
        'https://user@example.com/a',
        'https://user:pass@example.com/a',
        'https://example.com:444/a',
        'https://example.com/a#fragment',
        'https://example.com\\@127.0.0.1/a',
        'https://example.com\n/a',
        'https://[fe80::1%25eth0]/a',
        'https://example.com:bad/a',
        'https:///missing-host',
    ],
)
def test_unsafe__url_rejected__denied(url: str):
    # arrange

    # act
    with pytest.raises(UnsafeImportError) as ex:
        validate_url(raw_url=url)

    # assert
    assert str(ex.value) == (
        'Only HTTPS URLs without credentials on port 443 are allowed'
    )


@pytest.mark.parametrize(
    'address',
    [
        '127.0.0.1',
        '10.0.0.1',
        '172.16.0.1',
        '192.168.1.1',
        '169.254.169.254',
        '100.64.1.1',
        '0.0.0.0',
        '224.0.0.1',
        '240.0.0.1',
        '192.0.2.1',
        '::1',
        '::',
        'fe80::1',
        'fc00::1',
        'ff02::1',
        '2001:db8::1',
        '::ffff:127.0.0.1',
        '::ffff:8.8.8.8',
        '64:ff9b::a00:1',
        '2002:0a00:0001::1',
        '2001::a00:1',
    ],
)
def test_nonpublic__address_rejected__denied(address: str):
    # arrange

    # act
    result = is_public_address(value=address)

    # assert
    assert not result


@pytest.mark.parametrize('address', ['8.8.8.8', '2606:4700:4700::1111'])
def test_public__ipv4_and_ipv6_allowed__ok(address: str):
    # arrange

    # act
    result = is_public_address(value=address)

    # assert
    assert result


async def test_mixed__dns_answer_denied__denied(mocker: MockerFixture):
    # arrange
    resolver = mocker.patch.object(
        asyncio.get_running_loop(),
        'getaddrinfo',
        new_callable=AsyncMock,
    )
    resolver.return_value = [
        (2, 1, 6, '', ('8.8.8.8', 443)),
        (2, 1, 6, '', ('127.0.0.1', 443)),
    ]

    # act
    with pytest.raises(UnsafeImportError) as ex:
        await resolve_public_ip(host='example.com')

    # assert
    assert str(ex.value) == (
        'The import host must resolve exclusively to public addresses'
    )
    resolver.assert_awaited_once_with(
        'example.com',
        443,
        type=socket.SOCK_STREAM,
    )


@pytest.mark.parametrize(
    ('url_host', 'tls_host'),
    [
        ('example.com', 'example.com'),
        ('пример.рф', 'xn--e1afmkfd.xn--p1ai'),
    ],
)
async def test_ip__is_pinned_and_sni_preserved_no_ambient_auth__ok(
    mocker: MockerFixture,
    wire: Callable[..., Any],
    url_host: str,
    tls_host: str,
):
    # arrange
    dns = mocker.patch(
        'src.infra.url_importer.resolve_public_ip', return_value='8.8.8.8'
    )
    backend, streams = wire(b'HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\nabc')
    tls_context = ssl.create_default_context()
    ssl_mock = mocker.patch(
        'src.infra.url_importer.ssl.create_default_context',
        return_value=tls_context,
    )
    mocker.patch.dict('os.environ', {'HTTPS_PROXY': 'http://127.0.0.1:1'})

    # act
    result = await URLImporter().download(
        raw_url=f'https://{url_host}/file?signature=secret'
    )

    # assert
    try:
        assert result.stream.read() == b'abc'
        assert result.size == 3
        assert tls_context.check_hostname
        assert tls_context.verify_mode == ssl.CERT_REQUIRED
        ssl_mock.assert_called_once_with()
        assert dns.await_count == 1
        dns.assert_awaited_once_with(host=tls_host)
        backend.connect_tcp.assert_awaited_once_with(
            host='8.8.8.8',
            port=443,
            timeout=10.0,
            local_address=None,
            socket_options=None,
        )
        streams[0].start_tls.assert_awaited_once_with(
            ssl_context=tls_context,
            server_hostname=tls_host,
            timeout=10.0,
        )
        assert streams[0].write.await_count == 3
        streams[0].write.assert_has_awaits(
            [
                call(
                    (
                        f'GET /file?signature=secret HTTP/1.1\r\n'
                        f'Host: {tls_host}\r\n'
                        'Accept-Encoding: identity\r\n\r\n'
                    ).encode(),
                    timeout=10.0,
                ),
                call(b'', timeout=10.0),
                call(b'', timeout=10.0),
            ]
        )
    finally:
        result.stream.close()


async def test_redirect__dns_revalidated_and_rebinding_denied__denied(
    mocker: MockerFixture, wire: Callable[..., Any]
):
    # arrange
    wire(
        b'HTTP/1.1 302 Found\r\nLocation: https://internal.example/file\r\n'
        b'Content-Length: 0\r\n\r\n'
    )
    dns = mocker.patch.object(
        asyncio.get_running_loop(), 'getaddrinfo', new_callable=AsyncMock
    )
    dns.side_effect = [
        [(2, 1, 6, '', ('8.8.8.8', 443))],
        [(2, 1, 6, '', ('127.0.0.1', 443))],
    ]

    # act
    with pytest.raises(UnsafeImportError) as ex:
        await URLImporter().download(raw_url='https://example.com/file')

    # assert
    assert str(ex.value) == (
        'The import host must resolve exclusively to public addresses'
    )
    assert dns.await_count == 2

    dns.assert_has_awaits(
        [
            call('example.com', 443, type=socket.SOCK_STREAM),
            call('internal.example', 443, type=socket.SOCK_STREAM),
        ],
    )


@pytest.mark.parametrize(
    'location',
    [
        'http://example.com/file',
        'https://user@example.com/file',
        'https://example.com:8443/file',
        'https://[::1]/file',
    ],
)
async def test_unsafe__redirect_rejected__denied(
    mocker: MockerFixture, wire: Callable[..., Any], location: str
):
    # arrange
    wire(
        (
            f'HTTP/1.1 302 Found\r\nLocation: {location}\r\n'
            'Content-Length: 0\r\n\r\n'
        ).encode()
    )
    dns_mock = mocker.patch.object(
        asyncio.get_running_loop(),
        'getaddrinfo',
        return_value=[(2, 1, 6, '', ('8.8.8.8', 443))],
    )

    # act
    with pytest.raises(UnsafeImportError) as ex:
        await URLImporter().download(raw_url='https://example.com/file')

    # assert
    assert str(ex.value) == (
        'The import host must resolve exclusively to public addresses'
        if location == 'https://[::1]/file'
        else 'Only HTTPS URLs without credentials on port 443 are allowed'
    )
    dns_mock.assert_awaited_once_with(
        'example.com',
        443,
        type=socket.SOCK_STREAM,
    )


async def test_max__three_redirects__ok(
    mocker: MockerFixture, wire: Callable[..., Any]
):
    # arrange
    redirect = (
        b'HTTP/1.1 302 Found\r\nLocation: /next\r\nContent-Length: 0\r\n\r\n'
    )
    wire(redirect, redirect, redirect, redirect)
    dns = mocker.patch(
        'src.infra.url_importer.resolve_public_ip', return_value='8.8.8.8'
    )

    # act
    with pytest.raises(UnsafeImportError) as ex:
        await URLImporter().download(raw_url='https://example.com/file')

    # assert
    assert dns.await_count == 4

    assert str(ex.value) == ('Too many import redirects or missing target')
    dns.assert_has_awaits(
        [
            call(host='example.com'),
            call(host='example.com'),
            call(host='example.com'),
            call(host='example.com'),
        ],
    )


@pytest.mark.parametrize(
    'response',
    [
        b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nabcde',
        (
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'
            b'5\r\nabcde\r\n0\r\n\r\n'
        ),
        (
            b'HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\n'
            b'Content-Length: 3\r\n\r\nabc'
        ),
    ],
)
async def test_stream__and_declared_size_limits__ok(
    mocker: MockerFixture, wire: Callable[..., Any], response: bytes
):
    # arrange
    wire(response)
    dns_mock = mocker.patch(
        'src.infra.url_importer.resolve_public_ip', return_value='8.8.8.8'
    )

    # act
    with pytest.raises(UnsafeImportError) as ex:
        await URLImporter(max_bytes=4).download(
            raw_url='https://example.com/file'
        )

    # assert
    assert str(ex.value) == (
        'Encoded import responses are not supported'
        if b'Content-Encoding' in response
        else 'Import source exceeds the size limit'
    )
    dns_mock.assert_awaited_once_with(host='example.com')


async def test_overall__deadline_includes_dns__ok(mocker: MockerFixture):
    # arrange
    async def stalled(host: str):
        await asyncio.Event().wait()

    mocker.patch('src.infra.url_importer.IMPORT_DEADLINE', 0.01)
    dns_mock = mocker.patch(
        'src.infra.url_importer.resolve_public_ip', side_effect=stalled
    )

    # act
    with pytest.raises(TimeoutError) as ex:
        await URLImporter().download(raw_url='https://example.com/file')

    # assert
    assert str(ex.value) == ''
    dns_mock.assert_awaited_once_with(host='example.com')


def test_config__cannot_raise_hard_cap__ok():
    # arrange

    # act
    importer = URLImporter(max_bytes=100 * 1024 * 1024)

    # assert
    assert importer.max_bytes == 25 * 1024 * 1024


@pytest.mark.parametrize('repeat_cancel', [False, True])
async def test_download__cancel_during_spool_write__drains_before_close(
    mocker: MockerFixture,
    wire: Callable[..., Any],
    repeat_cancel: bool,
):
    # arrange
    wire(b'HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\nabc')
    dns_mock = mocker.patch(
        'src.infra.url_importer.resolve_public_ip',
        return_value='8.8.8.8',
    )
    stream = BytesIO()
    spool_mock = mocker.patch(
        'src.infra.url_importer.SpooledTemporaryFile',
        return_value=stream,
    )
    started, release = threading.Event(), threading.Event()
    original_write = stream.write

    def blocked_write(data: bytes) -> int:
        started.set()
        if not release.wait(timeout=5):
            message = 'test write was not released'
            raise TimeoutError(message)
        return original_write(data)

    write_mock = mocker.patch.object(
        stream,
        'write',
        side_effect=blocked_write,
    )

    task = asyncio.create_task(
        coro=URLImporter().download(raw_url='https://example.com/file'),
    )

    # act
    try:
        write_started = await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        if repeat_cancel:
            task.cancel()
            await asyncio.sleep(0)
        pending_before_release = not task.done()
        open_before_release = not stream.closed
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(fut=task, timeout=5)
    finally:
        release.set()

    # assert
    assert write_started
    assert pending_before_release
    assert open_before_release
    assert stream.closed
    write_mock.assert_called_once_with(b'abc')
    spool_mock.assert_called_once_with(max_size=1024 * 1024, mode='w+b')
    dns_mock.assert_awaited_once_with(host='example.com')


@pytest.mark.parametrize('limit', [0, -1])
def test_init__nonpositive_limit__rejected(limit: int):
    # arrange

    # act
    with pytest.raises(
        ValueError, match=r'^Import size limit must be positive$'
    ) as ex:
        URLImporter(max_bytes=limit)

    # assert
    assert str(ex.value) == 'Import size limit must be positive'


@pytest.mark.parametrize('status', [201, 204, 400, 404, 503])
async def test_read_response__unsuccessful_status__no_write(
    import_response: Callable[..., httpcore.Response],
    status: int,
):
    # arrange
    response = import_response(status=status)
    stream = BytesIO()

    # act
    with pytest.raises(UnsafeImportError) as ex:
        await URLImporter()._read_response(
            response=response,
            headers={},
            stream=stream,
        )

    # assert
    assert str(ex.value) == 'Import source returned an unsuccessful response'
    assert stream.getvalue() == b''
    assert not stream.closed


@pytest.mark.parametrize('length', [b'', b'undefined', b'1.5'])
async def test_read_response__malformed_length__rejected_before_write(
    import_response: Callable[..., httpcore.Response],
    length: bytes,
):
    # arrange
    headers = {b'content-length': length}
    response = import_response(headers=headers)
    stream = BytesIO()

    # act
    with pytest.raises(ValueError, match='invalid literal for int') as ex:
        await URLImporter()._read_response(
            response=response,
            headers=headers,
            stream=stream,
        )

    # assert
    assert str(ex.value) == (
        f'invalid literal for int() with base 10: {length!r}'
    )
    assert stream.getvalue() == b''
    assert not stream.closed


async def test_read_response__negative_length__no_write(
    import_response: Callable[..., httpcore.Response],
):
    # arrange
    headers = {b'content-length': b'-1'}
    response = import_response(headers=headers)
    stream = BytesIO()

    # act
    with pytest.raises(UnsafeImportError) as ex:
        await URLImporter()._read_response(
            response=response,
            headers=headers,
            stream=stream,
        )

    # assert
    assert str(ex.value) == 'Import source exceeds the size limit'
    assert stream.getvalue() == b''
    assert not stream.closed


async def test_read_response__no_optional_headers__default_metadata(
    import_response: Callable[..., httpcore.Response],
):
    # arrange
    response = import_response()
    stream = BytesIO()

    # act
    result = await URLImporter()._read_response(
        response=response,
        headers={},
        stream=stream,
    )

    # assert
    assert result == (3, None)
    assert stream.getvalue() == b'abc'
    assert not stream.closed
