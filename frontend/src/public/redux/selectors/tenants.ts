import { IApplicationState } from '../../types/redux';

export const getTenantsSorting = (state: IApplicationState) => state.tenants.sorting;
export const getTenantsCountStore = (state: IApplicationState) => state.tenants.count;
