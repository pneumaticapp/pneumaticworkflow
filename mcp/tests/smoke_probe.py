"""Run inside the production image against real HTTP MCP/core/Redis
containers."""

import asyncio
import json
from argparse import ArgumentParser
from typing import Any

import httpx
import httpx2
import mcp_types as types
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from smoke_core import (
    DELEGATE_REVOKED,
    DELEGATE_SERVICE_FAILURE,
    LEGACY_FILES,
    OUTAGE,
    READ_ONLY,
    RESOURCE,
    SOURCE,
    WRITE_ONLY,
)

ENDPOINT = "http://mcp:8000/mcp"
HOST = "my.pneumatic.app"


async def main(*, endpoint: str = ENDPOINT, startup_only: bool = False):
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
    headers = {
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-11-25",
    }
    async with httpx.AsyncClient(
        trust_env=False, timeout=5, headers={"Host": HOST}
    ) as raw:
        async with asyncio.timeout(30):
            while True:
                try:
                    started = await raw.post(
                        endpoint,
                        json=body,
                        headers={
                            **headers,
                            "Authorization": f"Bearer {READ_ONLY}",
                        },
                    )
                    if started.status_code == 200:
                        assert len(started.json()["result"]["tools"]) == 18
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(0.1)
        metadata = await raw.get(
            endpoint.removesuffix("/mcp")
            + "/.well-known/oauth-protected-resource/mcp"
        )
        assert metadata.json()["resource"] == RESOURCE
        assert len(metadata.json()["scopes_supported"]) == 4
        if startup_only:
            print("PASS: MCP startup, OAuth, tool discovery and Redis")
            return
        unauthorized = await raw.post(endpoint, json=body, headers=headers)
        assert unauthorized.status_code == 401
        assert (
            'error="invalid_token"' in unauthorized.headers["www-authenticate"]
        )
        assert "error_description=" in unauthorized.headers["www-authenticate"]
        assert (
            'scope="pneumatic:read"'
            in unauthorized.headers["www-authenticate"]
        )
        outage = await raw.post(
            endpoint,
            json=body,
            headers={**headers, "Authorization": f"Bearer {OUTAGE}"},
        )
        assert (
            outage.status_code == 503
            and "www-authenticate" not in outage.headers
        )
        readonly_tools = await raw.post(
            endpoint,
            json=body,
            headers={**headers, "Authorization": f"Bearer {READ_ONLY}"},
        )
        assert readonly_tools.status_code == 200
        assert len(readonly_tools.json()["result"]["tools"]) == 18
        for token, status in (
            (DELEGATE_SERVICE_FAILURE, 503),
            (DELEGATE_REVOKED, 401),
        ):
            failure = await raw.post(
                endpoint,
                headers={**headers, "Authorization": f"Bearer {token}"},
                json={
                    **body,
                    "method": "tools/call",
                    "params": {
                        "name": "get_workflow",
                        "arguments": {"workflow_id": 1},
                    },
                },
            )
            assert failure.status_code == status
            assert ("www-authenticate" in failure.headers) == (status == 401)
            assert token not in failure.text
        step_up = await raw.post(
            endpoint,
            headers={**headers, "Authorization": f"Bearer {READ_ONLY}"},
            json={
                **body,
                "method": "tools/call",
                "params": {
                    "name": "run_workflow",
                    "arguments": {
                        "template_id": 1,
                    },
                },
            },
        )
        assert step_up.status_code == 403
        step_challenge = step_up.headers["www-authenticate"]
        assert 'error="insufficient_scope"' in step_challenge
        assert (
            'error_description="Additional permissions are '
            'required for this tool."' in step_challenge
        )
        assert step_up.json()["result"]["_meta"]["mcp/www_authenticate"] == [
            step_challenge
        ]
        revoked = await raw.post(
            endpoint,
            headers={**headers, "Authorization": f"Bearer {SOURCE}"},
            json={
                **body,
                "method": "tools/call",
                "params": {
                    "name": "get_workflow",
                    "arguments": {"workflow_id": 401},
                },
            },
        )
        assert revoked.status_code == 401
        revoked_challenge = revoked.headers["www-authenticate"]
        assert (
            'error="invalid_token"' in revoked_challenge
            and "error_description=" in revoked_challenge
        )
        assert revoked.json()["result"]["_meta"]["mcp/www_authenticate"] == [
            revoked_challenge
        ]

        async def call_task(
            task_id: int, output: dict[str, Any], token: str, key: str
        ) -> httpx.Response:
            return await raw.post(
                endpoint,
                headers={**headers, "Authorization": f"Bearer {token}"},
                json={
                    **body,
                    "method": "tools/call",
                    "params": {
                        "name": "complete_task",
                        "arguments": {
                            "task_id": task_id,
                            "output": output,
                        },
                    },
                },
            )

        for index, clear in enumerate((None, [], "")):
            key = f"file-clear-{index}"
            denied = await call_task(8, {"file-1": clear}, WRITE_ONLY, key)
            assert denied.status_code == 403, denied.text
            challenge = denied.headers["www-authenticate"]
            assert 'scope="pneumatic:write files:write"' in challenge
            assert (
                'error="insufficient_scope"' in challenge
                and "error_description=" in challenge
            )
            assert denied.json()["result"]["_meta"][
                "mcp/www_authenticate"
            ] == [challenge]
            assert denied.json()["result"]["structuredContent"]["error"][
                "required_scopes"
            ] == [
                "pneumatic:write",
                "files:write",
            ]
            accepted = await call_task(8, {"file-1": clear}, SOURCE, key)
            assert (
                accepted.status_code == 200
                and not accepted.json()["result"]["isError"]
            ), accepted.text
            plain = await call_task(
                9, {"text-1": clear}, WRITE_ONLY, f"plain-clear-{index}"
            )
            assert (
                plain.status_code == 200
                and not plain.json()["result"]["isError"]
            )
        for text in (
            "https://my.pneumatic.app/files/abcdefgh.pdf",
            "[Report](https://my.pneumatic.app/files/abcdefgh.pdf)",
        ):
            linked = await call_task(
                11,
                {"group": [{"text-1": text}]},
                SOURCE,
                "file-link-" + str(len(text)),
            )
            assert (
                linked.status_code == 200
                and not linked.json()["result"]["isError"]
            ), linked.text
        external = await call_task(
            12,
            {"text-1": "[report](https://example.org/files/report123.pdf)"},
            WRITE_ONLY,
            "external-file-link",
        )
        assert (
            external.status_code == 200
            and not external.json()["result"]["isError"]
        )
        forbidden = await call_task(13, {}, WRITE_ONLY, "normal-forbidden")
        assert (
            forbidden.json()["result"]["structuredContent"]["error"]["code"]
            == "forbidden"
        )
        assert (
            "www-authenticate" not in forbidden.headers
            and "_meta" not in forbidden.json()["result"]
        )
        for version in ("2025-11-25", "2026-07-28"):
            meta = {
                types.PROTOCOL_VERSION_META_KEY: version,
                types.CLIENT_CAPABILITIES_META_KEY: {},
            }
            listed = await raw.post(
                endpoint,
                headers={
                    **headers,
                    "MCP-Protocol-Version": version,
                    "MCP-Method": "tools/list",
                    "Authorization": f"Bearer {SOURCE}",
                },
                json={
                    **body,
                    "params": {"_meta": meta}
                    if version == "2026-07-28"
                    else {},
                },
            )
            assert listed.status_code == 200
            for tool in listed.json()["result"]["tools"]:
                assert (
                    tool["securitySchemes"] == tool["_meta"]["securitySchemes"]
                )
                assert tool["securitySchemes"][0]["type"] == "oauth2"
        for mode in ("legacy", "auto"):
            async with httpx2.AsyncClient(
                trust_env=False,
                headers={
                    "Host": HOST,
                    "Authorization": f"Bearer {SOURCE}",
                },
            ) as http:
                transport = streamable_http_client(endpoint, http_client=http)
                async with Client(
                    transport, mode=mode, read_timeout_seconds=5
                ) as client:
                    tools = await client.list_tools()
                    assert len(tools.tools) == 18
                    workflow = await client.call_tool(
                        name="get_workflow", arguments={"workflow_id": 1}
                    )
                    assert workflow.structured_content["data"]["id"] == 1
                    assert (
                        workflow.structured_content["data"][
                            "kickoff_fieldsets"
                        ][0]["fields"][0]["value"]
                        == "important"
                    )
                    completed = await client.call_tool(
                        name="complete_task",
                        arguments={
                            "task_id": 7,
                            "output": {
                                "group": [
                                    {
                                        "file-1": [
                                            {
                                                "upload_id": (
                                                    "018e0000-0000-"
                                                    "7000-8000-"
                                                    "000000000001"
                                                )
                                            }
                                        ]
                                    }
                                ]
                            },
                        },
                    )
                    assert not completed.is_error
                    started = await client.call_tool(
                        name="run_workflow",
                        arguments={
                            "template_id": 1,
                        },
                    )
                    assert not started.is_error
                    uncertain = await client.call_tool(
                        name="run_workflow",
                        arguments={
                            "template_id": 999,
                        },
                    )
                    assert uncertain.is_error
                    assert (
                        uncertain.structured_content["error"]["retryable"]
                        is False
                    )
                    assert SOURCE not in json.dumps(
                        uncertain.structured_content
                    )
                    attachment = await client.call_tool(
                        name="get_attachment", arguments={"attachment_id": 1}
                    )
                    assert (
                        attachment.structured_content["data"]["download"][
                            "expires_in"
                        ]
                        == 300
                    )
                    for attachment_id, file_id in LEGACY_FILES.items():
                        legacy = await client.call_tool(
                            name="get_attachment",
                            arguments={"attachment_id": attachment_id},
                        )
                        assert not legacy.is_error
                        assert (
                            legacy.structured_content["data"]["attachment"][
                                "file_id"
                            ]
                            == file_id
                        )
                        assert (
                            legacy.structured_content["data"]["file"][
                                "file_id"
                            ]
                            == file_id
                        )
                    error = await client.call_tool(
                        name="get_workflow", arguments={"workflow_id": 999}
                    )
                    assert error.is_error
                    assert (
                        error.structured_content["error"]["code"]
                        == "not_found"
                    )
                    assert SOURCE not in json.dumps(error.structured_content)
                    assert "source.invalid" not in json.dumps(
                        error.structured_content
                    )
        modern = {
            types.PROTOCOL_VERSION_META_KEY: "2026-07-28",
            types.CLIENT_CAPABILITIES_META_KEY: {},
        }
        discovery = await raw.post(
            endpoint,
            json={
                **body,
                "method": "server/discover",
                "params": {"_meta": modern},
            },
            headers={
                **headers,
                "Authorization": f"Bearer {SOURCE}",
                "MCP-Protocol-Version": "2026-07-28",
                "MCP-Method": "server/discover",
            },
        )
        assert discovery.status_code == 200
        assert "mcp-session-id" not in discovery.headers
        stats = (await raw.get("http://core:8080/stats")).json()
        assert stats["counts"]["GET /workflows/999"] == 2
        assert stats["counts"]["POST /templates/1/run"] == 2
        assert (
            stats["counts"]["POST /templates/999/run"] == 2
        )  # One attempt per logical write.
        assert (
            stats["counts"]["POST /v2/tasks/8/complete"] == 6
        )  # Denial then explicit scope-upgraded call.
        assert stats["counts"]["POST /v2/tasks/9/complete"] == 3
    print(
        "PASS: Docker SDK2.3 legacy+modern, discovery, 18 "
        "tools, delegated calls, "
        "legacy Unicode/space file tickets, structured scope step-up/clears, "
        "errors, no write retries, 401/403/503"
    )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--endpoint", default=ENDPOINT)
    parser.add_argument("--startup-only", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(endpoint=args.endpoint, startup_only=args.startup_only))
