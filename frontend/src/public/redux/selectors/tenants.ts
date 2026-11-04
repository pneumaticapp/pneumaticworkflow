import type { IApplicationState } from '../store';

export const getTenantsSorting = (state: IApplicationState) => state.tenants.sorting;
export const getTenantsCountStore = (state: IApplicationState) => state.tenants.count;
