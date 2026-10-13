import asyncio
import json
import time
from typing import Any

import httpx
import pytest
from conftest import SECRET, TOKEN_A, TOKEN_B, UPLOAD_ID, Service

from pneumatic_mcp.app import SERVER_INSTRUCTIONS
from pneumatic_mcp.errors import MESSAGES
from pneumatic_mcp.settings import SCOPE_ORDER, SCOPES


@pytest.mark.parametrize(
    argnames="token",
    argvalues=["a" * 4097, TOKEN_A + "=" * 4096],
)
async def test_verify_token__overlong_credentials__before_introspection(
    service: Service, token: str
):

    # arrange
    service.upstream.tokens[token] = service.upstream.tokens[TOKEN_A].copy()

    # act
    response = await service.rpc(method="tools/list", token=token)

    # assert
    assert response.status_code == 401
    assert not service.upstream.requests


async def test_initialize__legacy__sessionless(service: Service):

    # arrange
    params = {
        "protocolVersion": "2025-11-25",
        "capabilities": {},
        "clientInfo": {"name": "protocol-test", "version": "1"},
    }

    # act
    response = await service.rpc(method="initialize", params=params)

    # assert
    assert response.status_code == 200
    assert response.json()["result"]["protocolVersion"] == "2025-11-25"
    assert response.json()["result"]["instructions"] == SERVER_INSTRUCTIONS
    assert "mcp-session-id" not in response.headers


@pytest.mark.parametrize(
    argnames="method,path,status",
    argvalues=[
        ("POST", "/mcp/", 404),
        ("GET", "/mcp", 405),
        ("DELETE", "/mcp", 405),
        ("GET", "/sse", 404),
    ],
)
async def test_router__unsupported_routes__rejected(
    service: Service, method: str, path: str, status: int
):

    # arrange
    headers = {"Authorization": f"Bearer {TOKEN_A}"}

    # act
    response = await service.http.request(
        method=method, url=path, json={}, headers=headers
    )

    # assert
    assert response.status_code == status
    if status == 405:
        assert response.headers["allow"] == "POST"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert not service.upstream.business_requests
    assert not service.upstream.delegations


async def test_notification__initialized__accepted(service: Service):

    # arrange
    body = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    headers = {"Authorization": f"Bearer {TOKEN_A}"}

    # act
    response = await service.http.post(url="/mcp", headers=headers, json=body)

    # assert
    assert response.status_code == 202
    assert "mcp-session-id" not in response.headers
    assert not service.upstream.delegations


async def test_authentication__missing_token__challenge(service: Service):

    # arrange
    expected = (
        'Bearer error="invalid_token", '
        'error_description="Authentication required", '
        'resource_metadata="https://my.pneumatic.app/'
        '.well-known/oauth-protected-resource/mcp", '
        'scope="pneumatic:read"'
    )

    # act
    response = await service.rpc(method="tools/list", token=None)

    # assert
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == expected
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert not service.upstream.requests


@pytest.mark.parametrize(
    argnames="path",
    argvalues=[
        "/.well-known/oauth-protected-resource/mcp",
        "/.well-known/oauth-protected-resource",
    ],
)
async def test_metadata__supported_paths__all_scopes(
    service: Service, path: str
):

    # arrange
    expected = service.settings.public_url

    # act
    response = await service.http.get(url=path)

    # assert
    assert response.status_code == 200
    assert response.json()["scopes_supported"] == list(SCOPE_ORDER)
    assert set(response.json()["scopes_supported"]) == SCOPES
    assert response.json()["resource"] == expected
    assert response.json()["authorization_servers"] == [
        service.settings.issuer_url
    ]
    assert response.headers.get_list("cache-control") == ["no-store"]
    assert response.headers["referrer-policy"] == "no-referrer"


@pytest.mark.parametrize(
    argnames="path",
    argvalues=["/health", "/ready"],
)
async def test_router__diagnostic_routes__absent(service: Service, path: str):

    # arrange
    expected = 404

    # act
    response = await service.http.get(url=path)

    # assert
    assert response.status_code == expected


