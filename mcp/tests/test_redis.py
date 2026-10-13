import asyncio
from typing import Any

import httpx
import pytest
from conftest import TOKEN_A, TOKEN_B

from pneumatic_mcp.errors import CoreError
from pneumatic_mcp.limiter import RedisRateLimiter


@pytest.mark.parametrize(
    argnames="token,status",
    argvalues=[(TOKEN_A, 429), (TOKEN_B, 200)],
)
async def test_limiter__two_processes__shared_connection_budget(
    replicas: tuple[httpx.AsyncClient, list[str]],
    replica_rpc: Any,
    token: str,
    status: int,
):

    # arrange
    http, urls = replicas
    for index in range(60):
        response = await replica_rpc(
            http=http,
            url=urls[index % 2],
            method="tools/list" if index % 9 == 0 else "tools/call",
        )
        if response.status_code != 200:
            pytest.fail(f"Unexpected setup response: {response.text}")

    # act
    response = await replica_rpc(http=http, url=urls[1], token=token)

    # assert
    assert response.status_code == status
    if status == 429:
        assert response.headers["retry-after"] == "60"
    else:
        assert response.json()["result"]["isError"] is False


@pytest.mark.parametrize(
    argnames="token,status",
    argvalues=[
        ("shared-account-source-6-abcdefghijklmnop", 429),
        (TOKEN_B, 200),
    ],
)
async def test_limiter__two_processes__shared_account_budget(
    replicas: tuple[httpx.AsyncClient, list[str]],
    replica_rpc: Any,
    token: str,
    status: int,
):

    # arrange
    http, urls = replicas
    for connection in range(1, 6):
        source = f"shared-account-source-{connection}-abcdefghijklmnop"
        for offset in range(0, 60, 10):
            responses = await asyncio.gather(
                *[
                    replica_rpc(
                        http=http,
                        url=urls[(offset + index) % 2],
                        token=source,
                    )
                    for index in range(10)
                ]
            )
            if {response.status_code for response in responses} != {200}:
                pytest.fail(
                    "Unexpected response while charging account budget"
                )

    # act
    response = await replica_rpc(http=http, url=urls[0], token=token)

    # assert
    assert response.status_code == status
    if status == 429:
        assert response.headers["retry-after"] == "60"
    else:
        assert response.json()["result"]["isError"] is False


async def test_limiter__redis_outage__fail_closed():

    # arrange
    limiter = RedisRateLimiter(url="redis://127.0.0.1:1/15")
    try:
        # act
        with pytest.raises(CoreError) as ex:
            await limiter.acquire(connection_id="connection", account_id=1)

        # assert
        assert ex.value.code == "unavailable"
    finally:
        await limiter.close()
