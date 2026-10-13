"""Real HTTP contract smoke for Django and the MCP SDK resource server.

Run with the backend test dependencies AND mcp/pyproject.toml dependencies,
an isolated PostgreSQL database and MCP_TEST_REDIS_URL. From the repo root:
PYTHONPATH=backend:mcp/src pytest -c backend/pytest.ini \
    scripts/tests/test_mcp_core_http.py

This exercises real OAuth and business views over TCP. It does not establish
acceptance by Claude.ai/ChatGPT, frontend SSO or the external storage provider.
Set MCP_STORAGE_SMOKE_URL to the isolated live_mcp_server.py URL to also
exercise storage HTTP, PostgreSQL, completion callbacks and revocable bytes.
"""

import base64
import hashlib
import os
import socket
import sys
import threading
import time
import traceback
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import uvicorn
from django.core.signals import got_request_exception
from pneumatic_mcp.app import create_app
from pneumatic_mcp.settings import Settings
from pneumatic_mcp.tool_catalog import TOOLS
from pytest_django.fixtures import SettingsWrapper
from pytest_django.live_server_helper import LiveServer
from pytest_mock import MockerFixture
from src.authentication.tokens import PneumaticToken
from src.generics.throttling import CustomSimpleRateThrottle
from src.authentication.throttling import (
    OAuthAuthorizeThrottle,
    OAuthRegisterThrottle,
    OAuthTokenThrottle,
)
from src.mcp.models import ClientPolicy, Connection
from src.processes.enums import FieldType
from src.processes.models.templates.template import TemplateIntegrations
from src.processes.models.workflows.task import Task
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_owner,
    create_test_template,
)
from src.storage.models import Attachment