@pytest.mark.parametrize(
    argnames="change",
    argvalues=[
        {"active": False},
        {"active": "true"},
        {"exp": 1},
        {"exp": True},
        {"exp": "9999999999"},
        {"aud": "https://attacker.test/mcp"},
        {"aud": "https://my.pneumatic.app/mcp/"},
        {"aud": ["https://my.pneumatic.app/mcp", "https://attacker.test/mcp"]},
        {"scope": "mcp:read"},
        {"scope": "pneumatic:read admin"},
        {"scope": ""},
        {"connection_id": None},
        {"account_id": None},
        {"sub": "different-user"},
    ],
)
async def test_verify_token__invalid_claims__fail_closed(
    service: Service, change: dict[str, Any]
):

    # arrange
    service.upstream.tokens[TOKEN_A].update(change)

    expected = (
        503
        if any(key in change for key in {"connection_id", "account_id"})
        or change.get("active") == "true"
        or isinstance(change.get("exp"), bool)
        or change.get("exp") == "9999999999"
        else 401
    )

    # act
    response = await service.rpc(method="tools/list")

    # assert
    assert response.status_code == expected
    assert not service.upstream.business_requests
    assert not service.upstream.delegations


async def test_verify_token__singleton_audience__ok(service: Service):

    # arrange
    service.upstream.tokens[TOKEN_A]["aud"] = [service.settings.public_url]

    # act
    received = await service.rpc(method="tools/list")

    # assert
    assert (received).status_code == 200


