/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { IIntegrationListItem } from '../../types/integrations';
import { Loader } from '../UI/Loader';
import { IntegrationCard } from './IntegrationCard';

import styles from './IntegrationsList.css';

export interface IIntegrationsListProps {
  integrations: IIntegrationListItem[];
  isLoading: boolean;
  loadIntegrationsList(): void;
}

export function IntegrationsList({ integrations, isLoading, loadIntegrationsList }: IIntegrationsListProps) {
  const { useEffect } = React;

  useEffect(() => {
    loadIntegrationsList();
  }, []);

  const renderList = () => {
    if (isLoading) {
      return <Loader isLoading={true} />;
    }

    return (
      <div className={styles['integraions-list']}>
        {integrations.map(integration => (
          <div key={integration.id} className={styles['integraion-card']}>
            <IntegrationCard {...integration} />
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={styles['container']}>
      {renderList()}
    </div>
  );
}
