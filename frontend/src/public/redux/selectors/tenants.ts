import type { RootState } from '../store';

export const getTenantsSorting = (state: RootState) => state.tenants.sorting;
export const getTenantsCountStore = (state: RootState) => state.tenants.count;
