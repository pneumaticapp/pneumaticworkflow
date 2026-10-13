"""Child process used only by the real Redis replica tests."""

import sys

import httpx
import uvicorn
from conftest import SECRET, FakeCore

from pneumatic_mcp.app import create_app
from pneumatic_mcp.client import CoreClient
from pneumatic_mcp.limiter import RedisRateLimiter
from pneumatic_mcp.settings import Settings

if __name__ == "__main__":
    settings = Settings(
        enabled=True,
        service_secret=SECRET,
        allowed_hosts=["test-host"],
        backend_url="http://core.test/core-prefix/",
    )
    upstream = FakeCore(settings=settings)
    core = CoreClient(
        settings=settings, transport=httpx.MockTransport(upstream)
    )
    app = create_app(
        settings=settings,
        core=core,
        limiter=RedisRateLimiter(url=sys.argv[2], prefix=sys.argv[3]),
    )
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(sys.argv[1]),
        access_log=False,
        log_level="error",
    )
