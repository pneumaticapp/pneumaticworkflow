import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { TRulesetMessageInputProps } from './types';
import styles from '../FieldsetRulesets/FieldsetRulesets.css';

export const RulesetMessageInput = ({
  message,
  onChange,
  isReadOnly,
}: TRulesetMessageInputProps) => {
  const { formatMessage } = useIntl();
  const [isTouched, setIsTouched] = useState(false);

  useEffect(() => {
    setIsTouched(false);
  }, [message]);

  const isError = isTouched && (!message || !message.trim());

  return (
    <>
      <span className={styles['ruleset-card__label']}>
        {formatMessage({ id: 'fieldsets.ruleset-message' })}
      </span>
      <input
        type="text"
        className={classnames(styles['ruleset-message-input'], {
          [styles['ruleset-message-input_error']]: isError,
        })}
        value={message || ''}
        placeholder={formatMessage({ id: 'fieldsets.ruleset-message-placeholder' })}
        onChange={(event) => onChange(event.target.value)}
        onFocus={() => setIsTouched(false)}
        onBlur={() => setIsTouched(true)}
        disabled={isReadOnly}
      />
    </>
  );
};
