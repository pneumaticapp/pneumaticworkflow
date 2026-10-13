import * as React from 'react';
import { useIntl } from 'react-intl';
import { RouteComponentProps } from 'react-router-dom';
import { MCP_BINARY_CONTENT_TYPE } from '../../utils/mcpFileMetadata';
import { Button } from '../UI/Buttons/Button/Button';
import { useMcpUpload } from './useMcpUpload';
import styles from './Mcp.css';

export function McpUpload({ match }: RouteComponentProps<{ session_id: string }>) {
  const { formatMessage } = useIntl();
  const { session, error, busy, sent, form, handleFileChange, handleRefresh } = useMcpUpload(match.params.session_id);

  const complete = session && ['ready', 'attached'].includes(session.status);
  const pending = sent || session?.status === 'importing';
  return (
    <main className={styles['panel']}>
      <h1>{formatMessage({ id: 'mcp.upload.title' })}</h1>
      {error && <p role="alert">{formatMessage({ id: error })}</p>}
      {!session && !error && <p role="status">{formatMessage({ id: 'mcp.loading' })}</p>}
      {complete && <p role="status">{formatMessage({ id: 'mcp.upload.complete' })}</p>}
      {session && !complete && (
        <>
          <p>{formatMessage({ id: 'mcp.upload.description' }, { name: session.filename, bytes: session.size })}</p>
          {pending ? (
            <>
              <p role="status">{formatMessage({ id: 'mcp.upload.verifying' })}</p>
              <Button label={formatMessage({ id: 'mcp.upload.refresh' })} disabled={busy} onClick={handleRefresh} />
            </>
          ) : (
            <form onSubmit={form.handleSubmit}>
              <label htmlFor="mcp-file">{formatMessage({ id: 'mcp.upload.file' })}</label>
              <input
                id="mcp-file"
                className={styles['file']}
                type="file"
                accept={
                  session.content_type === MCP_BINARY_CONTENT_TYPE ? undefined : session.content_type || undefined
                }
                disabled={busy}
                onChange={handleFileChange}
              />
              <Button
                type="submit"
                label={formatMessage({ id: 'mcp.upload.submit' })}
                disabled={!form.values.file || busy}
                isLoading={busy}
              />
            </form>
          )}
        </>
      )}
    </main>
  );
}
