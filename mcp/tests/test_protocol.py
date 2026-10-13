import json
from typing import Any
from urllib.parse import quote

import httpx
import httpx2
import jsonschema
import mcp_types as types
import pytest
from conftest import MODERN, SECRET, TOKEN_A, UPLOAD_ID, Service
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from pneumatic_mcp.outputs import MAX_RESULT_BYTES
from pneumatic_mcp.tool_catalog import TOOLS


@pytest.mark.parametrize(argnames="version", argvalues=["2025-11-25", MODERN])
@pytest.mark.parametrize(argnames="clear", argvalues=[None, [], ""])
async def test_complete_task__file_clear_consented__delegated(
    service: Service, version: str, clear: Any, modern_meta: Any
):
    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:write files:write"
    output = {"group": [{"file-1": clear}]}
    arguments = {
        "task_id": 7,
        "output": output,
    }
    params = {
        "name": "complete_task",
        "arguments": arguments,
        **({"_meta": modern_meta()} if version == MODERN else {}),
    }
    headers = {
        "MCP-Protocol-Version": version,
        "MCP-Method": "tools/call",
        "MCP-Name": "complete_task",
    }

    # act
    response = await service.rpc(
        method="tools/call", params=params, headers=headers
    )

    # assert
    assert response.status_code == 200
    assert response.json()["result"]["isError"] is False
    assert "www-authenticate" not in response.headers
    assert len(service.upstream.delegations) == 1
    assert list(service.upstream.delegations.values())[0]["scopes"] == [
        "pneumatic:write",
        "files:write",
    ]
    assert json.loads(service.upstream.business_requests[0].content) == {
        "output": output
    }
    assert "idempotency-key" not in (
        service.upstream.business_requests[0].headers
    )


async def test_discover__modern__without_initialize(
    service: Service, modern_meta: Any
):

    # act

    # arrange
    response = await service.rpc(
        method="server/discover",
        params={"_meta": modern_meta()},
        headers={
            "MCP-Protocol-Version": MODERN,
            "MCP-Method": "server/discover",
        },
    )

    # assert
    assert response.status_code == 200, response.text
    assert MODERN in response.json()["result"]["supportedVersions"]
    assert "mcp-session-id" not in response.headers


async def test_call_tool__modern_without_initialize__ok(
    service: Service, modern_meta: Any
):

    # act

    # arrange
    response = await service.rpc(
        method="tools/call",
        params={
            "_meta": modern_meta(),
            "name": "get_workflow",
            "arguments": {"workflow_id": 7},
        },
        headers={
            "MCP-Protocol-Version": MODERN,
            "MCP-Method": "tools/call",
            "MCP-Name": "get_workflow",
        },
    )

    # assert
    assert response.status_code == 200, response.text
    assert response.json()["result"]["structuredContent"]["data"]["id"] == 101
    assert "mcp-session-id" not in response.headers


@pytest.mark.parametrize(
    argnames="headers, meta_version",
    argvalues=[
        (
            {"MCP-Method": "tools/list", "MCP-Name": "get_workflow"},
            MODERN,
        ),
        ({"MCP-Method": "tools/call", "MCP-Name": "get_task"}, MODERN),
        (
            {"MCP-Method": "tools/call", "MCP-Name": "get_workflow"},
            "2025-11-25",
        ),
    ],
)
async def test_call_tool__header_mismatch__before_execution(
    service: Service,
    headers: dict[str, str],
    meta_version: str,
    modern_meta: Any,
):

    # act

    # arrange
    response = await service.rpc(
        method="tools/call",
        params={
            "_meta": modern_meta(version=meta_version),
            "name": "get_workflow",
            "arguments": {"workflow_id": 7},
        },
        headers={"MCP-Protocol-Version": MODERN, **headers},
    )

    # assert
    assert response.status_code == 400, response.text
    assert response.json()["error"]["code"] == types.HEADER_MISMATCH
    assert not service.upstream.delegations


@pytest.mark.parametrize(argnames="mode", argvalues=["legacy", "auto"])
async def test_sdk_client__tool_call__ok(service: Service, mode: str):

    # arrange
    async with httpx2.AsyncClient(
        trust_env=False,
        headers={
            "Host": "test-host",
            "Authorization": f"Bearer {TOKEN_A}",
        },
    ) as http:
        transport = streamable_http_client(
            service.url + "/mcp", http_client=http
        )
        async with Client(
            transport, mode=mode, read_timeout_seconds=5
        ) as client:
            # act
            response = await client.call_tool(
                name="get_workflow", arguments={"workflow_id": 7}
            )

            # assert
            assert not response.is_error
            assert response.structured_content["data"]["id"] == 101


