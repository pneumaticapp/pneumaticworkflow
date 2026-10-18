import * as React from 'react';
import { useCallback } from 'react';
import { useIntl } from 'react-intl';

import { Button } from '../../UI/Buttons/Button';
import { Tooltip } from '../../UI/Tooltip';
import type { IAIProviderListItemProps } from './types';

import styles from './AIProviders.css';

const keyMask = '••••••••';

export const AIProviderListItem = React.memo(({ provider, onDelete }: IAIProviderListItemProps) => {
  const { formatMessage } = useIntl();
  const isUsed = provider.usage.length > 0;
  const agentNames = provider.usage.map(({ name }) => name).join(', ');

  const handleDelete = useCallback(() => {
    onDelete(provider.id);
  }, [provider.id, onDelete]);

  return (
    <li className={styles['providers__item']} data-testid={`ai-provider-${provider.id}`}>
      <div className={styles['providers__item-info']}>
        <h3 className={styles['providers__item-name']}>{provider.name}</h3>
        <p className={styles['providers__item-url']}>{provider.baseUrl}</p>
        <p className={styles['providers__item-key']}>
          <code>
            {provider.apiKeyPrefix}
            {keyMask}
          </code>
        </p>
        {isUsed && (
          <p className={styles['providers__item-usage']} data-testid={`ai-provider-usage-${provider.id}`}>
            {formatMessage({ id: 'ai-providers.usage' }, { agents: agentNames })}
          </p>
        )}
      </div>
      <Tooltip
        containerClassName={styles['providers__item-actions']}
        disabled={!isUsed}
        content={formatMessage({ id: 'ai-providers.delete-disabled-tooltip' }, { agents: agentNames })}
      >
        <div data-testid={`delete-ai-provider-guard-${provider.id}`}>
          <Button
            type="button"
            className={styles['providers__delete-btn']}
            onClick={handleDelete}
            size="sm"
            buttonStyle="transparent-black"
            disabled={isUsed}
            label={formatMessage({ id: 'ai-providers.delete' })}
            data-testid={`delete-ai-provider-${provider.id}`}
          />
        </div>
      </Tooltip>
    </li>
  );
});

AIProviderListItem.displayName = 'AIProviderListItem';
