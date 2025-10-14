import contextlib
import json

from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
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

    async def notification(self, event):
        await self.send(
            text_data=json.dumps(
                event['notification'],
            ),
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data == self.HEARTBEAT_PING_MESSAGE:
            with contextlib.suppress(ConnectionClosedError):
                await self.send(text_data=self.HEARTBEAT_PONG_MESSAGE)
        else:
            await super().receive(text_data=text_data, bytes_data=bytes_data)
