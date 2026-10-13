"""Bounded HTTPS downloads through a DNS-validated, pinned transport."""

import asyncio
import ipaddress
import socket
import ssl
from collections.abc import Iterable
from dataclasses import dataclass
from tempfile import SpooledTemporaryFile
from typing import IO
from urllib.parse import urljoin, urlsplit

import httpcore
import httpx

MAX_IMPORT_BYTES = 25 * 1024 * 1024
MAX_REDIRECTS = 3
IMPORT_DEADLINE = 60
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class UnsafeImportError(Exception):
    """An external resource cannot be safely downloaded."""


@dataclass
class ImportedFile:
    """An owned temporary stream, closed by its caller."""

    stream: IO[bytes]
    size: int
    content_type: str | None


def validate_url(raw_url: str) -> httpx.URL:
    """Accept only unambiguous HTTPS URLs on the standard TLS port."""
    try:
        if (
            len(raw_url) > 8192  # noqa: PLR2004
            or '\\' in raw_url
            or any(ord(char) <= 32 or ord(char) == 127 for char in raw_url)  # noqa: PLR2004
        ):
            raise ValueError  # noqa: TRY301
        parsed = urlsplit(raw_url)
        if (
            parsed.scheme.lower() != 'https'
            or '@' in parsed.netloc
            or parsed.fragment
            or parsed.port not in (None, 443)
            or not parsed.hostname
            or '%' in parsed.hostname
        ):
            raise ValueError  # noqa: TRY301
        url = httpx.URL(raw_url)
        if not url.host or url.port not in (None, 443):
            raise ValueError  # noqa: TRY301
    except (ValueError, httpx.InvalidURL):
        msg = 'Only HTTPS URLs without credentials on port 443 are allowed'
        raise UnsafeImportError(msg) from None
    return url


def is_public_address(value: str) -> bool:
    """Reject special-use and transition addresses, including IPv6."""
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if (
        not address.is_global
        or address.is_multicast
        or address.is_reserved
        or address.is_loopback
        or address.is_link_local
        or address.is_unspecified
    ):
        return False
    if isinstance(address, ipaddress.IPv6Address):
        # Transition mechanisms can tunnel to a forbidden IPv4 endpoint.
        return (
            address.ipv4_mapped is None
            and address.sixtofour is None
            and address.teredo is None
            and address in ipaddress.ip_network('2000::/3')
        )
    return True


async def resolve_public_ip(host: str) -> str:
    """Resolve once and reject the entire result if any address is unsafe."""
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        addresses = [str(literal)]
    else:
        results = await asyncio.get_running_loop().getaddrinfo(
            host,
            443,
            type=socket.SOCK_STREAM,
        )
        addresses = [result[4][0] for result in results]
    if not addresses or not all(
        is_public_address(value=address) for address in addresses
    ):
        msg = 'The import host must resolve exclusively to public addresses'
        raise UnsafeImportError(msg)
    return addresses[0]


