import * as React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { IntlMessages } from '../../IntlMessages';

import styles from './TemplateValidationMessage.css';

interface ITemplateValidationMessageProps {
  messageId?: string;
  className?: string;
}

export function TemplateValidationMessage({ messageId, className }: ITemplateValidationMessageProps) {
  if (!messageId) {
    return null;
  }

  return (
    <p className={classnames(styles['validation-error'], className)} role="alert">
      <IntlMessages id={messageId} />
    </p>
  );
}

export function useLocalizedValidationMessage(messageId?: string) {
  const { formatMessage } = useIntl();

  return messageId ? formatMessage({ id: messageId }) : undefined;
}
