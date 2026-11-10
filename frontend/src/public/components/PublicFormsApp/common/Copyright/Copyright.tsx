/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { BRAND } from '../../../../constants/branding';

import styles from './Copyright.css';

interface ICopyrightProps {
  className?: string;
}

export function Copyright({ className }: ICopyrightProps) {
  const { formatMessage } = useIntl();

  return (
    <p className={classnames(styles['copyright'], className)}>
      {formatMessage(
        { id: 'public-form.copyright' },
        {
          link: (
            <a className={styles['copyright__link']} href={BRAND.homePath} target="_blank" rel="noreferrer">
              {formatMessage({ id: 'public-form.pneumatic' })}
            </a>
          ),
        },
      )}
    </p>
  );
}
