import * as React from 'react';
import { useIntl } from 'react-intl';
import { getMcpConnections, mcpErrorMessage, revokeMcpConnection } from '../../api/mcp';
import { IMcpConnection } from '../../types/mcp';
import { Button } from '../UI/Buttons/Button/Button';
import styles from './Mcp.css';

export function McpConnections() {
  const { formatMessage } = useIntl();
  const [items, setItems] = React.useState<IMcpConnection[]>();
  const [csrf, setCsrf] = React.useState('');
  const [error, setError] = React.useState('');
  const [busy, setBusy] = React.useState('');
  const [confirm, setConfirm] = React.useState('');
  const controller = React.useRef<AbortController>();
  const revoking = React.useRef(false);

  React.useEffect(() => {
    const requestController = new AbortController();
    controller.current = requestController;
    getMcpConnections(requestController.signal)
      .then((data) => {
        if (!requestController.signal.aborted) {
          setItems(data.results);
          setCsrf(data.csrf_token);
        }
      })
      .catch((reason) => {
        if (!requestController.signal.aborted) setError(mcpErrorMessage(reason));
      });
    return () => requestController.abort();
  }, []);

  const revoke = React.useCallback(
    async (id: string) => {
      const signal = controller.current?.signal;
      if (revoking.current || !signal || signal.aborted) return;
      revoking.current = true;
      setBusy(id);
      setError('');
      try {
        await revokeMcpConnection(id, csrf);
        if (signal.aborted) return;
        const data = await getMcpConnections(signal);
        if (signal.aborted) return;
        setItems(data.results);
        setCsrf(data.csrf_token);
        setConfirm('');
      } catch (reason) {
        if (!signal.aborted) {
          const message = mcpErrorMessage(reason);
          setError(message);
          if (message !== 'mcp.error.unavailable') {
            setItems(undefined);
            setCsrf('');
            setConfirm('');
          }
        }
      } finally {
        if (!signal.aborted) {
          revoking.current = false;
          setBusy('');
        }
      }
    },
    [csrf],
  );
  const handleRevoke = React.useCallback(
    (event: React.MouseEvent) => {
      const id = event.currentTarget.getAttribute('data-connection-id');
      if (!id || revoking.current) return;
      if (confirm === id) void revoke(id);
      else setConfirm(id);
    },
    [confirm, revoke],
  );
  const handleCancel = React.useCallback(() => setConfirm(''), []);
  const displayItems = React.useMemo(
    () =>
      items?.map((item) => ({
        ...item,
        scopeLabel: item.scopes.map((scope) => formatMessage({ id: `mcp.scope.${scope}` })).join(', '),
      })),
    [items, formatMessage],
  );

  return (
    <main className={styles['panel']}>
      <h1>{formatMessage({ id: 'mcp.connections.title' })}</h1>
      <p>{formatMessage({ id: 'mcp.connections.description' })}</p>
      {error && <p role="alert">{formatMessage({ id: error })}</p>}
      {!items && !error && <p role="status">{formatMessage({ id: 'mcp.loading' })}</p>}
      {items?.length === 0 && <p>{formatMessage({ id: 'mcp.connections.empty' })}</p>}
      <ul className={styles['list']}>
        {displayItems?.map((item) => (
          <li key={item.id} className={styles['item']}>
            <h2>{item.client_name}</h2>
            <p>{item.scopeLabel}</p>
            {item.revoked_at ? (
              <p role="status">{formatMessage({ id: 'mcp.connections.revoked' })}</p>
            ) : (
              <>
                {confirm === item.id && (
                  <p>{formatMessage({ id: 'mcp.connections.confirm' }, { app: item.client_name })}</p>
                )}
                <div className={styles['actions']}>
                  <Button
                    label={formatMessage({
                      id: confirm === item.id ? 'mcp.connections.confirm-revoke' : 'mcp.connections.revoke',
                    })}
                    disabled={Boolean(busy)}
                    data-connection-id={item.id}
                    onClick={handleRevoke}
                  />
                  {confirm === item.id && (
                    <Button
                      buttonStyle="transparent-black"
                      label={formatMessage({ id: 'mcp.cancel' })}
                      disabled={Boolean(busy)}
                      onClick={handleCancel}
                    />
                  )}
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}
