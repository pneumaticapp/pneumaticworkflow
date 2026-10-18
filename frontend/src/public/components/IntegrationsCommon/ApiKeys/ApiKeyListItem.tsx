import * as React from 'react';
import { memo, useCallback } from 'react';
import { useIntl, FormattedDate } from 'react-intl';

import { Button } from '../../UI/Buttons/Button';
import type { IApiKeyListItemProps } from './types';

import styles from '../IntegrationsCommon.css';

const keyMask = '••••••••';

export const ApiKeyListItem = memo(({ apiKey, onRevoke }: IApiKeyListItemProps) => {
  const { formatMessage } = useIntl();

  const handleRevoke = useCallback(() => {
    onRevoke(apiKey.id);
  }, [apiKey.id, onRevoke]);

  return (
    <div className={styles['api-keys__item']} data-testid={`api-key-${apiKey.id}`}>
      <div className={styles['api-keys__item-info']}>
        <span className={styles['api-keys__item-name']}>{apiKey.name}</span>
        <span className={styles['api-keys__item-prefix']}>
          {apiKey.prefix}
          {keyMask}
        </span>
        <span className={styles['api-keys__item-meta']}>
          {apiKey.lastUsedAt
            ? formatMessage(
                { id: 'integrations.api-key-last-used' },
                { date: <FormattedDate value={new Date(apiKey.lastUsedAt)} /> },
              )
            : formatMessage({ id: 'integrations.api-key-never-used' })}
        </span>
      </div>
      <div className={styles['api-keys__item-actions']}>
        <Button
          type="button"
          onClick={handleRevoke}
          size="sm"
          buttonStyle="transparent-black"
          label={formatMessage({ id: 'integrations.api-key-revoke' })}
          data-testid={`revoke-${apiKey.id}`}
        />
      </div>
    </div>
  );
});
ApiKeyListItem.displayName = 'ApiKeyListItem';
