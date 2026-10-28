import * as React from 'react';
import { useIntl, FormattedDate } from 'react-intl';

import { TokenListItem } from '../TokenListItem';
import type { IApiKeyListItemProps } from './types';

export function ApiKeyListItem({ apiKey, onRevoke }: IApiKeyListItemProps) {
  const { formatMessage } = useIntl();

  const handleRevoke = () => {
    onRevoke(apiKey.id);
  };

  return (
    <TokenListItem
      name={apiKey.name}
      tokenPrefix={apiKey.prefix}
      meta={
        apiKey.lastUsedAt
          ? formatMessage(
              { id: 'integrations.api-key-last-used' },
              { date: <FormattedDate value={new Date(apiKey.lastUsedAt)} /> },
            )
          : formatMessage({ id: 'integrations.api-key-never-used' })
      }
      data-testid={`api-key-${apiKey.id}`}
      action={{
        label: formatMessage({ id: 'integrations.api-key-revoke' }),
        onClick: handleRevoke,
        'data-testid': `revoke-${apiKey.id}`,
      }}
    />
  );
}