@pytest.mark.parametrize(argnames="mode", argvalues=["legacy", "auto"])
async def test_sdk_client__tools_list__ok(service: Service, mode: str):

    # arrange
    async with httpx2.AsyncClient(
        trust_env=False,
        headers={
            "Host": "test-host",
            "Authorization": f"Bearer {TOKEN_A}",
        },
    ) as http:
        transport = streamable_http_client(
            service.url + "/mcp", http_client=http
        )
        async with Client(
            transport, mode=mode, read_timeout_seconds=5
        ) as client:
            # act
            response = await client.list_tools()

            # assert
            assert len(response.tools) == 18


async def test_call_tool__step_up__http_and_chatgpt_challenge(
    service: Service,
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:read"

    arguments = {
        "template_id": 7,
    }

    # act
    response = await service.tool(name="run_workflow", arguments=arguments)

    # assert
    assert response.status_code == 403
    challenge = response.headers["www-authenticate"]
    assert challenge == (
        'Bearer error="insufficient_scope", '
        'error_description="Additional permissions are '
        'required for this tool.", '
        'scope="pneumatic:write", '
        'resource_metadata="https://my.pneumatic.app/.well-known/oauth-protected-resource/mcp"'
    )
    assert response.json()["result"]["_meta"]["mcp/www_authenticate"] == [
        challenge
    ]
    assert response.headers.get_list("www-authenticate") == [challenge]
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert not service.upstream.delegations


@pytest.mark.parametrize(argnames="version", argvalues=["2025-11-25", MODERN])
@pytest.mark.parametrize(
    argnames="name,scopes",
    argvalues=[
        ("list_templates", ["pneumatic:read"]),
        ("get_template", ["pneumatic:read"]),
        ("get_template_kickoff", ["pneumatic:read"]),
        ("list_workflows", ["pneumatic:read"]),
        ("get_workflow", ["pneumatic:read"]),
        ("get_workflow_events", ["pneumatic:read"]),
        ("list_my_tasks", ["pneumatic:read"]),
        ("get_task", ["pneumatic:read"]),
        ("run_workflow", ["pneumatic:write"]),
        ("complete_task", ["pneumatic:write"]),
        ("add_workflow_comment", ["pneumatic:write"]),
        ("comment_task", ["pneumatic:write"]),
        ("list_attachments", ["files:read"]),
        ("get_attachment", ["files:read"]),
        ("get_upload_status", ["files:read"]),
        ("create_upload_link", ["files:write"]),
        ("import_attachment_from_url", ["files:write"]),
        ("attach_uploaded_file", ["pneumatic:write", "files:write"]),
    ],
)
async def test_list_tools__both_versions__oauth_schemes(
    service: Service,
    version: str,
    name: str,
    scopes: list[str],
    modern_meta: Any,
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:read"
    params = {"_meta": modern_meta()} if version == MODERN else {}
    headers = {"MCP-Protocol-Version": version, "MCP-Method": "tools/list"}
    schemes = [{"type": "oauth2", "scopes": scopes}]

    # act
    response = await service.rpc(
        method="tools/list", params=params, headers=headers
    )
    tools = {tool["name"]: tool for tool in response.json()["result"]["tools"]}
    declared = (
        TOOLS[name].schema().model_dump(by_alias=True, exclude_none=True)
    )

    # assert
    assert response.status_code == 200
    assert len(tools) == 18
    assert tools[name]["securitySchemes"] == schemes
    assert tools[name]["_meta"]["securitySchemes"] == schemes
    assert declared["securitySchemes"] == schemes
    assert declared["_meta"]["securitySchemes"] == schemes


async def test_call_tool__runtime_revocation__safe_challenge(
    service: Service,
):

    # arrange
    service.upstream.business_status = 401
    service.upstream.business_body = {
        "detail": f"private message {TOKEN_A} {SECRET}"
    }

    # act
    response = await service.tool(
        name="get_workflow", arguments={"workflow_id": 7}
    )

    # assert
    assert response.status_code == 401
    challenge = response.headers["www-authenticate"]
    assert challenge == (
        'Bearer error="invalid_token", '
        'error_description="Authentication is required. '
        'Reconnect this account.", '
        'scope="pneumatic:read", '
        'resource_metadata="https://my.pneumatic.app/.well-known/oauth-protected-resource/mcp"'
    )
    result = response.json()["result"]
    assert result["isError"] is True
    assert result["_meta"]["mcp/www_authenticate"] == [challenge]
    assert TOKEN_A not in response.text and SECRET not in response.text
    assert len(service.upstream.business_requests) == 1


@pytest.mark.parametrize(
    argnames="body",
    argvalues=[
        {"code": "service_auth_failed", "detail": "private config failure"},
        {"detail": "old private authentication failure"},
        {"code": "unknown_private_error"},
        [],
    ],
)
async def test_delegate__service_auth_failure__no_reconnect(
    service: Service, body: Any
):

    # arrange
    service.upstream.delegate_status = 401
    service.upstream.delegate_error_body = body

    # act
    response = await service.tool(
        name="get_workflow", arguments={"workflow_id": 7}
    )

    # assert
    assert response.status_code == 503
    assert response.headers["retry-after"] == "1"
    assert "www-authenticate" not in response.headers
    result = response.json()["result"]
    assert (
        result["structuredContent"]["error"]["code"]
        == "authorization_unavailable"
    )
    assert "_meta" not in result
    assert not service.upstream.business_requests


async def test_delegate__source_revoked__auth_challenge(
    service: Service,
):

    # arrange
    service.upstream.delegate_status = 401
    service.upstream.delegate_error_body = {
        "code": "invalid_token",
        "detail": SECRET,
    }

    # act
    response = await service.tool(
        name="get_workflow", arguments={"workflow_id": 7}
    )

    # assert
    assert response.status_code == 401
    assert 'error="invalid_token"' in response.headers["www-authenticate"]
    assert response.json()["result"]["_meta"]["mcp/www_authenticate"]
    assert SECRET not in response.text
    assert not service.upstream.business_requests


@pytest.mark.parametrize(
    argnames="name, id_key, values_key",
    argvalues=[
        ("run_workflow", "template_id", "kickoff"),
        ("complete_task", "task_id", "output"),
    ],
)
@pytest.mark.parametrize(argnames="nested", argvalues=[False, True])
async def test_call_tool__nested_upload_refs__file_delegation(
    service: Service, name: str, id_key: str, values_key: str, nested: bool
):

    # arrange
    fields = {"file-1": [{"upload_id": UPLOAD_ID}]}
    values = {"group-1": [{"nested": fields}]} if nested else fields
    args = {
        id_key: 7,
        values_key: values,
    }

    # act
    response = await service.tool(name=name, arguments=args)

    # assert
    assert not response.json()["result"]["isError"], response.text
    grant = list(service.upstream.delegations.values())[-1]
    assert set(grant["scopes"]) == {
        "pneumatic:write",
        "files:read",
        "files:write",
    }
    assert (
        json.loads(service.upstream.business_requests[-1].content)[values_key]
        == values
    )


@pytest.mark.parametrize(
    argnames="name, id_key, values_key",
    argvalues=[
        ("run_workflow", "template_id", "kickoff"),
        ("complete_task", "task_id", "output"),
    ],
)
async def test_call_tool__upload_without_scope__no_delegation(
    service: Service,
    name: str,
    id_key: str,
    values_key: str,
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:write"

    # act
    response = await service.tool(
        name=name,
        arguments={
            id_key: 7,
            values_key: {"group-1": [{"file-1": [{"upload_id": UPLOAD_ID}]}]},
        },
    )

    # assert
    assert response.status_code == 403
    challenge = response.headers["www-authenticate"]
    assert 'scope="pneumatic:write files:write"' in challenge
    assert response.json()["result"]["_meta"]["mcp/www_authenticate"] == [
        challenge
    ]
    assert not service.upstream.delegations


@pytest.mark.parametrize(
    argnames="output",
    argvalues=[
        {},
        {"text-1": []},
        {"group": [{"text-1": None}]},
        {"text-1": ""},
    ],
)
async def test_complete_task__ordinary_values__workflow_scope(
    service: Service, output: dict[str, Any]
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:write"

    # act
    response = await service.tool(
        name="complete_task",
        arguments={
            "task_id": 7,
            "output": output,
        },
    )

    # assert
    assert not response.json()["result"]["isError"], response.text
    assert list(service.upstream.delegations.values())[-1]["scopes"] == [
        "pneumatic:write"
    ]


@pytest.mark.parametrize(argnames="version", argvalues=["2025-11-25", MODERN])
@pytest.mark.parametrize(argnames="clear", argvalues=[None, [], ""])
async def test_complete_task__file_clear_denied__scope_challenge(
    service: Service, version: str, clear: Any, modern_meta: Any
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:write"
    service.upstream.business_status = 403
    service.upstream.business_body = {
        "code": "insufficient_scope",
        "required_scopes": ["pneumatic:write", "files:write"],
        "detail": f"private field info {TOKEN_A} {SECRET}",
    }
    arguments = {
        "task_id": 7,
        "output": {"group": [{"file-1": clear}]},
    }

    # act
    denied = await service.rpc(
        method="tools/call",
        params={
            "name": "complete_task",
            "arguments": arguments,
            **({"_meta": modern_meta()} if version == MODERN else {}),
        },
        headers={
            "MCP-Protocol-Version": version,
            "MCP-Method": "tools/call",
            "MCP-Name": "complete_task",
        },
    )

    # assert
    assert denied.status_code == 403, denied.text
    challenge = denied.headers["www-authenticate"]
    assert 'scope="pneumatic:write files:write"' in challenge
    assert (
        'error="insufficient_scope"' in challenge
        and "error_description=" in challenge
    )
    result = denied.json()["result"]
    assert result["_meta"]["mcp/www_authenticate"] == [challenge]
    assert result["structuredContent"]["error"]["required_scopes"] == [
        "pneumatic:write",
        "files:write",
    ]
    assert TOKEN_A not in denied.text and SECRET not in denied.text
    assert len(service.upstream.business_requests) == 1
    assert list(service.upstream.delegations.values())[-1]["scopes"] == [
        "pneumatic:write"
    ]


@pytest.mark.parametrize(argnames="version", argvalues=["2025-11-25", MODERN])
async def test_call_tool__core_scope_error__union_permissions(
    service: Service, version: str, modern_meta: Any
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:write"
    service.upstream.business_status = 403
    service.upstream.business_body = {
        "code": "insufficient_scope",
        "required_scopes": ["files:read", "files:write", "files:read"],
        "detail": f"untrusted header\r\n{SECRET}",
    }

    # act
    response = await service.rpc(
        method="tools/call",
        params={
            "name": "complete_task",
            "arguments": {
                "task_id": 7,
            },
            **({"_meta": modern_meta()} if version == MODERN else {}),
        },
        headers={
            "MCP-Protocol-Version": version,
            "MCP-Method": "tools/call",
            "MCP-Name": "complete_task",
        },
    )

    # assert
    assert response.status_code == 403, response.text
    challenge = response.headers["www-authenticate"]
    assert 'scope="pneumatic:write files:read files:write"' in challenge
    assert response.json()["result"]["_meta"]["mcp/www_authenticate"] == [
        challenge
    ]
    assert "untrusted" not in challenge and SECRET not in response.text
    assert len(service.upstream.business_requests) == 1


@pytest.mark.parametrize(
    argnames="required",
    argvalues=[
        None,
        [],
        "files:write",
        ["admin"],
        ["files:write\r\nInjected"],
        [False],
    ],
)
async def test_call_tool__invalid_scope_error__no_relink(
    service: Service, required: Any
):

    # arrange
    service.upstream.business_status = 403
    service.upstream.business_body = {
        "code": "insufficient_scope",
        "required_scopes": required,
    }

    # act
    response = await service.tool(
        name="complete_task",
        arguments={
            "task_id": 7,
        },
    )
    result = response.json()["result"]

    # assert
    assert result["structuredContent"]["error"]["code"] == "invalid_response"
    assert "_meta" not in result and "www-authenticate" not in response.headers
    assert len(service.upstream.business_requests) == 1


@pytest.mark.parametrize(
    argnames="name, arguments",
    argvalues=[
        ("get_workflow", {"workflow_id": 7}),
        (
            "run_workflow",
            {
                "template_id": 7,
            },
        ),
    ],
)
async def test_workflow__kickoff_fieldsets__preserved(
    service: Service, name: str, arguments: dict[str, Any]
):

    # arrange
    service.upstream.business_body = {
        "id": 7,
        "name": "W",
        "kickoff": {
            "output": [],
            "fieldsets": [
                {
                    "api_name": "group",
                    "fields": [{"api_name": "f", "value": "important"}],
                }
            ],
        },
    }

    # act
    response = await service.tool(name=name, arguments=arguments)
    result = response.json()["result"]["structuredContent"]

    # assert
    assert result["truncated"] is False
    assert (
        result["data"]["kickoff_fieldsets"][0]["fields"][0]["value"]
        == "important"
    )
    jsonschema.validate(result, TOOLS[name].schema().output_schema)


async def test_list_attachments__filters_and_page__forwarded(service: Service):

    # act

    # arrange
    response = await service.tool(
        name="list_attachments",
        arguments={
            "task_id": 7,
            "workflow_id": 9,
            "limit": 1,
            "offset": 2,
        },
    )

    # assert
    assert not response.json()["result"]["isError"]
    request = service.upstream.business_requests[-1]
    assert dict(request.url.params) == {
        "task_id": "7",
        "workflow_id": "9",
        "limit": "1",
        "offset": "2",
    }


@pytest.mark.parametrize(
    argnames="text",
    argvalues=[
        "[Report](https://my.pneumatic.app/files/abcdefgh-1234.pdf)",
        '![Image](https://my.pneumatic.app:443/files/abcdefgh.png "caption")',
        "https://my.pneumatic.app/files/abcdefgh.pdf?download=1",
    ],
)
async def test_comment__file_reference__file_scopes(
    service: Service, text: str
):

    # act

    # arrange
    response = await service.tool(
        name="add_workflow_comment",
        arguments={
            "workflow_id": 7,
            "text": text,
        },
    )

    # assert
    assert not response.json()["result"]["isError"], response.text
    assert set(list(service.upstream.delegations.values())[-1]["scopes"]) == {
        "pneumatic:write",
        "files:read",
        "files:write",
    }


async def test_comment__missing_file_read__step_up(service: Service):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:write files:write"

    # act
    response = await service.tool(
        name="add_workflow_comment",
        arguments={
            "workflow_id": 7,
            "text": "[Report](https://my.pneumatic.app/files/abcdefgh.pdf)",
        },
    )

    # assert
    assert response.status_code == 403
    assert (
        'scope="pneumatic:write files:read files:write"'
        in response.headers["www-authenticate"]
    )
    assert not service.upstream.delegations


@pytest.mark.parametrize(
    argnames="text",
    argvalues=[
        "A plain comment",
        "[External](https://drive.google.com/doc/abcdefgh)",
        "[report](https://example.org/files/report123.pdf)",
        "[report](https://my.pneumatic.app.evil.test/files/report123.pdf)",
        "https://my.pneumatic.app/files/mcp/download/" + "x" * 43,
        "https://user:password@my.pneumatic.app/files/abcdefgh.pdf",
    ],
)
async def test_comment__ordinary_text__minimal_scope(
    service: Service, text: str
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:write"

    # act
    response = await service.tool(
        name="add_workflow_comment",
        arguments={
            "workflow_id": 7,
            "text": text,
        },
    )

    # assert
    assert not response.json()["result"]["isError"]
    assert list(service.upstream.delegations.values())[-1]["scopes"] == [
        "pneumatic:write"
    ]


@pytest.mark.parametrize(
    argnames="name,id_key,values_key",
    argvalues=[
        ("run_workflow", "template_id", "kickoff"),
        ("complete_task", "task_id", "output"),
    ],
)
@pytest.mark.parametrize(
    argnames="text",
    argvalues=[
        "https://my.pneumatic.app/files/abcdefgh.pdf",
        "[Report](https://my.pneumatic.app/files/abcdefgh.pdf)",
    ],
)
async def test_call_tool__nested_file_links__file_scopes(
    service: Service, name: str, id_key: str, values_key: str, text: str
):

    # arrange
    args = {
        id_key: 7,
        values_key: {"group": [{"text-1": text}]},
    }

    # act
    response = await service.tool(name=name, arguments=args)

    # assert
    assert (
        response.status_code == 200
        and not response.json()["result"]["isError"]
    ), response.text
    assert set(list(service.upstream.delegations.values())[-1]["scopes"]) == {
        "pneumatic:write",
        "files:read",
        "files:write",
    }


@pytest.mark.parametrize(
    argnames="name,arguments,path",
    argvalues=[
        (
            "run_workflow",
            {"template_id": 7, "kickoff": {"text-1": "ordinary text"}},
            "/templates/7/run",
        ),
        (
            "complete_task",
            {"task_id": 7, "output": {"text-1": "ordinary text"}},
            "/v2/tasks/7/complete",
        ),
        (
            "add_workflow_comment",
            {"workflow_id": 7, "text": "ordinary text"},
            "/workflows/7/comment",
        ),
    ],
)
async def test_call_tool__existing_consent__path_bound_scopes(
    service: Service, name: str, arguments: dict[str, Any], path: str
):

    # act

    # arrange
    response = await service.tool(
        name=name,
        arguments={
            **arguments,
        },
    )

    # assert
    assert (
        response.status_code == 200
        and not response.json()["result"]["isError"]
    )
    grant = list(service.upstream.delegations.values())[-1]
    assert set(grant["scopes"]) == {
        "pneumatic:write",
        "files:read",
        "files:write",
    }
    assert (
        grant["tool"] == name
        and grant["path"] == path
        and grant["method"] == "POST"
    )


@pytest.mark.parametrize(argnames="status", argvalues=[401, 403, 500, 302])
async def test_verify_token__private_outage__no_challenge(
    service: Service, status: int
):

    # arrange
    service.upstream.introspection_status = status

    # act
    response = await service.rpc(method="tools/list")

    # assert
    assert response.status_code == 503
    assert "www-authenticate" not in response.headers
    assert response.json()["error"] == "authorization_unavailable"
    assert response.headers["retry-after"] == "1"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert TOKEN_A not in response.text and SECRET not in response.text


@pytest.mark.parametrize(
    argnames="body", argvalues=[{}, [], {"active": "true"}]
)
async def test_verify_token__malformed_response__unavailable(
    service: Service, body: Any
):

    # arrange
    service.upstream.introspection_body = body

    # act
    received = await service.rpc(method="tools/list")

    # assert
    assert (received).status_code == 503


async def test_verify_token__timeout__unavailable(service: Service):

    # arrange
    service.upstream.introspection_error = httpx.ReadTimeout(
        "sensitive diagnostics"
    )

    # act
    received = await service.rpc(method="tools/list")

    # assert
    assert (received).status_code == 503


@pytest.mark.parametrize(
    argnames="path",
    argvalues=[
        "/mcp",
        "/.well-known/oauth-protected-resource/mcp",
        "/.well-known/oauth-protected-resource",
    ],
)
async def test_mcp_enabled__disabled__unavailable(
    service_factory: Any, path: str
):

    # arrange
    async with service_factory(enabled=False) as service:
        method = "POST" if path == "/mcp" else "GET"

        # act
        response = await service.http.request(method=method, url=path)

        # assert
        assert response.status_code == 503
        assert response.json() == {"error": "disabled"}
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert not service.upstream.requests


@pytest.mark.parametrize(
    argnames="name,readonly,destructive,openworld",
    argvalues=[
        ("get_workflow", True, False, False),
        ("get_task", True, False, False),
        ("list_templates", True, False, False),
        ("get_attachment", True, False, False),
        ("complete_task", False, True, True),
        ("run_workflow", False, False, True),
        ("add_workflow_comment", False, False, False),
        ("attach_uploaded_file", False, False, False),
        ("import_attachment_from_url", False, False, True),
    ],
)
async def test_list_tools__annotations_and_schema__correct(
    service: Service,
    name: str,
    readonly: bool,
    destructive: bool,
    openworld: bool,
):

    # arrange
    method = "tools/list"

    # act
    response = await service.rpc(method=method)
    tools = {tool["name"]: tool for tool in response.json()["result"]["tools"]}
    tool = tools[name]

    # assert
    assert response.status_code == 200
    assert tool["title"]
    assert tool["outputSchema"]["required"] == ["data"]
    assert tool["annotations"] == {
        "readOnlyHint": readonly,
        "destructiveHint": destructive,
        "idempotentHint": readonly,
        "openWorldHint": openworld,
    }


async def test_get_attachment__output__matches_schema(service: Service):

    # arrange
    arguments = {"attachment_id": 7}
    schema = TOOLS["get_attachment"].schema().output_schema

    # act
    response = await service.tool(name="get_attachment", arguments=arguments)
    content = response.json()["result"]["structuredContent"]

    # assert
    assert response.status_code == 200
    jsonschema.validate(instance=content, schema=schema)
    assert content["data"]["download"]["download_url"] == (
        "https://my.pneumatic.app/files/mcp/download/" + "x" * 43
    )
    assert len(service.upstream.file_requests) == 2


@pytest.mark.parametrize(argnames="version", argvalues=["2025-11-25", MODERN])
@pytest.mark.parametrize(
    argnames="file_id",
    argvalues=[
        "NiihssB_Drawing (v2).odg",
        "Схема процесса 日本語.odg",
        "🧪" * 512,
    ],
)
async def test_get_attachment__legacy_file_id__preserved(
    service: Service, version: str, file_id: str, modern_meta: Any
):

    # arrange
    service.upstream.attachment_file_id = file_id

    # act
    response = await service.rpc(
        method="tools/call",
        params={
            "name": "get_attachment",
            "arguments": {"attachment_id": 7},
            **({"_meta": modern_meta()} if version == MODERN else {}),
        },
        headers={
            "MCP-Protocol-Version": version,
            "MCP-Method": "tools/call",
            "MCP-Name": "get_attachment",
        },
    )

    # assert
    assert (
        response.status_code == 200
        and not response.json()["result"]["isError"]
    ), response.text
    content = response.json()["result"]["structuredContent"]
    assert content["data"]["attachment"]["file_id"] == file_id
    assert content["data"]["file"]["file_id"] == file_id
    prefix = "/mcp/files/" + quote(string=file_id, safe="")
    grants = list(service.upstream.delegations.values())
    assert grants[0]["path"] == "/integrations/mcp/attachments/7"
    assert grants[1]["path"] == prefix
    assert grants[2]["path"] == prefix + "/download-ticket"
    assert service.upstream.file_requests[0].url.raw_path.decode() == prefix
    assert service.upstream.file_requests[1].url.raw_path.decode() == (
        prefix + "/download-ticket"
    )
    assert grants[0]["scopes"] == ["files:read"]
    assert grants[1]["scopes"] == ["files:read"]
    assert grants[2]["scopes"] == ["files:read"]
    jsonschema.validate(
        content, TOOLS["get_attachment"].schema().output_schema
    )


@pytest.mark.parametrize(
    argnames="file_id",
    argvalues=[
        "../secret",
        r"folder\file",
        "file?query",
        "file#fragment",
        "%2Fsecret",
        "control\x00",
        "bidi\u202e",
        ".",
        "..",
        "   ",
    ],
)
async def test_get_attachment__unsafe_file_id__no_file_requests(
    service: Service, file_id: str
):

    # arrange
    service.upstream.attachment_file_id = file_id

    # act
    response = await service.tool(
        name="get_attachment", arguments={"attachment_id": 7}
    )

    # assert
    assert (
        response.json()["result"]["structuredContent"]["error"]["code"]
        == "invalid_response"
    )
    assert (
        len(service.upstream.delegations) == 1
    )  # Core authorizes the record first.
    assert not service.upstream.file_requests


async def test_normalize__large_core_results__compact(
    service: Service,
):

    # arrange
    service.upstream.business_body = {
        "count": 100,
        "results": [
            {
                "id": index + 1,
                "name": "N" * 1000,
                "description": "D" * 2000,
                "owners": [{"email": "sensitive@example.test"}],
                "unused_internal_field": SECRET,
            }
            for index in range(100)
        ],
    }

    # act
    response = await service.tool(
        name="list_templates", arguments={"limit": 100}
    )
    content = response.json()["result"]["structuredContent"]

    # assert
    assert content["truncated"] is True
    assert (
        len(json.dumps(content, ensure_ascii=False).encode())
        <= MAX_RESULT_BYTES
    )
    assert (
        "owners" not in response.text
        and "unused_internal_field" not in response.text
    )
    assert len(content["data"]["items"]) <= 100


@pytest.mark.parametrize(
    argnames="tool",
    argvalues=["get_template_kickoff", "get_task", "get_workflow"],
)
async def test_normalize__rest_selections__compact_choices(
    service: Service, tool: str
):

    # arrange
    fields = [
        {
            "api_name": "choice-1",
            "name": "Choice",
            "type": "radio",
            "is_required": True,
            "is_hidden": False,
            "default": "One",
            "selections": ["One", "Two"],
        }
    ]
    service.upstream.business_body = {
        "id": 7,
        "name": "Object",
        "template_id": 7,
        "kickoff": {"fields": fields, "output": fields},
        "output": fields,
    }
    id_key = {
        "get_template_kickoff": "template_id",
        "get_task": "task_id",
        "get_workflow": "workflow_id",
    }[tool]

    # act
    response = await service.tool(name=tool, arguments={id_key: 7})

    # assert
    assert not response.json()["result"]["isError"], response.text
    data = response.json()["result"]["structuredContent"]["data"]
    field = data[
        {
            "get_template_kickoff": "fields",
            "get_task": "output",
            "get_workflow": "kickoff",
        }[tool]
    ][0]
    assert field["selections"] == [{"value": "One"}, {"value": "Two"}]
    assert field["default"] == "One" and field["is_hidden"] is False


async def test_call_tool__object_permission_denied__no_relink(
    service: Service,
):

    # arrange
    service.upstream.business_status = 403
    service.upstream.business_body = {
        "code": "permission_denied",
        "required_scopes": ["files:write"],
        "detail": SECRET,
    }

    # act
    response = await service.tool(
        name="get_workflow", arguments={"workflow_id": 7}
    )
    result = response.json()["result"]

    # assert
    assert result["isError"]
    assert result["structuredContent"]["error"]["code"] == "forbidden"
    assert "_meta" not in result and "www-authenticate" not in response.headers


async def test_create_upload_link__kickoff_target__ok(service: Service):

    # arrange
    args = {
        "template_id": 7,
        "field_api_name": "file-1",
        "filename": "note.pdf",
        "content_type": "application/pdf",
        "size": 42,
    }

    # act
    response = await service.tool(name="create_upload_link", arguments=args)

    # assert
    assert not response.json()["result"]["isError"], response.text
    request = service.upstream.business_requests[-1]
    assert json.loads(request.content)["target_type"] == "kickoff"


async def test_run_workflow__kickoff_upload_reference__delegated(
    service: Service,
):

    # arrange
    body = {
        "template_id": 7,
        "kickoff": {"file-1": [{"upload_id": UPLOAD_ID}]},
    }

    # act
    response = await service.tool(name="run_workflow", arguments=body)

    # assert
    assert not response.json()["result"]["isError"]
    assert (
        json.loads(service.upstream.business_requests[-1].content)["kickoff"]
        == body["kickoff"]
    )
    grant = list(service.upstream.delegations.values())[-1]
    assert set(grant["scopes"]) == {
        "pneumatic:write",
        "files:read",
        "files:write",
    }


async def test_run_workflow__upload_missing_scope__denied(
    service: Service,
):

    # arrange
    service.upstream.tokens[TOKEN_A]["scope"] = "pneumatic:write"

    # act
    response = await service.tool(
        name="run_workflow",
        arguments={
            "template_id": 7,
            "kickoff": {"file-1": [{"upload_id": UPLOAD_ID}]},
        },
    )

    # assert
    assert response.status_code == 403
    challenge = response.headers["www-authenticate"]
    assert 'scope="pneumatic:write files:write"' in challenge
    assert response.json()["result"]["_meta"]["mcp/www_authenticate"] == [
        challenge
    ]
    assert not service.upstream.delegations


@pytest.mark.parametrize(
    argnames="targets",
    argvalues=[
        {},
        {"task_id": 1, "template_id": 7},
        {"template_id": 7, "target_type": "task"},
    ],
)
async def test_create_upload_link__invalid_target__no_delegation(
    service: Service, targets: dict[str, Any]
):

    # act

    # arrange
    response = await service.tool(
        name="create_upload_link",
        arguments={
            **targets,
            "field_api_name": "f",
            "filename": "a.txt",
            "content_type": "text/plain",
            "size": 1,
        },
    )

    # assert
    assert (
        response.json()["result"]["structuredContent"]["error"]["code"]
        == "invalid_arguments"
    )
    assert not service.upstream.delegations


async def test_call_tool__oversized_body__no_delegation(service_factory: Any):

    # arrange
    async with service_factory(max_request_bytes=1024) as service:
        # act
        response = await service.tool(
            name="complete_task",
            arguments={
                "task_id": 7,
                "output": {"text": "A" * 2000},
            },
        )

        # assert
        assert response.status_code == 413
        assert not service.upstream.delegations


async def test_call_tool__write_timeout__no_retry(service_factory: Any):

    # arrange
    async with service_factory(call_timeout=0.03) as service:
        service.upstream.delay = 0.1

        # act
        response = await service.tool(
            name="complete_task",
            arguments={
                "task_id": 7,
            },
        )

        # assert
        assert (
            response.json()["result"]["structuredContent"]["error"]["code"]
            == "timeout"
        )
        assert len(service.upstream.business_requests) == 1
