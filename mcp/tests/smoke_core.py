"""HTTP-only contract responder for the isolated Docker protocol smoke."""

import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import quote, unquote

RESOURCE = "https://my.pneumatic.app/mcp"
SOURCE = "source-oauth-docker-smoke-0123456789"
READ_ONLY = "source-oauth-readonly-smoke-0123456789"
WRITE_ONLY = "source-oauth-writeonly-smoke-0123456789"
OUTAGE = "source-oauth-core-outage-0123456789"
DELEGATE_SERVICE_FAILURE = "source-oauth-delegate-config-0123456789"
DELEGATE_REVOKED = "source-oauth-delegate-revoked-0123456789"
SERVICE_SECRET = os.environ["MCP_SERVICE_SECRET"]
GRANTS = {}
COUNTS = {}
LOCK = threading.Lock()
SCOPES = ["pneumatic:read", "pneumatic:write", "files:read", "files:write"]
LEGACY_FILES = {2: "NiihssB_Drawing (v2).odg", 3: "Схема процесса 日本語.odg"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args: Any):
        pass  # Requests may carry private tokens or URLs.

    def reply(self, status: int, body: dict[str, Any]):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(size) or b"{}")
        if self.path.startswith("/internal/mcp/"):
            if self.headers.get("X-MCP-Service-Secret") != SERVICE_SECRET:
                return self.reply(401, {"detail": "Invalid service client"})
            source = body.get("token")
            if source == OUTAGE:
                return self.reply(
                    503, {"detail": "private upstream diagnostics"}
                )
            if (
                source
                not in {
                    SOURCE,
                    READ_ONLY,
                    WRITE_ONLY,
                    DELEGATE_SERVICE_FAILURE,
                    DELEGATE_REVOKED,
                }
                or body.get("resource") != RESOURCE
            ):
                return self.reply(200, {"active": False})
            identity = {
                "user_id": 11,
                "account_id": 101,
                "connection_id": "docker-connection",
            }
            scopes = (
                SCOPES
                if source == SOURCE
                else ["pneumatic:write"]
                if source == WRITE_ONLY
                else ["pneumatic:read"]
            )
            if self.path == "/internal/mcp/introspect":
                return self.reply(
                    200,
                    {
                        "active": True,
                        **identity,
                        "client_id": "docker-client",
                        "scope": " ".join(scopes),
                        "aud": [RESOURCE],
                        "exp": int(time.time()) + 900,
                    },
                )
            if self.path != "/internal/mcp/delegate" or not set(
                body["scopes"]
            ) <= set(scopes):
                return self.reply(403, {"detail": "Invalid operation scope"})
            if source in {DELEGATE_SERVICE_FAILURE, DELEGATE_REVOKED}:
                return self.reply(
                    401,
                    {
                        "code": "service_auth_failed"
                        if source == DELEGATE_SERVICE_FAILURE
                        else "invalid_token",
                        "detail": f"private delegation failure {source}",
                    },
                )
            credential = "mcp-d_" + secrets.token_urlsafe(32)
            with LOCK:
                GRANTS[credential] = body.copy()
            return self.reply(
                200,
                {
                    "credential": credential,
                    "token_type": "Bearer",
                    "expires_in": 60,
                    "expires_at": int(time.time()) + 60,
                    "operation": body["tool"],
                    "scopes": body["scopes"],
                    **identity,
                    "audience": "pneumatic-files"
                    if body["path"].startswith("/mcp/files/")
                    else "pneumatic-backend",
                },
            )
        if not self.business_authorized("POST"):
            return
        if self.path.endswith("/download-ticket"):
            return self.reply(
                200,
                {
                    "download_url": "https://my.pneumatic.app/files/mcp/download/"
                    + "x" * 43,
                    "expires_at": "2099-01-01T00:00:00Z",
                    "expires_in": 300,
                },
            )
        required = {"pneumatic:write"}
        if self.path == "/v2/tasks/7/complete" or (
            self.path == "/v2/tasks/8/complete"
            and "file-1" in body.get("output", {})
        ):
            required.add("files:write")
        if "https://my.pneumatic.app/files/abcdefgh.pdf" in json.dumps(body):
            required.update({"files:read", "files:write"})
        if not required <= set(self.grant["scopes"]):
            return self.reply(
                403,
                {
                    "code": "insufficient_scope",
                    "required_scopes": [
                        scope for scope in SCOPES if scope in required
                    ],
                    "detail": f"private file authorization {SOURCE}",
                },
            )
        if self.path == "/v2/tasks/13/complete":
            return self.reply(
                403,
                {
                    "code": "permission_denied",
                    "detail": "Object rights denied",
                },
            )
        if self.path == "/templates/999/run":
            return self.reply(
                503, {"detail": f"private write failure {SOURCE}"}
            )
        return self.reply(200, {"id": 1, "name": "New workflow", "status": 1})

    def business_authorized(self, method: str):
        credential = self.headers.get("Authorization", "").removeprefix(
            "Bearer "
        )
        with LOCK:
            grant = GRANTS.get(credential)
            if (
                grant
                and grant["method"] == method
                and grant["path"] == self.path
            ):
                self.grant = grant
                COUNTS[method + " " + self.path] = (
                    COUNTS.get(method + " " + self.path, 0) + 1
                )
                return True
        self.reply(
            401, {"detail": "A route-bound delegated credential is required"}
        )
        return False

    def do_GET(self):
        if self.path == "/stats":
            with LOCK:
                return self.reply(200, {"counts": COUNTS.copy()})
        if not self.business_authorized("GET"):
            return
        if self.path == "/workflows/999":
            return self.reply(
                404,
                {"detail": f"private data {SOURCE} https://source.invalid/a"},
            )
        if self.path == "/workflows/401":
            return self.reply(
                401, {"detail": f"private token failure {SOURCE}"}
            )
        if self.path.startswith("/integrations/mcp/attachments/"):
            attachment_id = int(self.path.rsplit("/", 1)[-1])
            return self.reply(
                200,
                {
                    "id": attachment_id,
                    "file_id": LEGACY_FILES.get(attachment_id, "file-1"),
                },
            )
        if self.path.startswith("/mcp/files/"):
            file_id = unquote(
                self.path.removeprefix("/mcp/files/"), errors="strict"
            )
            assert quote(string=file_id, safe="") == self.path.removeprefix(
                "/mcp/files/"
            )
            assert file_id in {"file-1", *LEGACY_FILES.values()}
            return self.reply(
                200,
                {
                    "file_id": file_id,
                    "name": "note.txt",
                    "size": 5,
                    "content_type": "text/plain",
                },
            )
        return self.reply(
            200,
            {
                "id": 1,
                "name": "Workflow",
                "status": 1,
                "kickoff": {
                    "output": [],
                    "fieldsets": [
                        {
                            "api_name": "group",
                            "fields": [
                                {"api_name": "field", "value": "important"},
                            ],
                        }
                    ],
                },
            },
        )


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