@pytest.mark.django_db(transaction=True)
def test_mcp_http__workflow_files_and_revocation__ok(
    settings: SettingsWrapper,
    live_server: LiveServer,
    mocker: MockerFixture,
):
    redis_url = os.environ.get("MCP_TEST_REDIS_URL")
    if not redis_url:
        pytest.skip("An isolated Redis is required for this real HTTP smoke")

    # arrange: no real account, token or external provider is used.
    settings.MCP_ENABLED = True
    settings.MCP_PUBLIC_URL = "https://pneumatic.test/mcp"
    settings.MCP_ISSUER_URL = "https://pneumatic.test"
    settings.FRONTEND_URL = settings.MCP_ISSUER_URL
    settings.FILE_SERVICE_URL = "https://pneumatic.test/files"
    settings.FILE_SERVICE_HOST_PATH = "pneumatic.test/files"
    settings.MCP_SERVICE_SECRET = "isolated-core-smoke-secret-0123456789"
    settings.MCP_FILE_SERVICE_SECRET = "isolated-file-smoke-secret-9876543210"
    settings.CACHES = {
        **settings.CACHES,
        "default": {
            **settings.CACHES["default"],
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": redis_url,
            "KEY_PREFIX": "mcp-http-" + os.urandom(16).hex(),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 2,
                "SOCKET_TIMEOUT": 2,
            },
        },
    }
    # Lifecycle smoke isolates the flow from request timing; throttle intervals
    # are exercised by the backend OAuth tests using this same implementation.
    mocker.patch.object(
        CustomSimpleRateThrottle,
        "THROTTLE_RATES",
        {
            **CustomSimpleRateThrottle.THROTTLE_RATES,
            OAuthRegisterThrottle.scope: None,
            OAuthAuthorizeThrottle.scope: None,
            OAuthTokenThrottle.scope: None,
        },
    )
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, "ANALYTICS": False}
    analytics_track_mock = mocker.patch(
        "src.analysis.services.analytics.track"
    )
    # Keep ordinary task scheduling real; intercept the broker so no
    # eager notification, webhook or ACL-sync task reaches an external service.
    broker_mock = mocker.patch(
        "celery.app.task.Task.apply_async", autospec=True,
    )
    storage_url = os.environ.get("MCP_STORAGE_SMOKE_URL")
    if storage_url:
        settings.MCP_FILE_SERVICE_URL = storage_url
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "pneumatic.test"]
    settings.OAUTH2_PROVIDER = {
        **settings.OAUTH2_PROVIDER,
        "OIDC_ISS_ENDPOINT": settings.MCP_ISSUER_URL,
    }
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=1,
    )
    if storage_url:
        file_fields = create_test_fieldset_template(
            account=account,
            template=template,
            task=template.tasks.get(number=1),
        )
        file_fields.fields.update(
            api_name="field_file",
            type=FieldType.FILE,
            name="File",
        )
    TemplateIntegrations.objects.get_or_create(
        template=template, defaults={"account": account}
    )
    login_token = PneumaticToken.create(
        user=user, user_agent="MCP smoke", user_ip="127.0.0.1"
    )
    client = httpx.Client(
        base_url=live_server.url, trust_env=False, timeout=20
    )
    core_errors = []

    def capture_core_exception(sender: object, **kwargs: object):
        core_errors.append(
            "".join(traceback.format_exception(*sys.exc_info()))
        )

    got_request_exception.connect(capture_core_exception, weak=False)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    app = create_app(
        Settings(
            enabled=True,
            public_url=settings.MCP_PUBLIC_URL,
            issuer_url=settings.MCP_ISSUER_URL,
            backend_url=live_server.url,
            file_service_url=storage_url or "http://file-service:8000",
            service_secret=settings.MCP_SERVICE_SECRET,
            redis_url=redis_url,
            allowed_hosts=["pneumatic.test"],
        )
    )
    server = uvicorn.Server(
        uvicorn.Config(app, log_level="critical", access_log=False)
    )
    thread = threading.Thread(
        target=server.run, kwargs={"sockets": [listener]}, daemon=True
    )
    thread.start()
    mcp = httpx.Client(
        base_url=f"http://127.0.0.1:{port}",
        trust_env=False,
        timeout=20,
        headers={
            "Host": "pneumatic.test",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": "2025-11-25",
        },
    )
    try:
        deadline = time.monotonic() + 10
        while not server.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert server.started
        probe = client.post(
            "/internal/mcp/introspect",
            headers={"X-MCP-Service-Secret": settings.MCP_SERVICE_SECRET},
            json={
                "token": "synthetic-invalid-token",
                "resource": settings.MCP_PUBLIC_URL,
            },
        )
        assert probe.status_code == 200, probe.text
        assert probe.json() == {"active": False}
        assert (
            mcp.get("/.well-known/oauth-protected-resource/mcp").status_code
            == 200
        )

        # act: a public DCR client completes S256, login bridge and consent.
        registration = client.post(
            "/oauth/mcp/register",
            json={
                "client_name": "Isolated HTTP smoke",
                "redirect_uris": ["https://client.test/callback"],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
            },
        )
        assert registration.status_code == 201, registration.text
        client_id = registration.json()["client_id"]
        policy = ClientPolicy.objects.get(application__client_id=client_id)
        assert policy.can_introspect is False
        verifier = "v" * 64
        challenge = (
            base64.urlsafe_b64encode(
                hashlib.sha256(verifier.encode()).digest()
            )
            .decode()
            .rstrip("=")
        )
        authorization = client.get(
            "/oauth/mcp/authorize",
            params={
                "client_id": client_id,
                "redirect_uri": "https://client.test/callback",
                "response_type": "code",
                "scope": (
                    "pneumatic:read pneumatic:write files:read files:write"
                ),
                "state": "synthetic-state",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "resource": settings.MCP_PUBLIC_URL,
            },
        )
        assert authorization.status_code == 302, authorization.text
        request_id = parse_qs(
            urlparse(authorization.headers["location"]).query
        )["request_id"][0]
        user_headers = {"Authorization": f"Bearer {login_token}"}
        bridge = client.post(
            "/integrations/mcp/login-code",
            headers=user_headers,
            json={"request_id": request_id},
        )
        assert bridge.status_code == 200, bridge.text
        handoff = client.get(
            "/oauth/mcp/login",
            params={"request_id": request_id, "code": bridge.json()["code"]},
        )
        assert handoff.status_code == 302, handoff.text
        consent = client.post(
            "/integrations/mcp/consent",
            headers=user_headers,
            json={"request_id": request_id, "allow": True},
        )
        assert consent.status_code == 200, consent.text
        final = client.get(
            "/oauth/mcp/login",
            params={"request_id": request_id, "code": consent.json()["code"]},
        )
        assert final.status_code == 302, final.text
        callback = parse_qs(urlparse(final.headers["location"]).query)
        assert callback["state"] == ["synthetic-state"]
        assert callback["iss"] == [settings.MCP_ISSUER_URL]
        token_response = client.post(
            "/oauth/mcp/token",
            data={
                "grant_type": "authorization_code",
                "code": callback["code"][0],
                "client_id": client_id,
                "redirect_uri": "https://client.test/callback",
                "code_verifier": verifier,
                "resource": settings.MCP_PUBLIC_URL,
            },
        )
        assert token_response.status_code == 200, token_response.text
        tokens = token_response.json()
        assert tokens["expires_in"] == 900
        mcp.headers["Authorization"] = f"Bearer {tokens['access_token']}"

        def rpc(
            method: str,
            params: dict[str, object] | None = None,
        ) -> dict[str, object]:
            response = mcp.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": method,
                    "params": params or {},
                },
            )
            assert response.status_code == 200, response.text
            result = response.json()["result"]
            assert result.get("isError") is not True, (
                core_errors[-1] if core_errors else result
            )
            return result

        def tool(
            name: str,
            arguments: dict[str, object] | None = None,
        ) -> dict[str, object]:
            return rpc(
                method="tools/call",
                params={"name": name, "arguments": arguments or {}},
            )["structuredContent"]["data"]

        initialized = rpc(
            method="initialize",
            params={
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "real-core-smoke", "version": "1"},
            },
        )
        assert initialized["protocolVersion"] == "2025-11-25"
        discovered_tools = rpc(method="tools/list")["tools"]
        assert len(discovered_tools) == len(TOOLS)
        assert {tool["name"] for tool in discovered_tools} == set(TOOLS)
        assert tool(name="list_templates")["items"][0]["id"] == template.pk
        assert (
            tool(
                name="get_template_kickoff",
                arguments={"template_id": template.pk},
            )["template_id"]
            == template.pk
        )
        args = {
            "template_id": template.pk,
            "name": "Real HTTP smoke",

        }
        first = tool(name="run_workflow", arguments=args)
        assert template.workflows.count() == 1
        workflow_id = first["id"]
        workflow = tool(
            name="get_workflow", arguments={"workflow_id": workflow_id}
        )
        task_id = workflow["tasks"][0]["id"]
        assert (
            tool(name="get_task", arguments={"task_id": task_id})["id"]
            == task_id
        )
        comment = tool(
            name="add_workflow_comment",
            arguments={
                "workflow_id": workflow_id,
                "text": "HTTP comment",

            },
        )
        assert comment["id"] > 0
        download_path = None
        if storage_url:
            # The storage sidecar replaces only the byte provider. Core grants,
            # callbacks, SQL rows and attachment permissions remain genuine.
            task = Task.objects.get(pk=task_id)
            field = task.workflow.fields.get(api_name="field_file")
            assert field.task_id is None
            assert field.fieldset.task_id == task_id
            upload_args = {
                "task_id": task_id,
                "field_api_name": field.api_name,
                "filename": "мой report.txt",
                "content_type": "text/plain",
                "size": 3,

            }
            upload = tool(name="create_upload_link", arguments=upload_args)
            assert upload == tool(
                name="create_upload_link", arguments=upload_args
            )
            assert upload["filename"] == "мой_report.txt"
            capability = client.post(
                f"/integrations/mcp/uploads/{upload['id']}/token",
                headers=user_headers,
                json={},
            )
            assert capability.status_code == 200, capability.text
            with httpx.Client(
                base_url=storage_url, trust_env=False, timeout=20
            ) as files:
                transferred = files.post(
                    "/upload",
                    headers={
                        "Authorization": (
                            f"Bearer {capability.json()['access_token']}"
                        ),
                        "X-MCP-Upload-Session": upload["id"],
                    },
                    files={"file": (upload["filename"], b"abc", "text/plain")},
                )
                assert transferred.status_code == 200, transferred.text
                ready = tool(
                    name="get_upload_status",
                    arguments={"upload_id": upload["id"]},
                )
                assert ready["status"] == "ready"
                attached = tool(
                    name="attach_uploaded_file",
                    arguments={
                        "upload_id": upload["id"],
                        "task_id": task_id,

                    },
                )
                assert attached["status"] == "attached"
                assert Task.objects.get(pk=task_id).status == task.status
                attachment = Attachment.objects.get(
                    file_id=ready["file_id"],
                    workflow=task.workflow,
                    output=field,
                )
                detail = tool(
                    name="get_attachment",
                    arguments={"attachment_id": attachment.pk},
                )
                assert detail["file"]["name"] == upload["filename"]
                assert 0 < detail["download"]["expires_in"] <= 300
                download_path = urlparse(
                    detail["download"]["download_url"]
                ).path.removeprefix("/files")
                downloaded = files.get(download_path)
                assert downloaded.status_code == 200, downloaded.text
                assert downloaded.content == b"abc"
                assert downloaded.headers["cache-control"] == "no-store"
                assert downloaded.headers["referrer-policy"] == "no-referrer"
                partial = files.get(
                    download_path, headers={"Range": "bytes=1-2"}
                )
                assert partial.status_code == 206, partial.text
                assert partial.content == b"bc"
        completion = {"task_id": task_id, }
        assert tool(name="complete_task", arguments=completion)["id"] == task_id

        refreshed = client.post(
            "/oauth/mcp/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
                "client_id": client_id,
                "resource": settings.MCP_PUBLIC_URL,
            },
        )
        assert refreshed.status_code == 200, refreshed.text
        assert refreshed.json()["refresh_token"] != tokens["refresh_token"]
        mcp.headers["Authorization"] = (
            f"Bearer {refreshed.json()['access_token']}"
        )
        assert tool(name="list_my_tasks")["items"] == []
        if download_path:
            # A refresh invalidates source-bound tickets. Reissue and prove
            # live byte access immediately before revoking the connection.
            renewed_file = tool(
                name="get_attachment",
                arguments={"attachment_id": attachment.pk},
            )
            download_path = urlparse(
                renewed_file["download"]["download_url"]
            ).path.removeprefix("/files")
            live_file = httpx.get(
                storage_url + download_path, trust_env=False, timeout=20
            )
            assert live_file.status_code == 200, live_file.text
            assert live_file.content == b"abc"
        connection = Connection.objects.get(
            user=user, application__client_id=client_id
        )
        revoked = client.delete(
            f"/integrations/mcp/connections/{connection.pk}",
            headers=user_headers,
        )
        assert revoked.status_code == 204, revoked.text
        denied = mcp.post(
            "/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
        assert denied.status_code == 401
        if download_path:
            denied_file = httpx.get(
                storage_url + download_path, trust_env=False, timeout=20
            )
            assert denied_file.status_code in (401, 403), denied_file.text
        assert broker_mock.called
        analytics_track_mock.assert_not_called()
    finally:
        client.close()
        mcp.close()
        server.should_exit = True
        thread.join(timeout=10)
        listener.close()
        got_request_exception.disconnect(capture_core_exception)
        assert not thread.is_alive(), "MCP server failed to stop"
