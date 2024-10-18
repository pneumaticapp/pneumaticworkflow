import * as React from 'react';
import { useIntl } from 'react-intl';

import { TopNavContainer } from '../../components/TopNav';
import { ReturnLink } from '../../components/UI';
import { ERoutes } from '../../constants/routes';

interface ITemplateLayoutProps {
  children: React.ReactNode;
}
export function TemplateLayout({ children }: ITemplateLayoutProps) {
  const { formatMessage } = useIntl();

  const renderLeftContent = () => {
    return (
      <ReturnLink
        label={formatMessage({ id: 'menu.templates' })}
        route={ERoutes.Templates}
      />
    );
  };

  return (
    <>
      <TopNavContainer leftContent={renderLeftContent()} />
      <main>
        <div className="container-fluid">
          {children}
        </div>
      </main>
    </>
  );
}
