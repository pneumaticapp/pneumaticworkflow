/* eslint-disable no-plusplus */
import { eventChannel } from 'redux-saga';
import { mapToCamelCase } from '../../utils/mappers';

const HEARTBEAT_PING_MESSAGE = 'PING';
const HEARTBEAT_PONG_MESSAGE = 'PONG';
const HEARTBEAT_INTERVAL_TIME = 10000;
const MAX_MISSED_HEARTBEATS = 3;

export function createWebSocketChannel(url: string) {
  let ws: WebSocket;
  let heartbeatInterval: NodeJS.Timeout | null = null;
  let missedHeartbeats = 0;

  return eventChannel((emit) => {
    function createWebSocket() {
      ws = new WebSocket(url);

      ws.onopen = () => {
        if (heartbeatInterval !== null) {
          return;
        }

        missedHeartbeats = 0;
        heartbeatInterval = setInterval(() => {
          try {
            missedHeartbeats++;
            if (missedHeartbeats >= MAX_MISSED_HEARTBEATS) {
              throw new Error('Too many missed heartbeats.');
            }

            ws.send(HEARTBEAT_PING_MESSAGE);
          } catch (error) {
            if (heartbeatInterval) {
              clearInterval(heartbeatInterval);
            }

            heartbeatInterval = null;
            console.warn(`Closing connection. Reason: ${error.message}`);
            ws.close();
          }
        }, HEARTBEAT_INTERVAL_TIME) as unknown as NodeJS.Timeout;
      };

      ws.onmessage = (message) => {
        if (message.data === HEARTBEAT_PONG_MESSAGE) {
          missedHeartbeats = 0;

          return;
        }

        const data = mapToCamelCase(JSON.parse(message.data));

        emit(data);
      };

      ws.onclose = createWebSocket;
    }

    createWebSocket();

    return () => {
      ws.close();
    };
  });
}
