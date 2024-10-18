/* eslint-disable jsx-a11y/control-has-associated-label */
import React from 'react';
import { useIntl } from 'react-intl';

import { SectionTitle } from '../../../UI/Typeography/SectionTitle/SectionTitle';
import { AppStoreButtonIcon, GooglePlayButtonIcon } from '../../../icons';

import styles from './AppMobileButtons.css';

export function AppMobileButtons() {
  const { formatMessage } = useIntl();

  return (
    <div className={styles['store']}>
      <SectionTitle className={styles['store__title']}>
        {formatMessage({ id: 'dashboard.app-mobile-buttons-group-title' }, { br: <br /> })}
      </SectionTitle>

      <div className={styles['store__item']}>
        <a
          className={styles['button']}
          target="_blank"
          href="https://apps.apple.com/app/pneumatic-workflow/id1618369634"
          rel="noreferrer"
        >
          <AppStoreButtonIcon />
        </a>
      </div>
      <div className={styles['store__item']}>
        <a
          className={styles['button']}
          target="_blank"
          href="https://play.google.com/store/apps/details?id=com.pneumatic.workflow"
          rel="noreferrer"
        >
          <GooglePlayButtonIcon />
        </a>
      </div>
    </div>
  );
}
