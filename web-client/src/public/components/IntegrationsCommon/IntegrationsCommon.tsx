/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';

import { copyToClipboard } from '../../utils/helpers';
import { NotificationManager } from '../UI/Notifications';
import { Button } from '../UI/Buttons/Button';

import styles from './IntegrationsCommon.css';
import { EPageTitle } from '../../constants/defaultValues';
import { PageTitle } from '../PageTitle/PageTitle';

export interface IIntegrationsCommonProps {
  apiKey: string;
  isApiKeyLoading: boolean;
  loadApiKey(): void;
}

export function IntegrationsCommon({ apiKey, isApiKeyLoading, loadApiKey }: IIntegrationsCommonProps) {
  React.useEffect(() => {
    loadApiKey();
  }, []);

  const { formatMessage } = useIntl();
  const apiKeyValue = isApiKeyLoading ? formatMessage({ id: 'integrations.loading-api-key' }) : apiKey;

  const handleCopyKey = () => {
    if (!apiKey) {
      return;
    }

    copyToClipboard(apiKey);
    NotificationManager.success({ message: 'user.copied-to-clipboard' });
  };

  const supportEmail = formatMessage({ id: 'integrations.support-email' });

  return (
    <>
      <PageTitle titleId={EPageTitle.Integrations} />
      <p className={styles['description']}>{formatMessage({ id: 'integrations.description' })}</p>

      <div className={styles['api-key']}>
        <p className={styles['api-key__title']}>{formatMessage({ id: 'integrations.api-key-title' })}</p>
        <input className={styles['api-key__input']} type="text" value={apiKeyValue} readOnly />
        <Button
          className={styles['api-key__button']}
          type="button"
          onClick={handleCopyKey}
          size="sm"
          label={formatMessage({ id: 'integrations.copy-api-key' })}
        />
      </div>

      <p className={styles['hint']}>
        {formatMessage({ id: 'integrations.hint' })}
        <a className={styles['link']} href={`mailto:${supportEmail}`}>{supportEmail}</a>
      </p>
    </>
  );
}
