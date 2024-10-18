import React, { useMemo } from 'react';

import { TopNavContainer } from '../../components/TopNav';
import { SelectMenu } from '../../components/UI';
import { ETenantsSorting } from '../../types/tenants';

export interface ITenantsLayoutProps {
  children: React.ReactNode;
  sorting: ETenantsSorting;
  changeSorting(sorting: ETenantsSorting): void;
}

export function TenantsLayout({ children, sorting, changeSorting }: ITenantsLayoutProps) {
  const sortingTitles = useMemo(() => Object.values(ETenantsSorting), []);

  const renderTenantsNavContent = () => {
    return <SelectMenu values={sortingTitles} activeValue={sorting} onChange={changeSorting} />;
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
