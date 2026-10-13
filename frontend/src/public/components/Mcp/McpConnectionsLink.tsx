import * as React from 'react';
import { useIntl } from 'react-intl';
import { isMcpEnabled } from '../../api/mcp';
import { ERoutes } from '../../constants/routes';
import styles from './Mcp.css';

export function McpConnectionsLink() {
  const { formatMessage } = useIntl();
  if (!isMcpEnabled()) return null;
  return (
    <a className={styles['link']} href={ERoutes.McpConnections}>
      {formatMessage({ id: 'mcp.connections.title' })}
    </a>
  );
}
