import * as React from 'react';
import classnames from 'classnames';

import { IntlMessages } from '../../IntlMessages';

import { IFieldsetRulesetsBadgeProps } from './types';
import styles from './FieldsetRulesetsBadge.css';

export function FieldsetRulesetsBadge({ rulesets, count, className }: IFieldsetRulesetsBadgeProps) {
  const resolvedCount = count ?? rulesets?.length ?? 0;

  if (resolvedCount <= 0) {
    return null;
  }

  return (
    <span data-testid="rulesets-badge" className={classnames(styles['rulesets-badge'], className)}>
      <IntlMessages id="fieldsets.field-rulesets-badge" values={{ count: resolvedCount }} />
    </span>
  );
}
