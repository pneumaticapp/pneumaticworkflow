import * as React from 'react';
import { useCallback } from 'react';
import { useIntl } from 'react-intl';

import { Button } from '../../UI/Buttons/Button';
import { Tooltip } from '../../UI/Tooltip';
import { TokenListItem } from '../TokenList';
import type { IAIProviderListItemProps } from './types';

import styles from './AIProviders.css';

export const AIProviderListItem = React.memo(({ provider, onDelete }: IAIProviderListItemProps) => {
  const { formatMessage } = useIntl();
  const isUsed = provider.usage.length > 0;
  const agentNames = provider.usage.map(({ name }) => name).join(', ');

  const handleDelete = useCallback(() => {
    onDelete(provider.id);
  }, [provider.id, onDelete]);

  return (
    <TokenListItem
      name={provider.name}
      details={provider.baseUrl}
      tokenPrefix={provider.apiKeyPrefix}
      meta={isUsed ? formatMessage({ id: 'ai-providers.usage' }, { agents: agentNames }) : undefined}
      data-testid={`ai-provider-${provider.id}`}
      action={
        <Tooltip
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
      }
    />
  );
});

AIProviderListItem.displayName = 'AIProviderListItem';
