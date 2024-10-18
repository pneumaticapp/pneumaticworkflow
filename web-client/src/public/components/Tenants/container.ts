import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';
import { ITenantsProps, Tenants } from './Tenants';
import {
  loadTenants,
  changeTenantsSorting,
  loginPartnerSuperuser,
  createTenant,
  changeTenantName,
  deleteTenant,
} from '../../redux/actions';
import { withSyncedQueryString } from '../../HOCs/withSyncedQueryString';
import { ETenantsSorting } from '../../types/tenants';

type TStoreProps = Pick<ITenantsProps, 'isLoading' | 'tenants' | 'sorting'>;
type TDispatchProps = Pick<
  ITenantsProps,
  'loadTenants' | 'loginPartnerSuperuser' | 'createTenant' | 'changeTenantName' | 'deleteTenant'
>;

export function mapStateToProps({ tenants }: IApplicationState): TStoreProps {
  return {
    isLoading: tenants.isLoading,
    tenants: tenants.list,
    sorting: tenants.sorting,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  loadTenants,
  loginPartnerSuperuser,
  createTenant,
  changeTenantName,
  deleteTenant,
};

const SyncedTenants = withSyncedQueryString<TStoreProps>([
  {
    propName: 'sorting',
    queryParamName: 'sorting',
    defaultAction: changeTenantsSorting(ETenantsSorting.NameAsc),
    createAction: changeTenantsSorting,
    getQueryParamByProp: (value) => value,
  },
])(Tenants);

export const TenantsContainer = connect<TStoreProps, TDispatchProps>(
  mapStateToProps,
  mapDispatchToProps,
)(SyncedTenants);
