import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction } from '../../types/redux';
import { ETenantsSorting, ITenant } from '../../types/tenants';

export const enum ETenantsActions {
  LoadTenants = 'LOAD_TENANTS',
  UpdateTenants = 'UPDATE_TENANTS',

  LoadTenantsCount = 'LOAD_TENANTS_COUNT',
  UpdateTenantsCount = 'UPDATE_TENANTS_COUNT',
  LoadTenantsCountSuccess = 'LOAD_TENANTS_COUNT_SUCCESS',
  LoadTenantsCountFailed = 'LOAD_TENANTS_COUNT_FAILED',

  LoadTenantsSuccess = 'LOAD_TENANTS_SUCCESS',
  LoadTenantsFailed = 'LOAD_TENANTS_FAILED',
  ChangeTenantsSorting = 'CHANGE_TENANTS_SORTING',

  CreateTenant = 'CREATE_TENANT',
  ChangeTenantName = 'CHANGE_TENANT_NAME',
  DeleteTenant = 'DELETE_TENANT',
}

export type TLoadTenantsCount = ITypedReduxAction<ETenantsActions.LoadTenantsCount, void>;
export const loadTenantsCount: (payload?: void) => TLoadTenantsCount = actionGenerator<
  ETenantsActions.LoadTenantsCount,
  void
>(ETenantsActions.LoadTenantsCount);

export type TUpdateTenantsCount = ITypedReduxAction<ETenantsActions.UpdateTenantsCount, void>;
export const updateTenantsCount: (payload?: void) => TUpdateTenantsCount = actionGenerator<
  ETenantsActions.UpdateTenantsCount,
  void
>(ETenantsActions.UpdateTenantsCount);

export type TLoadTenantsCountSuccess = ITypedReduxAction<ETenantsActions.LoadTenantsCountSuccess, number>;
export const loadTenantsCountSuccess: (payload: number) => TLoadTenantsCountSuccess = actionGenerator<
  ETenantsActions.LoadTenantsCountSuccess,
  number
>(ETenantsActions.LoadTenantsCountSuccess);

export type TLoadTenantsCountFailed = ITypedReduxAction<ETenantsActions.LoadTenantsCountFailed, void>;
export const loadTenantsCountFailed: (payload?: void) => TLoadTenantsCountFailed = actionGenerator<
  ETenantsActions.LoadTenantsCountFailed,
  void
>(ETenantsActions.LoadTenantsCountFailed);

export type TCreateTenant = ITypedReduxAction<ETenantsActions.CreateTenant, string>;
export const createTenant: (payload: string) => TCreateTenant = actionGenerator<ETenantsActions.CreateTenant, string>(
  ETenantsActions.CreateTenant,
);

export type TChangeTenantNamePayload = {
  id: number;
  name: string;
};

export type TChangeTenantName = ITypedReduxAction<ETenantsActions.ChangeTenantName, TChangeTenantNamePayload>;
export const changeTenantName: (payload: TChangeTenantNamePayload) => TChangeTenantName = actionGenerator<
  ETenantsActions.ChangeTenantName,
  TChangeTenantNamePayload
>(ETenantsActions.ChangeTenantName);

export type TDeleteTenant = ITypedReduxAction<ETenantsActions.DeleteTenant, number>;
export const deleteTenant: (payload: number) => TDeleteTenant = actionGenerator<ETenantsActions.DeleteTenant, number>(
  ETenantsActions.DeleteTenant,
);

export type TUpdateTenants = ITypedReduxAction<ETenantsActions.UpdateTenants, void>;
export const updateTenants: (payload?: void) => TUpdateTenants = actionGenerator<ETenantsActions.UpdateTenants, void>(
  ETenantsActions.UpdateTenants,
);

export type TLoadTenants = ITypedReduxAction<ETenantsActions.LoadTenants, void>;
export const loadTenants: (payload?: void) => TLoadTenants = actionGenerator<ETenantsActions.LoadTenants, void>(
  ETenantsActions.LoadTenants,
);

export type TLoadTenantsSuccess = ITypedReduxAction<ETenantsActions.LoadTenantsSuccess, ITenant[]>;
export const loadTenantsSuccess: (payload: ITenant[]) => TLoadTenantsSuccess = actionGenerator<
  ETenantsActions.LoadTenantsSuccess,
  ITenant[]
>(ETenantsActions.LoadTenantsSuccess);

export type TLoadTenantsFailed = ITypedReduxAction<ETenantsActions.LoadTenantsFailed, void>;
export const loadTenantsFailed: (payload?: void) => TLoadTenantsFailed = actionGenerator<
  ETenantsActions.LoadTenantsFailed,
  void
>(ETenantsActions.LoadTenantsFailed);

export type TChangeTenantsSorting = ITypedReduxAction<ETenantsActions.ChangeTenantsSorting, ETenantsSorting>;
export const changeTenantsSorting: (payload: ETenantsSorting) => TChangeTenantsSorting = actionGenerator<
  ETenantsActions.ChangeTenantsSorting,
  ETenantsSorting
>(ETenantsActions.ChangeTenantsSorting);

export type TTenantsActions =
  | TLoadTenantsCount
  | TUpdateTenantsCount
  | TLoadTenantsCountSuccess
  | TLoadTenantsCountFailed
  | TLoadTenants
  | TLoadTenantsSuccess
  | TLoadTenantsFailed
  | TChangeTenantsSorting
  | TUpdateTenants
  | TDeleteTenant
  | TChangeTenantName
  | TCreateTenant;
