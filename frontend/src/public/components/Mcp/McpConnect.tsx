import * as React from 'react';
import { useIntl } from 'react-intl';
import { approveMcp, connectMcp, getMcpConsent, mcpErrorMessage, navigateMcp } from '../../api/mcp';
import { IMcpConsent } from '../../types/mcp';
import { isMcpId } from '../../utils/safeRedirect';
import { Button } from '../UI/Buttons/Button/Button';
import styles from './Mcp.css';

export function McpConnect() {
  const { formatMessage } = useIntl();
  const ids = new URLSearchParams(window.location.search).getAll('request_id');
  const requestId = ids.length === 1 && isMcpId(ids[0]) ? ids[0] : '';
  const [context, setContext] = React.useState<IMcpConsent>();
  const [error, setError] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const controller = React.useRef<AbortController>();
  const submitting = React.useRef(false);

  React.useEffect(() => {
    const requestController = new AbortController();
    controller.current = requestController;
    submitting.current = false;
    setBusy(false);
    setContext(undefined);
    setError('');
    if (!requestId) setError('mcp.error.expired');
    else
      getMcpConsent(requestId, requestController.signal)
        .then((value) => {
          if (!requestController.signal.aborted) setContext(value);
        })
        .catch((reason) => {
          if (!requestController.signal.aborted) setError(mcpErrorMessage(reason));
        });
    return () => requestController.abort();
  }, [requestId]);

  const submit = React.useCallback(
    async (allow: boolean) => {
      const signal = controller.current?.signal;
      if (!context || submitting.current || !signal || signal.aborted) return;
      submitting.current = true;
      setBusy(true);
      setError('');
      try {
        const result = context.login_complete
          ? await approveMcp(requestId, context.csrf_token, allow)
          : await connectMcp(requestId, context.csrf_token);
        if (!signal.aborted) navigateMcp(result.redirect_url);
      } catch (reason) {
        if (!signal.aborted) {
          const message = mcpErrorMessage(reason);
          setError(message);
          if (message !== 'mcp.error.unavailable') setContext(undefined);
          submitting.current = false;
          setBusy(false);
        }
      }
    },
    [context, requestId],
  );
  const handleContinue = React.useCallback(() => {
    void submit(true);
  }, [submit]);
  const handleDeny = React.useCallback(() => {
    void submit(false);
  }, [submit]);

  return (
    <main className={styles['panel']}>
      <h1>{formatMessage({ id: 'mcp.connect.title' })}</h1>
      {error && <p role="alert">{formatMessage({ id: error })}</p>}
      {!context && !error && <p role="status">{formatMessage({ id: 'mcp.loading' })}</p>}
      {context && (
        <>
          <p>
            {formatMessage(
              { id: 'mcp.connect.description' },
              { app: context.client_name, account: context.account_name },
            )}
          </p>
          <ul>
            {context.scopes.map((scope) => (
              <li key={scope}>{formatMessage({ id: `mcp.scope.${scope}` })}</li>
            ))}
          </ul>
          <div className={styles['actions']}>
            <Button
              type="button"
              label={formatMessage({ id: context.login_complete ? 'mcp.connect.allow' : 'mcp.connect.continue' })}
              isLoading={busy}
              onClick={handleContinue}
            />
            {context.login_complete && (
              <Button
                type="button"
                buttonStyle="transparent-black"
                label={formatMessage({ id: 'mcp.connect.deny' })}
                disabled={busy}
                onClick={handleDeny}
              />
            )}
          </div>
        </>
      )}
    </main>
  );
}
