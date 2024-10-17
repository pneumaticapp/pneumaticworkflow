import React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { MicrosoftIcon } from '../icons';
import { Button, TButtonProps } from '../UI';

import styles from './styles.css';

export function MicrosoftButton({ onClick, className, ...props }: TButtonProps) {
  const { formatMessage } = useIntl();

  return (
    <Button
      className={classnames(styles['button'], styles['is-microsoft'], className)}
      label={formatMessage({ id: 'team.modal-btn-connect-google' })}
      icon={MicrosoftIcon}
      onClick={onClick}
      {...props}
    />
  );
}
