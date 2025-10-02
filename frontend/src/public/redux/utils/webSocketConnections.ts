import { WebSocketWithRemoveFlag } from './createWebSocketChannel';

const connections: WebSocketWithRemoveFlag[] = [];

export function addConnection(ws: WebSocket) {
  connections.push(ws);
}

export function hasActiveConnections(): boolean {
  return connections.length > 0;
}

export function closeAllConnections(): Promise<void> {
  if (connections.length === 0) {
    return Promise.resolve();
  }

  const closePromises = connections.map((ws) => {
    ws.shouldRemove = true;
    return new Promise<void>((resolveSocket) => {
      const checkSocketState = () => {
        if (ws.readyState === WebSocket.CLOSED) {
          resolveSocket();
        } else {
          setTimeout(checkSocketState, 100);
        }
      };

      ws.addEventListener('close', () => checkSocketState(), { once: true });
      ws.close(1000, 'Client closing');
      checkSocketState();
    });
  });

  return Promise.all(closePromises)
    .then(() => {
      connections.length = 0;
    })
    .catch((error) => console.error(error));
}