class PinnedNetworkBackend(httpcore.AsyncNetworkBackend):
    """Dial a numeric address while HTTP and TLS retain the original host."""

    def __init__(self, host: str, address: str):  # noqa: ANN204
        """Bind one DNS decision to one origin and connection pool."""
        self.host = host
        self.address = address
        self.backend = httpcore.AnyIOBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,  # noqa: ASYNC109
        local_address: str | None = None,
        socket_options: Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.AsyncNetworkStream:
        """Prevent a second DNS decision at the connection boundary."""
        if host != self.host or port != 443:  # noqa: PLR2004
            msg = 'Unexpected import origin'
            raise UnsafeImportError(msg)
        return await self.backend.connect_tcp(
            host=self.address,
            port=port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class URLImporter:
    """Fetch externally without ambient proxies or Pneumatic credentials."""

    def __init__(self, max_bytes: int = MAX_IMPORT_BYTES):  # noqa: ANN204
        """Apply a configurable cap that can only lower the hard limit."""
        self.max_bytes = min(max_bytes, MAX_IMPORT_BYTES)
        if self.max_bytes <= 0:
            msg = 'Import size limit must be positive'
            raise ValueError(msg)

    async def _download(
        self,
        raw_url: str,
        stream: IO[bytes],
    ) -> tuple[int, str | None]:
        for hop in range(MAX_REDIRECTS + 1):
            url = validate_url(raw_url=raw_url)
            host = url.raw_host.decode('ascii')
            address = await resolve_public_ip(host=host)
            backend = PinnedNetworkBackend(host=host, address=address)
            # httpcore has no environment proxy discovery. The origin remains
            # the hostname: certificate verification and SNI use it, not IP.
            async with (
                httpcore.AsyncConnectionPool(
                    network_backend=backend,
                    ssl_context=ssl.create_default_context(),
                    max_connections=1,
                    retries=0,
                ) as pool,
                pool.stream(
                    method='GET',
                    url=str(url),
                    headers={'Accept-Encoding': 'identity'},
                    extensions={
                        'timeout': dict.fromkeys(
                            ('connect', 'read', 'write', 'pool'),
                            10.0,
                        )
                    },
                ) as response,
            ):
                headers = {
                    key.lower(): value for key, value in response.headers
                }
                if response.status in REDIRECT_STATUSES:
                    if hop == MAX_REDIRECTS or b'location' not in headers:
                        msg = 'Too many import redirects or missing target'
                        raise UnsafeImportError(msg)
                    raw_url = urljoin(
                        str(url),
                        headers[b'location'].decode('ascii'),
                    )
                    continue
                return await self._read_response(
                    response=response,
                    headers=headers,
                    stream=stream,
                )
        msg = 'Import redirect limit exceeded'
        raise UnsafeImportError(msg)

    async def _read_response(  # noqa: PLR0912
        self,
        response: httpcore.Response,
        headers: dict[bytes, bytes],
        stream: IO[bytes],
    ) -> tuple[int, str | None]:
        if response.status != 200:  # noqa: PLR2004
            msg = 'Import source returned an unsuccessful response'
            raise UnsafeImportError(msg)
        encoding = headers.get(b'content-encoding', b'identity').lower()
        if encoding != b'identity':
            msg = 'Encoded import responses are not supported'
            raise UnsafeImportError(msg)
        if b'content-length' in headers:
            length = int(headers[b'content-length'])
            if length < 0 or length > self.max_bytes:
                msg = 'Import source exceeds the size limit'
                raise UnsafeImportError(msg)
        size = 0
        async for chunk in response.aiter_stream():
            size += len(chunk)
            if size > self.max_bytes:
                msg = 'Import source exceeds the size limit'
                raise UnsafeImportError(msg)
            write_task = asyncio.create_task(
                asyncio.to_thread(stream.write, chunk),
            )
            try:
                await asyncio.shield(write_task)
            except asyncio.CancelledError:
                # Cancellation cannot close a spool still owned by a thread.
                drain = asyncio.gather(write_task, return_exceptions=True)
                while not drain.done():
                    try:
                        await asyncio.shield(drain)
                    except asyncio.CancelledError:
                        continue
                raise
        content_type = headers.get(b'content-type')
        return size, content_type.decode('latin1') if content_type else None

    async def download(self, raw_url: str) -> ImportedFile:
        """Bound DNS, redirects, TLS and streaming by one overall deadline."""
        # Ownership transfers to ImportedFile and then the route's finally.
        stream = SpooledTemporaryFile(  # noqa: SIM115
            max_size=1024 * 1024,
            mode='w+b',
        )
        try:
            async with asyncio.timeout(IMPORT_DEADLINE):
                size, content_type = await self._download(
                    raw_url=raw_url,
                    stream=stream,
                )
            stream.seek(0)
            return ImportedFile(
                stream=stream,
                size=size,
                content_type=content_type,
            )
        except BaseException:
            stream.close()
            raise
