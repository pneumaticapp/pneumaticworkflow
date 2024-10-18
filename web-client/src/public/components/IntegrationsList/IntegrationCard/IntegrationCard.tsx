/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { Link } from 'react-router-dom';

import { IIntegrationListItem } from '../../../types/integrations';

import { getTruncatedText } from '../../../utils/helpers';
import { ERoutes } from '../../../constants/routes';

import styles from './IntegrationCard.css';

type IIntegrationCardProps = IIntegrationListItem;

const MAX_DESCRIPTION_LENGTH = 200;

export function IntegrationCard({ id, name, logo, shortDescription }: IIntegrationCardProps) {
  const normalizedDecription = getTruncatedText(shortDescription, MAX_DESCRIPTION_LENGTH);

  const pathToDetailed = ERoutes.IntegrationsDetail.replace(':id', String(id));

  return (
    <Link to={pathToDetailed} className={styles['container']}>
      {logo && (
        <div className={styles['card-image-wrapper']}>
          <img className={styles['card-image']} src={logo} alt={name} />
        </div>
      )}

      {normalizedDecription && (
        <p className={styles['card-description']}>
          {normalizedDecription}
        </p>
      )}
    </Link>
  );
}
