import React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { SSOIcon } from '../icons';
import { Button, TButtonProps } from '../UI';

import styles from './styles.css';

export function SSOButton({ onClick, className, ...props }: TButtonProps) {
  const { formatMessage } = useIntl();

  return (
    <Button
      className={classnames(styles['button'], styles['is-sso'], className)}
      label={formatMessage({ id: 'team.modal-btn-connect-google' })}
      icon={SSOIcon}
      onClick={onClick}
      {...props}
    />
  );
}