@pytest.mark.parametrize(
    argnames="scopes",
    argvalues=[
        "pneumatic:read",
        "pneumatic:write",
        "files:read",
        "files:write",
        "pneumatic:write files:write",
    ],
)
async def test_list_tools__any_valid_scope__all_discoverable(
    service: Service, scopes: str
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = scopes

    # act
    response = await service.rpc(method="tools/list")
    listed = response.json()["result"]["tools"]

    # assert
    assert len(listed) == 18
    assert listed[1]["name"] == "get_template"
    assert listed[8]["name"] == "run_workflow"
    assert listed[9]["name"] == "complete_task"
    assert listed[11]["name"] == "comment_task"
    assert listed[13]["name"] == "get_attachment"
    assert listed[17]["name"] == "attach_uploaded_file"
    assert listed[0]["inputSchema"]["additionalProperties"] is False
    assert listed[8]["inputSchema"]["additionalProperties"] is False
    assert listed[17]["inputSchema"]["additionalProperties"] is False


@pytest.mark.parametrize(
    argnames="scope",
    argvalues=["pneumatic:write", "files:write", "pneumatic:read files:read"],
)
async def test_call_tool__attach_missing_scopes__denied(
    service: Service, scope: str
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = scope

    # act
    response = await service.tool(
        name="attach_uploaded_file",
        arguments={
            "task_id": 1,
            "upload_id": UPLOAD_ID,
        },
    )
    result = (response).json()["result"]

    # assert
    assert result["isError"] is True
    assert result["structuredContent"]["error"]["code"] == "insufficient_scope"
    assert not service.upstream.delegations


@pytest.mark.parametrize(
    argnames=("name", "args", "path", "body"),
    argvalues=[
        ("list_templates", {}, "/templates", None),
        ("get_template", {"template_id": 7}, "/templates/7", None),
        (
            "get_template_kickoff",
            {"template_id": 7},
            "/integrations/mcp/templates/7/kickoff",
            None,
        ),
        ("list_workflows", {}, "/workflows", None),
        ("get_workflow", {"workflow_id": 7}, "/workflows/7", None),
        (
            "get_workflow_events",
            {"workflow_id": 7},
            "/workflows/7/events",
            None,
        ),
        ("list_my_tasks", {}, "/v3/tasks", None),
        ("get_task", {"task_id": 7}, "/v2/tasks/7", None),
        ("list_attachments", {}, "/attachments", None),
        (
            "get_attachment",
            {"attachment_id": 7},
            "/integrations/mcp/attachments/7",
            None,
        ),
        (
            "get_upload_status",
            {"upload_id": UPLOAD_ID},
            f"/integrations/mcp/uploads/{UPLOAD_ID}",
            None,
        ),
        (
            "run_workflow",
            {"template_id": 7, "kickoff": {"text-1": "value"}},
            "/templates/7/run",
            {"kickoff": {"text-1": "value"}, "is_urgent": False},
        ),
        (
            "complete_task",
            {"task_id": 7, "output": {"text-1": "value"}},
            "/v2/tasks/7/complete",
            {"output": {"text-1": "value"}},
        ),
        (
            "add_workflow_comment",
            {"workflow_id": 7, "text": "A comment"},
            "/workflows/7/comment",
            {"text": "A comment"},
        ),
        (
            "comment_task",
            {"task_id": 7, "text": "A task comment"},
            "/v2/tasks/7/comment",
            {"text": "A task comment"},
        ),
        (
            "create_upload_link",
            {
                "task_id": 7,
                "field_api_name": "file-1",
                "filename": "note.pdf",
                "content_type": "application/pdf",
                "size": 42,
            },
            "/integrations/mcp/uploads",
            {
                "task_id": 7,
                "field_api_name": "file-1",
                "filename": "note.pdf",
                "content_type": "application/pdf",
                "size": 42,
            },
        ),
        (
            "import_attachment_from_url",
            {"upload_id": UPLOAD_ID, "url": "https://public.test/a.pdf"},
            f"/integrations/mcp/uploads/{UPLOAD_ID}/import",
            {"url": "https://public.test/a.pdf"},
        ),
        (
            "attach_uploaded_file",
            {"upload_id": UPLOAD_ID, "task_id": 7},
            f"/integrations/mcp/uploads/{UPLOAD_ID}/attach",
            {"task_id": 7},
        ),
    ],
)
async def test_call_tool__fixed_route__delegated_credentials(
    service: Service,
    name: str,
    args: dict[str, Any],
    path: str,
    body: Any,
):

    # arrange
    if name == "create_upload_link":
        body = {**body, "target_type": "task"}

    # act
    response = await service.tool(name=name, arguments=args)
    result = (response).json()["result"]

    # assert
    assert not result.get("isError"), result
    request = service.upstream.business_requests[-1]
    assert request.url.path == "/core-prefix" + path
    assert request.headers["authorization"].startswith("Bearer mcp-d_")
    assert request.headers["authorization"] != f"Bearer {TOKEN_A}"
    assert (
        request.method,
        json.loads(request.content) if request.content else None,
    ) == (
        "POST" if body is not None else "GET",
        body,
    )
    if body is not None:
        assert "Idempotency-Key" not in request.headers
    elif "limit" in request.url.params:
        assert request.url.params["limit"] == "20"
    if name == "create_upload_link":
        content = result["structuredContent"]["data"]
        assert "credential" not in content
        assert content["upload_url"].endswith(f"/mcp/uploads/{UPLOAD_ID}")


@pytest.mark.parametrize(
    argnames=("name", "args"),
    argvalues=[
        ("list_templates", {"limit": 0}),
        ("list_templates", {"limit": 101}),
        ("list_templates", {"limit": "20"}),
        ("list_templates", {"limit": True}),
        ("list_workflows", {"account_id": 202}),
        ("list_my_tasks", {"user_id": 22}),
        ("get_task", {"task_id": "../accounts"}),
        ("get_workflow", {"workflow_id": -1}),
        ("run_workflow", {"template_id": False}),
        (
            "complete_task",
            {"task_id": False},
        ),
        (
            "create_upload_link",
            {
                "task_id": 1,
                "field_api_name": "f",
                "filename": "../x",
                "content_type": "text/plain",
                "size": 1,
            },
        ),
        (
            "import_attachment_from_url",
            {
                "upload_id": UPLOAD_ID,
                "url": "https://user:pass@host/a",
            },
        ),
        (
            "import_attachment_from_url",
            {
                "upload_id": UPLOAD_ID,
                "url": "http://public.test/a",
            },
        ),
        (
            "import_attachment_from_url",
            {
                "upload_id": UPLOAD_ID,
                "url": "https://public.test:444/a",
            },
        ),
        (
            "attach_uploaded_file",
            {
                "upload_id": "invalid-uuid",
                "task_id": 1,
            },
        ),
    ],
)
async def test_call_tool__invalid_arguments__no_delegation(
    service: Service, name: str, args: dict[str, Any]
):

    # act

    # arrange
    result = (await service.tool(name=name, arguments=args)).json()["result"]

    # assert
    assert result["isError"] is True
    assert result["structuredContent"]["error"]["code"] == "invalid_arguments"
    assert (
        result["structuredContent"]["error"]["message"]
        == (MESSAGES["invalid_arguments"])
    )
    assert not service.upstream.delegations


async def test_call_tool__concurrent_users__isolated(service: Service):

    # act

    # arrange
    a, b = await asyncio.gather(
        service.tool(name="list_workflows", token=TOKEN_A),
        service.tool(name="list_workflows", token=TOKEN_B),
    )

    # assert
    assert (a).json()["result"]["structuredContent"]["data"]["items"][0][
        "id"
    ] == 101
    assert (b).json()["result"]["structuredContent"]["data"]["items"][0][
        "id"
    ] == 202
    first = service.upstream.business_requests[0].headers["authorization"]
    second = service.upstream.business_requests[1].headers["authorization"]
    assert first != second


@pytest.mark.parametrize(
    argnames="status", argvalues=[400, 401, 403, 404, 409, 429, 500, 302]
)
async def test_call_tool__core_error__redacted_without_retry(
    service: Service, status: int, caplog: pytest.LogCaptureFixture
):

    # arrange
    service.upstream.business_status = status
    service.upstream.business_body = {
        "detail": f"{SECRET} {TOKEN_A} https://private-source.test/a?code=topsecret",
    }

    # act
    response = await service.tool(
        name="run_workflow",
        arguments={
            "template_id": 1,
        },
    )
    result = (response).json()["result"]

    # assert
    assert result["isError"] is True
    assert result["structuredContent"]["error"]["retryable"] is False
    assert len(service.upstream.business_requests) == 1
    assert SECRET not in response.text
    assert TOKEN_A not in response.text
    assert "private-source.test" not in response.text
    assert SECRET not in caplog.text
    assert TOKEN_A not in caplog.text
    assert "private-source.test" not in caplog.text


@pytest.mark.parametrize(
    argnames="exception",
    argvalues=[
        httpx.ReadTimeout("secret failure"),
        httpx.ConnectError("secret failure"),
    ],
)
async def test_call_tool__write_network_failure__no_retry(
    service: Service, exception: httpx.HTTPError
):

    # arrange
    service.upstream.error = exception

    # act
    result = (
        await service.tool(
            name="complete_task",
            arguments={
                "task_id": 1,
            },
        )
    ).json()["result"]

    # assert
    assert result["isError"] is True
    assert (
        "outcome may be unknown"
        in result["structuredContent"]["error"]["message"]
    )
    assert len(service.upstream.business_requests) == 1
    assert len(service.upstream.delegations) == 1


@pytest.mark.parametrize(
    argnames="override",
    argvalues=[
        {"credential": TOKEN_A},
        {"credential": "pn-normal-api-key"},
        {"audience": "pneumatic-files"},
        {"scopes": ["pneumatic:read", "pneumatic:write"]},
        {"scopes": "pneumatic:read"},
        {"expires_at": int(time.time()) + 1000},
        {"expires_at": 0},
        {"operation": "get_task"},
        {"account_id": 202},
        {"connection_id": "connection-b"},
    ],
)
async def test_call_tool__malformed_grant__no_business_request(
    service: Service, override: dict[str, Any]
):

    # arrange
    service.upstream.delegate_override = override

    # act
    result = (await service.tool(name="list_workflows")).json()["result"]

    # assert
    assert result["structuredContent"]["error"]["code"] == "invalid_response"
    assert not service.upstream.business_requests


@pytest.mark.parametrize(
    argnames="headers,status",
    argvalues=[
        ({"Host": "evil.test"}, 421),
        ({"Origin": "https://evil.test"}, 403),
    ],
)
async def test_transport_security__untrusted_headers__no_delegation(
    service: Service, headers: dict[str, str], status: int
):

    # arrange
    method = "tools/list"

    # act
    response = await service.rpc(method=method, headers=headers)

    # assert
    assert response.status_code == status
    assert not service.upstream.business_requests
    assert not service.upstream.delegations
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"


async def test_uvicorn__overload__before_introspection(
    service_factory: Any,
):

    # arrange
    async with service_factory(max_concurrency=2) as service:
        service.upstream.release = asyncio.Event()
        pending = asyncio.create_task(service.tool(name="list_workflows"))

        # act
        await asyncio.wait_for(service.upstream.started.wait(), timeout=2)
        count = len(service.upstream.requests)
        try:
            busy = await service.rpc(method="tools/list")
        finally:
            service.upstream.release.set()
            await pending

        # assert
        assert busy.status_code == 503
        assert len(service.upstream.requests) == count
