import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from src.asgi import application
from src.authentication.tokens import PneumaticToken
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.asyncio
async def test_websocket__real_auth_token__connect_and_heartbeat():

    # arrange
    account = await database_sync_to_async(func=create_test_account)()
    owner = await database_sync_to_async(func=create_test_owner)(
        account=account,
    )
    token = await database_sync_to_async(func=PneumaticToken.create)(
        user=owner,
    )
    communicator = WebsocketCommunicator(
        application=application,
        path=f'/ws/events?auth_token={token}',
    )

    # act
    connected, _ = await communicator.connect()
    try:
        if connected:
            await communicator.send_to(text_data='PING')
            response = await communicator.receive_from()
        else:
            response = None
    finally:
        await communicator.disconnect()

    # assert
    assert connected is True
    assert response == 'PONG'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames='query',
    argvalues=('', '?auth_token=invalid'),
)
async def test_websocket__missing_or_invalid_token__denied(query: str):

    # arrange
    communicator = WebsocketCommunicator(
        application=application,
        path=f'/ws/events{query}',
    )

    # act
    connected, _ = await communicator.connect()
    await communicator.disconnect()

    # assert
    assert connected is False
