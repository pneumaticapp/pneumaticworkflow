import type { ETenantsSorting, ITenant } from '../../types/tenants';

export interface ITenantsStore {
  list: ITenant[];
  isLoading: boolean;
  count: number | null;
  sorting: ETenantsSorting;
}
