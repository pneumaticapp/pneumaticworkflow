import * as React from 'react';
import { useIntl } from 'react-intl';

import { EPageTitle } from '../../constants/defaultValues';
import { PageTitle } from '../PageTitle/PageTitle';
import { AIProviders } from './AIProviders';
import { ApiKeys } from './ApiKeys';

import styles from './IntegrationsCommon.css';

export function IntegrationsCommon() {
  const { formatMessage } = useIntl();
  const supportEmail = formatMessage({ id: 'integrations.support-email' });

  return (
    <>
      <PageTitle titleId={EPageTitle.Integrations} />
      <p className={styles['description']}>{formatMessage({ id: 'integrations.description' })}</p>

      <ApiKeys />
      <AIProviders />

      <p className={styles['hint']}>
        {formatMessage({ id: 'integrations.hint' })}
        <a className={styles['link']} href={`mailto:${supportEmail}`}>
          {supportEmail}
        </a>
      </p>
    </>
  );
}
