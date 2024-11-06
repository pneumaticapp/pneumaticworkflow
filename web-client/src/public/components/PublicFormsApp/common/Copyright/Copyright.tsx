/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';
import * as classnames from 'classnames';

import { getPublicFormConfig } from '../../../../utils/getConfig';

import styles from './Copyright.css';

interface ICopyrightProps {
  className?: string;
}

export function Copyright({ className }: ICopyrightProps) {
  const { formatMessage } = useIntl();
  const { config: { mainPage } } = getPublicFormConfig();

  return (
    <p className={classnames(styles['copyright'], className)}>
      {formatMessage(
        { id: 'public-form.copyright' },
        {
          link: (
            <a
              className={styles['copyright__link']}
              href={mainPage}
              target="_blank"
            >
              {formatMessage({ id: 'public-form.pneumatic' })}
            </a>
          ),
        },
      )}
    </p>
  );
}
