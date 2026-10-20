import React, { useMemo } from 'react';
import { useIntl } from 'react-intl';

import { TopNavContainer } from '../../components/TopNav';
import { DropdownList } from '../../components/UI';
import { getSortingSelectProps } from '../../utils/getSortingSelectProps';
import { ETenantsSorting } from '../../types/tenants';

export interface ITenantsLayoutProps {
  children: React.ReactNode;
  sorting: ETenantsSorting;
  changeSorting(sorting: ETenantsSorting): void;
}

export function TenantsLayout({ children, sorting, changeSorting }: ITenantsLayoutProps) {
  const { formatMessage } = useIntl();
  const sortingTitles = useMemo(() => Object.values(ETenantsSorting), []);

  const renderTenantsNavContent = () => {
    return (
      <DropdownList
        controlSize="sm"
        controlVariant="accent"
        {...getSortingSelectProps(sortingTitles, sorting, changeSorting, formatMessage)}
      />
    );
  };

  return (
    <>
      <TopNavContainer leftContent={renderTenantsNavContent()} />
      <main>
        <div className="container-fluid">{children}</div>
      </main>
    </>
  );
}
