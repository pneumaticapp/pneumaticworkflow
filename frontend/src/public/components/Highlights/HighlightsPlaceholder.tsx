import React from 'react';
import { useIntl } from 'react-intl';

import { Placeholder } from '../UI';
import { HighlightsPlaceholderIcon } from './HighlightsPlaceholderIcon';
import { IHighlightsPlaceholderProps } from './types';

export function HighlightsPlaceholder({ hasChangedFilters }: IHighlightsPlaceholderProps) {
  const { formatMessage } = useIntl();

  if (hasChangedFilters) {
    return (
      <Placeholder
        mood="bad"
        Icon={HighlightsPlaceholderIcon}
        title={formatMessage({ id: 'workflow-highlights.placeholder-empty-search-title' })}
        description={formatMessage({ id: 'workflow-highlights.placeholder-empty-search-descrtiption' })}
      />
    );
  }

  return (
    <Placeholder
      mood="neutral"
      Icon={HighlightsPlaceholderIcon}
      title={formatMessage({ id: 'workflow-highlights.placeholder-empty-list-title' })}
      description={formatMessage({ id: 'workflow-highlights.placeholder-empty-list-descrtiption' })}
    />
  );
}
