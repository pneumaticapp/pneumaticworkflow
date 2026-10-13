"""Reproduce the MCP nginx routing and secret-log regression checks.

Run from any directory with Python 3.9+ and Docker access::

    python scripts/tests/test_mcp_nginx.py

The image nginx:1.25.4-alpine must already be cached locally. No packages or
images are downloaded. Each test uses a disposable, network-isolated container
with no published ports, a read-only filesystem and read-only nginx mounts.
All identifiers and OAuth codes are synthetic. No .env or application services
are used, and no host files are written.

Real Compose HTTP and Railway configurations are rendered in container tmpfs.
Test-only changes add separate frontend/file/backend responders, reduce the DNS
timeout and redirect Railway stdout/stderr logs to tmpfs for assertions. The
Compose includes, URI rewrites, location matching and log formats remain real.
This checks nginx behavior, not worker environments or application readiness.
"""

import base64
import json
import subprocess
import uuid
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "nginx:1.25.4-alpine"

STUBS = r"""
server {
    listen 127.0.0.2:8000;
    access_log off;
    error_log /dev/null crit;
    location = /mcp/uploads/ERROR_UPLOAD { return 444; }
    location = /ordinary-failure { return 444; }
    location / {
        return 200 "FRONTEND uri=$uri proto=$http_x_forwarded_proto\n";
    }
}
server {
    listen 127.0.0.3:8000;
    access_log off;
    error_log /dev/null crit;
    location = /mcp/download/ERROR_TICKET { return 444; }
    location = /mcp/files/ERROR_FILE { return 444; }
    location / {
        return 200 "FILES uri=$uri proto=$http_x_forwarded_proto\n";
    }
}
server {
    listen 127.0.0.4:8000;
    listen unix:/tmp/gunicorn/pneumatic-backend.sock;
    access_log off;
    error_log /dev/null crit;
    location = /oauth/mcp/login { return 444; }
    location = /oauth/mcp/header-probe {
        return 200 "$http_x_forwarded_for|$http_x_real_ip";
    }
    location / {
        return 200 "BACKEND uri=$uri proto=$http_x_forwarded_proto\n";
    }
}
"""

ROUTES = (
    (
        "ticket",
        "/files/mcp/download/ACCESS_TICKET",
        "FILES uri=/mcp/download/ACCESS_TICKET",
    ),
    (
        "encoded-ticket",
        "/files/%6dcp/down%6coad/ENCODED_TICKET",
        "FILES uri=/mcp/download/ENCODED_TICKET",
    ),
    (
        "files-path",
        "/files/mcp/files/ACCESS_FILE",
        "FILES uri=/mcp/files/ACCESS_FILE",
    ),
    (
        "upload",
        "/mcp/uploads/ACCESS_UPLOAD",
        "FRONTEND uri=/mcp/uploads/ACCESS_UPLOAD",
    ),
    (
        "encoded-upload",
        "/mcp/up%6coads/ENCODED_UPLOAD",
        "FRONTEND uri=/mcp/uploads/ENCODED_UPLOAD",
    ),
    ("connect", "/mcp/connect", "FRONTEND uri=/mcp/connect"),
    ("connections", "/mcp/connections", "FRONTEND uri=/mcp/connections"),
    ("ordinary-files", "/files/upload", "FILES uri=/upload"),
    ("oauth", "/oauth/mcp/authorize", "BACKEND uri=/oauth/mcp/authorize"),
    (
        "metadata",
        "/.well-known/oauth-protected-resource/mcp",
        "BACKEND uri=/.well-known/oauth-protected-resource/mcp",
    ),
)

FAILURES = (
    "/files/mcp/download/ERROR_TICKET",
    "/files/%6dcp/down%6coad/ERROR_TICKET",
    "/files/mcp/files/ERROR_FILE",
    "/mcp/uploads/ERROR_UPLOAD",
    "/mcp/up%6coads/ERROR_UPLOAD",
    "/oauth/mcp/login?code=ERROR_CODE&request_id=x",
    "/ordinary-failure",
)

SECRET_MARKERS = (
    "ACCESS_TICKET",
    "ENCODED_TICKET",
    "ACCESS_FILE",
    "ACCESS_UPLOAD",
    "ENCODED_UPLOAD",
    "ERROR_TICKET",
    "ERROR_FILE",
    "ERROR_UPLOAD",
    "ERROR_CODE",
)


def render_config(kind: Literal["compose", "railway"]) -> str:
    if kind == "compose":
        conf = (
            (ROOT / "nginx/templates/nginx.conf.template")
            .read_text(encoding="utf-8")
            .replace("${SERVER_ADDRESS}", "localhost")
        )
    else:
        conf = (ROOT / "nginx/railway/nginx.conf").read_text(encoding="utf-8")
        conf = conf.replace(
            "access_log /dev/stdout main;",
            "access_log /var/log/nginx/access.log main;",
        ).replace(
            "error_log /dev/stderr error;",
            "error_log /var/log/nginx/error.log error;",
        )
        values = {
            "PORT": "8080",
            "NAMESERVER": "127.0.0.1",
            "FRONTEND_HOST": "127.0.0.2:8000",
            "BACKEND_HOST": "127.0.0.4:8000",
            "FILE_SERVICE_HOST": "127.0.0.3:8000",
            "MCP_HOST": "missing-mcp.invalid:8000",
        }
        for name, value in values.items():
            conf = conf.replace("${" + name + "}", value)
    conf = conf.rsplit("}", 1)[0] + STUBS + "\n}\n"
    return conf.replace("http {", "http {\n    resolver_timeout 1s;", 1)


