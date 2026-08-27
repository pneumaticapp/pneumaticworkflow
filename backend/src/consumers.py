import contextlib
import json
from typing import Any, Dict, Optional

from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from uvicorn.protocols.utils import ClientDisconnected
from websockets.exceptions import ConnectionClosedError

UserModel = get_user_model()


class PneumaticBaseConsumer(AsyncWebsocketConsumer):
    HEARTBEAT_PING_MESSAGE = 'PING'
    HEARTBEAT_PONG_MESSAGE = 'PONG'
    classname = None

    async def validate_connection(self):
        if self.scope['user'].is_anonymous:
            raise DenyConnection

    async def connect(self):
        await self.validate_connection()

        room_name = self.scope['user'].id
        room_group_name = f'{self.classname}_{room_name}'

        await self.channel_layer.group_add(
            room_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, code):
        if not self.scope['user'].is_anonymous:
            room_name = self.scope['user'].id
            room_group_name = f'{self.classname}_{room_name}'
            await self.channel_layer.group_discard(
                room_group_name,
                self.channel_name,
            )

    async def notification(self, event: Dict[str, Any]):
        await self._send_ignoring_disconnect(
            text_data=json.dumps(
                event['notification'],
            ),
        )

    async def receive(
        self,
        text_data: Optional[str] = None,
        bytes_data: Optional[bytes] = None,
    ):
        if text_data == self.HEARTBEAT_PING_MESSAGE:
            await self._send_ignoring_disconnect(
                text_data=self.HEARTBEAT_PONG_MESSAGE,
            )
        else:
            await super().receive(
                text_data=text_data,
                bytes_data=bytes_data,
            )

    async def _send_ignoring_disconnect(
        self,
        text_data: Optional[str] = None,
    ):
        with contextlib.suppress(ClientDisconnected, ConnectionClosedError):
            await self.send(text_data=text_data)
