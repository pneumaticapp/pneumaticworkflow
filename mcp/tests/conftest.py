import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import mcp_types as types
import pytest
import uvicorn
from redis.asyncio import Redis

from pneumatic_mcp.app import create_app
from pneumatic_mcp.client import CoreClient
from pneumatic_mcp.settings import SCOPES, Settings

TOKEN_A = "source-oauth-account-a-0123456789"
TOKEN_B = "source-oauth-account-b-9876543210"
UPLOAD_ID = "018e0000-0000-7000-8000-000000000001"
SECRET = "service-test-secret-0123456789-abcdef"
MODERN = "2026-07-28"


@pytest.fixture
def modern_meta():
    def factory(version: str = MODERN) -> dict[str, Any]:
        return {
            types.PROTOCOL_VERSION_META_KEY: version,
            types.CLIENT_CAPABILITIES_META_KEY: {},
            types.CLIENT_INFO_META_KEY: {"name": "http-test", "version": "1"},
        }

    return factory


class FakeCore:
    """Core boundary double; the resource server is exercised over an actual
    TCP socket."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.requests: list[httpx.Request] = []
        self.business_requests: list[httpx.Request] = []
        self.file_requests: list[httpx.Request] = []
        self.delegations: dict[str, dict] = {}
        self.tokens = {
            TOKEN_A: {
                "active": True,
                "sub": "11",
                "user_id": 11,
                "account_id": 101,
                "client_id": "shared-client",
                "connection_id": "connection-a",
                "scope": " ".join(sorted(SCOPES)),
                "aud": settings.public_url,
                "exp": int(time.time()) + 900,
            },
            TOKEN_B: {
                "active": True,
                "sub": "22",
                "user_id": 22,
                "account_id": 202,
                "client_id": "shared-client",
                "connection_id": "connection-b",
                "scope": " ".join(sorted(SCOPES)),
                "aud": settings.public_url,
                "exp": int(time.time()) + 900,
            },
        }
        for index in range(1, 7):
            self.tokens[f"shared-account-source-{index}-abcdefghijklmnop"] = {
                **self.tokens[TOKEN_A],
                "connection_id": f"account-connection-{index}",
            }
        self.business_status = 200
        self.business_body = None
        self.attachment_file_id = "file-uuid-0001"
        self.delegate_override: dict = {}
        self.delegate_status = 200
        self.delegate_error_body = None
        self.introspection_status = 200
        self.introspection_body = None
        self.introspection_error = None
        self.error: Exception | None = None
        self.delay = 0
        self.started = asyncio.Event()
        self.release: asyncio.Event | None = None

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path.removeprefix("/core-prefix")
        if path.startswith("/internal/mcp/"):
            assert request.headers.get("X-MCP-Service-Secret") == SECRET
            assert "authorization" not in request.headers
            body = json.loads(request.content)
            assert body["resource"] == self.settings.public_url
            identity = self.tokens.get(body["token"])
            if path == "/internal/mcp/introspect":
                if self.introspection_error:
                    raise self.introspection_error
                return httpx.Response(
                    self.introspection_status,
                    json=(
                        self.introspection_body
                        if self.introspection_body is not None
                        else identity or {"active": False}
                    ),
                )
            assert path == "/internal/mcp/delegate"
            if self.delegate_status != 200:
                return httpx.Response(
                    self.delegate_status, json=self.delegate_error_body
                )
            if not identity or identity.get("active") is not True:
                return httpx.Response(
                    401, json={"detail": "revoked", "code": "invalid_token"}
                )
            if not set(body["scopes"]) <= set(identity["scope"].split()):
                return httpx.Response(403, json={"detail": "invalid scope"})
            credential = f"mcp-d_{len(self.delegations):032d}"
            self.delegations[credential] = {
                **body,
                "identity": identity.copy(),
            }
            return httpx.Response(
                200,
                json={
                    "credential": credential,
                    "token_type": "Bearer",
                    "expires_in": 60,
                    "expires_at": int(time.time()) + 60,
                    "scopes": body["scopes"],
                    "operation": body["tool"],
                    "audience": "pneumatic-files"
                    if body["path"].startswith("/mcp/files/")
                    else "pneumatic-backend",
                    "connection_id": identity["connection_id"],
                    "account_id": identity["account_id"],
                    "user_id": identity["user_id"],
                    **self.delegate_override,
                },
            )
        self.business_requests.append(request)
        credential = request.headers["authorization"].removeprefix("Bearer ")
        assert credential not in {TOKEN_A, TOKEN_B}
        assert "X-MCP-Service-Secret" not in request.headers
        grant = self.delegations[credential]
        assert path == grant["path"]
        assert request.method == grant["method"]
        self.started.set()
        if self.release:
            await self.release.wait()
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        if self.business_body is not None:
            return httpx.Response(
                self.business_status, json=self.business_body
            )
        data = {
            "id": grant["identity"]["account_id"],
            "name": "An object",
            "status": 1,
        }
        if path in {
            "/templates",
            "/workflows",
            "/v3/tasks",
            "/attachments",
        } or path.endswith("/events"):
            return httpx.Response(
                self.business_status,
                json={
                    "count": 1,
                    "results": [{**data, "file_id": "file-uuid-0001"}],
                },
            )
        if path.endswith("/kickoff"):
            data.update(
                template_id=7,
                fields=[
                    {
                        "api_name": "text-1",
                        "name": "Text",
                        "type": "string",
                        "is_required": True,
                    }
                ],
            )
        if path == "/integrations/mcp/uploads":
            data.update(
                id=UPLOAD_ID,
                status="pending",
                credential="mcp-u_ephemeral-capability",
                upload_url=f"https://my.pneumatic.app/mcp/uploads/{UPLOAD_ID}",
            )
        if path.startswith("/integrations/mcp/attachments/"):
            data["file_id"] = self.attachment_file_id
        if path.startswith("/integrations/mcp/uploads/"):
            data.update(id=UPLOAD_ID, status="ready")
        return httpx.Response(self.business_status, json=data)

    async def files(self, request: httpx.Request) -> httpx.Response:
        self.file_requests.append(request)
        assert request.url.host == "file-service"
        assert "X-MCP-Service-Secret" not in request.headers
        credential = request.headers["authorization"].removeprefix("Bearer ")
        grant = self.delegations[credential]
        assert grant["path"] == request.url.raw_path.decode()
        assert grant["method"] == request.method
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "file_id": self.attachment_file_id,
                    "name": "example.txt",
                    "size": 16,
                    "content_type": "text/plain",
                },
            )
        return httpx.Response(
            200,
            json={
                "download_url": "https://my.pneumatic.app/files/mcp/download/"
                + "x" * 43,
                "expires_at": "2026-10-09T00:00:00Z",
                "expires_in": 300,
            },
        )


@asynccontextmanager
async def running_server(
    app: Any, *, limit_concurrency: int | None = None
) -> AsyncIterator[str]:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    port = sock.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="error",
            access_log=False,
            lifespan="on",
            limit_concurrency=limit_concurrency,
            timeout_graceful_shutdown=2,
        )
    )
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        async with asyncio.timeout(10):
            while not server.started:
                if task.done():
                    await task
                    raise RuntimeError(
                        "Test HTTP server exited before startup"
                    )
                await asyncio.sleep(0.01)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=5)
        sock.close()


@dataclass
class Service:
    http: httpx.AsyncClient
    upstream: FakeCore
    settings: Settings
    url: str

    async def rpc(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        token: str | None = TOKEN_A,
        **kwargs: Any,
    ) -> httpx.Response:
        headers = (
            {"Authorization": f"Bearer {token}"} if token is not None else {}
        )
        headers.update(kwargs.pop("headers", {}))
        return await self.http.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or {},
            },
            headers=headers,
            **kwargs,
        )

    async def tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        return await self.rpc(
            method="tools/call",
            params={"name": name, "arguments": arguments or {}},
            **kwargs,
        )


@pytest.fixture
async def service_factory():
    @asynccontextmanager
    async def factory(**overrides: Any):
        limiter = overrides.pop("limiter", None) or TestLimiter()
        settings = Settings(
            _env_file=None,
            **{
                "enabled": True,
                "service_secret": SECRET,
                "public_url": "https://my.pneumatic.app/mcp",
                "issuer_url": "https://my.pneumatic.app",
                "backend_url": "http://core.test/core-prefix/",
                "allowed_hosts": ["test-host"],
                "allowed_origins": ["https://my.pneumatic.app"],
                **overrides,
            },
        )
        upstream = FakeCore(settings=settings)
        core = CoreClient(
            settings=settings,
            transport=httpx.MockTransport(upstream),
            file_transport=httpx.MockTransport(upstream.files),
        )
        async with running_server(
            app=create_app(settings=settings, core=core, limiter=limiter),
            limit_concurrency=settings.max_concurrency,
        ) as url:
            async with httpx.AsyncClient(
                base_url=url,
                trust_env=False,
                timeout=5,
                headers={
                    "Host": "test-host",
                    "Accept": "application/json, text/event-stream",
                    "MCP-Protocol-Version": "2025-11-25",
                },
            ) as http:
                yield Service(
                    http=http, upstream=upstream, settings=settings, url=url
                )

    return factory


@pytest.fixture
async def service(service_factory: Any):
    async with service_factory() as service:
        yield service


class TestLimiter:
    async def acquire(self, connection_id: str, account_id: int):
        pass

    async def close(self):
        pass


@pytest.fixture
async def redis_url():
    url = os.environ.get("MCP_TEST_REDIS_URL")
    if not url:
        pytest.skip(
            "Set MCP_TEST_REDIS_URL to an isolated Redis to "
            "run real replica tests"
        )
    redis = Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
    assert await redis.ping()
    await redis.aclose()
    return url


@pytest.fixture
async def replicas(redis_url: str):
    namespace = "mcp-tests-" + uuid4().hex
    workers, urls = [], []
    try:
        for _ in range(2):
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            workers.append(
                await asyncio.to_thread(
                    subprocess.Popen,
                    [
                        sys.executable,
                        str(Path(__file__).with_name("redis_worker.py")),
                        str(port),
                        redis_url,
                        namespace,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
            )
            urls.append(f"http://127.0.0.1:{port}")
        async with httpx.AsyncClient(trust_env=False) as http:
            metadata_path = "/.well-known/oauth-protected-resource/mcp"
            async with asyncio.timeout(15):
                for worker, url in zip(workers, urls, strict=True):
                    while True:
                        if worker.poll() is not None:
                            raise RuntimeError(worker.stderr.read().decode())
                        try:
                            if (
                                await http.get(url + metadata_path)
                            ).status_code == 200:
                                break
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.05)
            yield http, urls
    finally:
        for worker in workers:
            worker.terminate()
            await asyncio.to_thread(worker.wait, 10)
            worker.stderr.close()
        redis = Redis.from_url(redis_url)
        keys = [key async for key in redis.scan_iter(match=namespace + ":*")]
        if keys:
            await redis.delete(*keys)
        await redis.aclose()


@pytest.fixture
def replica_rpc():
    async def call(
        http: httpx.AsyncClient,
        url: str,
        *,
        token: str = TOKEN_A,
        method: str = "tools/call",
    ) -> httpx.Response:
        return await http.post(
            url=url + "/mcp",
            headers={
                "Host": "test-host",
                "Authorization": f"Bearer {token}",
                "MCP-Protocol-Version": "2025-11-25",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": {
                    "name": "get_workflow",
                    "arguments": {"workflow_id": 1},
                }
                if method == "tools/call"
                else {},
            },
        )

    return call
