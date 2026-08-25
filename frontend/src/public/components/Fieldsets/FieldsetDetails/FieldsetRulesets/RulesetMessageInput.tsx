import * as React from 'react';
import { useIntl } from 'react-intl';

import styles from './FieldsetRulesets.css';

import { TRulesetMessageInputProps } from './types';

export const RulesetMessageInput = ({
  message,
  onChange,
  isReadOnly,
}: TRulesetMessageInputProps) => {
  const { formatMessage } = useIntl();

  return (
    <>
      <span className={styles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.ruleset-message' })}
      </span>
      <input
        type="text"
        className={styles['ruleset-message-input']}
        value={message || ''}
        placeholder={formatMessage({ id: 'fieldsets.ruleset-message-placeholder' })}
        onChange={(e) => onChange(e.target.value)}
        disabled={isReadOnly}
      />
    </>
  );
};
