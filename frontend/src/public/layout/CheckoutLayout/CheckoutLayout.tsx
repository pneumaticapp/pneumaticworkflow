import * as React from 'react';
import { useIntl } from 'react-intl';

import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';

import { ReturnLink } from '../../components/UI';

export interface ICheckoutLayoutProps {
  children: React.ReactNode;
}

export function CheckoutLayout({ children }: ICheckoutLayoutProps) {
  const { formatMessage } = useIntl();

  const renderCheckoutPageLeftContent = () => {
    return (
      <ReturnLink
        label={formatMessage({ id: 'checkout.choose-the-plan' })}
        route={ERoutes.Main}
      />
    );
  };

  return (
    <>
      <TopNavContainer leftContent={renderCheckoutPageLeftContent()} />
      <main>
        <div className="container-fluid">
          {children}
        </div>
      </main>
    </>
  );
}
