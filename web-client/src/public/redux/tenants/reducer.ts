import { ITenantsStore } from '../../types/redux';
import { ETenantsSorting } from '../../types/tenants';
import { ETenantsActions, TTenantsActions } from './actions';

const INIT_STATE: ITenantsStore = {
  list: [],
  isLoading: false,
  count: 0,
  sorting: ETenantsSorting.NameAsc,
};

// eslint-disable-next-line @typescript-eslint/default-param-last
export const reducer = (state = INIT_STATE, action: TTenantsActions): ITenantsStore => {
  switch (action.type) {
    case ETenantsActions.CreateTenant:
      return { ...state, isLoading: true };
    case ETenantsActions.ChangeTenantName:
      return { ...state, isLoading: true };
    case ETenantsActions.DeleteTenant:
      return { ...state, isLoading: true };
    case ETenantsActions.UpdateTenants:
      return { ...state, isLoading: true };
    case ETenantsActions.LoadTenantsCountSuccess:
      return { ...state, count: action.payload };

    case ETenantsActions.LoadTenants:
      return { ...state, isLoading: true };
    case ETenantsActions.LoadTenantsSuccess:
      return { ...state, isLoading: false, list: action.payload };
    case ETenantsActions.LoadTenantsFailed:
      return { ...state, isLoading: false };
    case ETenantsActions.ChangeTenantsSorting:
      return { ...state, sorting: action.payload };
    default:
      return state;
  }
};
