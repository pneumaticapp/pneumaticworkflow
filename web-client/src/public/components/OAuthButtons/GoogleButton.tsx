import React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { connectGoogle } from '../../utils/helpers';
import { GoogleIcon } from '../icons';
import { Button, TButtonProps } from '../UI';

import styles from './styles.css';

export function GoogleButton({ onClick = connectGoogle, className, ...props }: TButtonProps) {
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
