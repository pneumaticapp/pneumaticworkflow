import React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { GoogleIcon } from '../icons';
import { Button, TButtonProps } from '../UI';

import styles from './styles.css';

export function GoogleButton({ onClick, className, ...props }: TButtonProps) {
  const { formatMessage } = useIntl();

  return (
    <Button
      className={classnames(styles['button'], styles['is-google'], className)}
      label={formatMessage({ id: 'team.modal-btn-connect-google' })}
      icon={GoogleIcon}
      onClick={onClick}
      {...props}
    />
  );
}
