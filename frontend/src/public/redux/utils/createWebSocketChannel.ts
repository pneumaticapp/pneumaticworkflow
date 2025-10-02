import { eventChannel } from 'redux-saga';
import { mapToCamelCase } from '../../utils/mappers';
import { addConnection } from './webSocketConnections';

export interface WebSocketWithRemoveFlag extends WebSocket {
  shouldRemove?: boolean;
}

const HEARTBEAT_PING_MESSAGE = 'PING';
const HEARTBEAT_PONG_MESSAGE = 'PONG';
const HEARTBEAT_INTERVAL_TIME = 10000;
const MAX_MISSED_HEARTBEATS = 3;

export function createWebSocketChannel(url: string) {
  let ws: WebSocketWithRemoveFlag;
  let heartbeatInterval: NodeJS.Timeout | null = null;
  let missedHeartbeats = 0;

  return eventChannel((emit) => {
    function createWebSocket() {
      ws = new WebSocket(url);
      addConnection(ws);

      ws.onopen = () => {
        if (heartbeatInterval !== null) {
          return;
        }

        missedHeartbeats = 0;
        heartbeatInterval = setInterval(() => {
          try {
            if (missedHeartbeats >= MAX_MISSED_HEARTBEATS) {
              throw new Error('Too many missed heartbeats.');
            }
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(HEARTBEAT_PING_MESSAGE);
              missedHeartbeats += 1;
            }
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
        missedHeartbeats = 0;
        if (message.data === HEARTBEAT_PONG_MESSAGE) {
          return;
        }

        const data = mapToCamelCase(JSON.parse(message.data));
        emit(data);
      };

      ws.onclose = () => {
        if (!ws.shouldRemove) {
          createWebSocket();
        }
      };
    }

    createWebSocket();

    return () => {
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
      }
      ws.close();
    };
  });
}
