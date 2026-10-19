import * as React from 'react';
import { memo, useCallback } from 'react';
import { useIntl, FormattedDate } from 'react-intl';

import { Button } from '../../UI/Buttons/Button';
import { TokenListItem } from '../TokenList';
import type { IApiKeyListItemProps } from './types';

export const ApiKeyListItem = memo(({ apiKey, onRevoke }: IApiKeyListItemProps) => {
  const { formatMessage } = useIntl();

  const handleRevoke = useCallback(() => {
    onRevoke(apiKey.id);
  }, [apiKey.id, onRevoke]);

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
      action={
        <Button
          type="button"
          onClick={handleRevoke}
          size="sm"
          buttonStyle="transparent-black"
          label={formatMessage({ id: 'integrations.api-key-revoke' })}
          data-testid={`revoke-${apiKey.id}`}
        />
      }
    />
  );
});
ApiKeyListItem.displayName = 'ApiKeyListItem';
