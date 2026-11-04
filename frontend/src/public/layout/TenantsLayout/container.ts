import { connect } from 'react-redux';

import type { IApplicationState } from '../../redux/store';
import { ITenantsLayoutProps, TenantsLayout } from './TenantsLayout';
import { changeTenantsSorting } from '../../redux/actions';

type TStoreProps = Pick<ITenantsLayoutProps, 'sorting'>;
type TDispatchProps = Pick<ITenantsLayoutProps, 'changeSorting'>;

const mapStateToProps = ({ tenants: { sorting } }: IApplicationState): TStoreProps => {
  return {
    sorting,
  };
};

const mapDispatchToProps: TDispatchProps = {
  changeSorting: changeTenantsSorting,
};

export const TemplatesLayoutContainer = connect(mapStateToProps, mapDispatchToProps)(TenantsLayout);