def render_checks(kind: Literal["compose", "railway"], config: str) -> bytes:
    encoded = base64.b64encode(config.encode("utf-8")).decode("ascii")
    port = "80" if kind == "compose" else "8080"
    lines = [
        "set -eu",
        f"printf '%s' '{encoded}' | base64 -d > /tmp/review.conf",
        "mkdir -p /tmp/gunicorn",
        "nginx -t -c /tmp/review.conf",
        "nginx -c /tmp/review.conf",
    ]
    for name, path, expected in ROUTES:
        lines.extend(
            (
                "response=$(wget -qO- --header='Host: localhost' "
                "--header='X-Forwarded-Proto: https' "
                f"'http://127.0.0.1:{port}{path}')",
                f"case \"$response\" in *'{expected}'*) ;; "
                f"*) printf 'ROUTE_FAIL {name}: %s\\n' \"$response\"; "
                "exit 1;; esac",
            )
        )
    lines.extend(
        (
            "response=$(wget -qO- --header='Host: localhost' "
            "--header='X-Forwarded-For: 198.51.100.99' "
            "--header='X-Real-IP: 198.51.100.88' "
            f"'http://127.0.0.1:{port}/oauth/mcp/header-probe')",
            "test \"$response\" = '198.51.100.99, 127.0.0.1|127.0.0.1'",
        )
    )
    for index, path in enumerate(FAILURES):
        lines.extend(
            (
                "wget -S -O- --header='Host: localhost' "
                f"'http://127.0.0.1:{port}{path}' "
                f">/tmp/failure-{index}.out 2>&1 || true",
                f"grep -Eq 'HTTP/1.1 502 ' /tmp/failure-{index}.out",
            )
        )
    lines.extend(
        (
            "wget -S -O- --header='Host: localhost' "
            f"'http://127.0.0.1:{port}/mcp' >/tmp/missing.out 2>&1 || true",
            "grep -q 'HTTP/1.1 503 ' /tmp/missing.out",
            "nginx -s quit -c /tmp/review.conf",
            "sleep 0.2",
            "printf '\\nREVIEW_LOG_START\\n'",
            "cat /var/log/nginx/*.log",
            "printf '\\nREVIEW_LOG_END\\n'",
        )
    )
    # Pass bytes to subprocess: text mode on Windows converts LF to CRLF,
    # which makes the Linux shell reject commands such as `set -eu`.
    return ("\n".join(lines) + "\n").encode("utf-8")


def check_nginx(kind: Literal["compose", "railway"]):
    name = "pneumatic-mcp-nginx-review-" + uuid.uuid4().hex
    command = [
        "docker",
        "run",
        "--rm",
        "--pull=never",
        "--name",
        name,
        "-i",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/run",
        "--tmpfs",
        "/var/cache/nginx",
        "--tmpfs",
        "/var/log/nginx",
        "--mount",
        f"type=bind,source={ROOT / 'nginx/includes'},"
        "target=/etc/nginx/includes,readonly",
        "--mount",
        f"type=bind,source={ROOT / 'nginx/www'},target=/var/www,readonly",
        "--add-host",
        "pneumatic-frontend:127.0.0.2",
        "--add-host",
        "pneumatic-file-service:127.0.0.3",
        "--entrypoint",
        "sh",
        IMAGE,
    ]
    try:
        result = subprocess.run(
            command,
            input=render_checks(kind=kind, config=render_config(kind=kind)),
            capture_output=True,
            timeout=45,
        )
    finally:
        # Remove only this invocation's explicitly named disposable container
        # if a timeout or interruption prevented --rm from cleaning it up.
        subprocess.run(
            ["docker", "rm", "--force", name],
            capture_output=True,
            timeout=15,
        )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    if result.returncode:
        raise AssertionError(f"{kind}: nginx/request checks failed\n{output}")
    logs = output.split("REVIEW_LOG_START\n", 1)[1].split("REVIEW_LOG_END", 1)[
        0
    ]
    leaks = [marker for marker in SECRET_MARKERS if marker in logs]
    if leaks:
        raise AssertionError(
            f"{kind}: synthetic markers leaked: {leaks}\n{logs}"
        )
    if 'request: "GET /ordinary-failure' not in logs:
        raise AssertionError(
            f"{kind}: ordinary error logging control missing\n{logs}"
        )
    for expected in ("/files/mcp/[redacted]", "/mcp/uploads/[redacted]"):
        if expected not in logs:
            raise AssertionError(
                f"{kind}: redaction output missing: {expected}\n{logs}"
            )
    print(
        json.dumps(
            {
                "config": kind,
                "routes_checked": len(ROUTES),
                "failures_checked": len(FAILURES),
                "oauth_proxy_headers_checked": True,
                "missing_mcp_status": 503,
                "leaked_markers": leaks,
                "ordinary_error_control_present": True,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    for config_kind in ("compose", "railway"):
        check_nginx(kind=config_kind)
    print("PASS: Compose and Railway MCP nginx regression checks.")
