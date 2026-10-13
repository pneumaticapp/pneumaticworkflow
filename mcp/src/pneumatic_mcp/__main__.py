import logging

import uvicorn

from pneumatic_mcp.app import create_app
from pneumatic_mcp.settings import Settings


def main():
    settings = Settings()
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s %(message)s"
    )
    uvicorn.run(
        create_app(settings=settings),
        host="0.0.0.0",
        port=settings.port,
        access_log=False,
        log_level="info",
        # Keep the root handlers already protected by create_app's redaction
        # filter.
        log_config=None,
        limit_concurrency=settings.max_concurrency,
        timeout_keep_alive=5,
        timeout_graceful_shutdown=settings.call_timeout + 5,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
