import * as React from 'react';
import { useIntl } from 'react-intl';

import { TopNavContainer } from '../../components/TopNav';
import { IntegrationsCommonContainer } from '../../components/IntegrationsCommon';
import { ERoutes } from '../../constants/routes';
import { ReturnLink } from '../../components/UI';

import styles from './IntegrationDetailsLayout.css';

interface IIntegrationDetailsLayoutProps {
  children: React.ReactNode;
}
export function IntegrationDetailsLayout({ children }: IIntegrationDetailsLayoutProps) {
  const { formatMessage } = useIntl();

  const renderLeftContent = () => {
    return (
      <ReturnLink
        label={formatMessage({ id: 'menu.integrations' })}
        route={ERoutes.Integrations}
      />
    );
  };

  return (
    <>
      <TopNavContainer leftContent={renderLeftContent()} />
      <main>
        <div className="container-fluid">
          <div className={styles['container']}>
            <div className={styles['common']}>
              <IntegrationsCommonContainer />
            </div>

            <div className={styles['content']}>
              {children}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
