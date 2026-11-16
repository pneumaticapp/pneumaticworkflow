import React from 'react';
import { useIntl } from 'react-intl';

import { TokenListItem } from '../TokenListItem';
import type { IAIProviderListItemProps } from './types';

export function AIProviderListItem({ provider, onDelete }: IAIProviderListItemProps) {
  const { formatMessage } = useIntl();
  const isUsed = provider.usage.length > 0;
  const agentNames = provider.usage.map(({ name }) => name).join(', ');

  const handleDelete = () => {
    onDelete(provider.id);
  };

  return (
    <TokenListItem
      name={provider.name}
      details={provider.baseUrl}
      tokenPrefix={provider.apiKeyPrefix}
      meta={isUsed ? formatMessage({ id: 'ai-providers.usage' }, { agents: agentNames }) : undefined}
      data-testid={`ai-provider-${provider.id}`}
      action={{
        label: formatMessage({ id: 'ai-providers.delete' }),
        onClick: handleDelete,
        isDisabled: isUsed,
        tooltip: isUsed
          ? formatMessage({ id: 'ai-providers.delete-disabled-tooltip' }, { agents: agentNames })
          : undefined,
        'data-testid': `delete-ai-provider-${provider.id}`,
      }}
    />
  );
}
