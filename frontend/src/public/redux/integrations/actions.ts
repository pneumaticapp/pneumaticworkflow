import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction } from '../../types/redux';
import { IApiKeyItem, IIntegrationDetailed, IIntegrationListItem } from '../../types/integrations';

export const enum EIntegrationsActions {
  LoadApiKeys = 'LOAD_API_KEYS',
  LoadApiKeysSuccess = 'LOAD_API_KEYS_SUCCESS',
  LoadApiKeysFailed = 'LOAD_API_KEYS_FAILED',
  CreateApiKey = 'CREATE_API_KEY',
  CreateApiKeySuccess = 'CREATE_API_KEY_SUCCESS',
  CreateApiKeyFailed = 'CREATE_API_KEY_FAILED',
  DeleteApiKey = 'DELETE_API_KEY',
  DeleteApiKeySuccess = 'DELETE_API_KEY_SUCCESS',
  DeleteApiKeyFailed = 'DELETE_API_KEY_FAILED',
  ClearNewlyCreatedKey = 'CLEAR_NEWLY_CREATED_KEY',
  LoadIntegrationsList = 'LOAD_INTEGRATIONS_LIST',
  LoadIntegrationsListSuccess = 'LOAD_INTEGRATIONS_LIST_SUCCESS',
  LoadIntegrationsListFailed = 'LOAD_INTEGRATIONS_LIST_FAILED',
  LoadIntegrationDetails = 'LOAD_INTEGRATIONS_DETAILS',
  LoadIntegrationDetailsSuccess = 'LOAD_INTEGRATIONS_DETAILS_SUCCESS',
  LoadIntegrationDetailsFailed = 'LOAD_INTEGRATIONS_DETAILS_FAILED',
}

// API Keys: Load
export type TLoadApiKeys = ITypedReduxAction<EIntegrationsActions.LoadApiKeys, void>;
export const loadApiKeys: (payload?: void) => TLoadApiKeys =
  actionGenerator<EIntegrationsActions.LoadApiKeys, void>(EIntegrationsActions.LoadApiKeys);

export type TLoadApiKeysSuccess = ITypedReduxAction<EIntegrationsActions.LoadApiKeysSuccess, IApiKeyItem[]>;
export const loadApiKeysSuccess: (payload: IApiKeyItem[]) => TLoadApiKeysSuccess =
  actionGenerator<EIntegrationsActions.LoadApiKeysSuccess, IApiKeyItem[]>(EIntegrationsActions.LoadApiKeysSuccess);

export type TLoadApiKeysFailed = ITypedReduxAction<EIntegrationsActions.LoadApiKeysFailed, void>;
export const loadApiKeysFailed: (payload?: void) => TLoadApiKeysFailed =
  actionGenerator<EIntegrationsActions.LoadApiKeysFailed, void>(EIntegrationsActions.LoadApiKeysFailed);

// API Keys: Create
export type TCreateApiKeyPayload = { name?: string };
export type TCreateApiKey = ITypedReduxAction<EIntegrationsActions.CreateApiKey, TCreateApiKeyPayload>;
export const createApiKey: (payload: TCreateApiKeyPayload) => TCreateApiKey =
  actionGenerator<EIntegrationsActions.CreateApiKey, TCreateApiKeyPayload>(EIntegrationsActions.CreateApiKey);

export type TCreateApiKeySuccessPayload = { apiKey: IApiKeyItem; rawKey: string };
export type TCreateApiKeySuccess = ITypedReduxAction<EIntegrationsActions.CreateApiKeySuccess, TCreateApiKeySuccessPayload>;
export const createApiKeySuccess: (payload: TCreateApiKeySuccessPayload) => TCreateApiKeySuccess =
  actionGenerator<EIntegrationsActions.CreateApiKeySuccess, TCreateApiKeySuccessPayload>(EIntegrationsActions.CreateApiKeySuccess);

export type TCreateApiKeyFailed = ITypedReduxAction<EIntegrationsActions.CreateApiKeyFailed, void>;
export const createApiKeyFailed: (payload?: void) => TCreateApiKeyFailed =
  actionGenerator<EIntegrationsActions.CreateApiKeyFailed, void>(EIntegrationsActions.CreateApiKeyFailed);

// API Keys: Delete
export type TDeleteApiKeyPayload = { id: number };
export type TDeleteApiKey = ITypedReduxAction<EIntegrationsActions.DeleteApiKey, TDeleteApiKeyPayload>;
export const deleteApiKey: (payload: TDeleteApiKeyPayload) => TDeleteApiKey =
  actionGenerator<EIntegrationsActions.DeleteApiKey, TDeleteApiKeyPayload>(EIntegrationsActions.DeleteApiKey);

export type TDeleteApiKeySuccess = ITypedReduxAction<EIntegrationsActions.DeleteApiKeySuccess, { id: number }>;
export const deleteApiKeySuccess: (payload: { id: number }) => TDeleteApiKeySuccess =
  actionGenerator<EIntegrationsActions.DeleteApiKeySuccess, { id: number }>(EIntegrationsActions.DeleteApiKeySuccess);

export type TDeleteApiKeyFailed = ITypedReduxAction<EIntegrationsActions.DeleteApiKeyFailed, void>;
export const deleteApiKeyFailed: (payload?: void) => TDeleteApiKeyFailed =
  actionGenerator<EIntegrationsActions.DeleteApiKeyFailed, void>(EIntegrationsActions.DeleteApiKeyFailed);

// API Keys: Clear newly created
export type TClearNewlyCreatedKey = ITypedReduxAction<EIntegrationsActions.ClearNewlyCreatedKey, void>;
export const clearNewlyCreatedKey: (payload?: void) => TClearNewlyCreatedKey =
  actionGenerator<EIntegrationsActions.ClearNewlyCreatedKey, void>(EIntegrationsActions.ClearNewlyCreatedKey);

// Integrations List
export type TLoadIntegrationsList = ITypedReduxAction<EIntegrationsActions.LoadIntegrationsList, void>;
export const loadIntegrationsList: (payload?: void) => TLoadIntegrationsList =
  actionGenerator<EIntegrationsActions.LoadIntegrationsList, void>(EIntegrationsActions.LoadIntegrationsList);

export type TLoadIntegrationsListSuccess = ITypedReduxAction<
EIntegrationsActions.LoadIntegrationsListSuccess,
IIntegrationListItem[]
>;
export const loadIntegrationsListSuccess: (payload: IIntegrationListItem[]) => TLoadIntegrationsListSuccess =
  actionGenerator<EIntegrationsActions.LoadIntegrationsListSuccess, IIntegrationListItem[]>
  (EIntegrationsActions.LoadIntegrationsListSuccess);

export type TLoadIntegrationsListFailed = ITypedReduxAction<EIntegrationsActions.LoadIntegrationsListFailed, void>;
export const loadIntegrationsListFailed: (payload?: void) => TLoadIntegrationsListFailed =
  actionGenerator<EIntegrationsActions.LoadIntegrationsListFailed, void>
  (EIntegrationsActions.LoadIntegrationsListFailed);

// Integration Details
export type TLoadIntegrationDetailsPayload = { id: number };
export type TLoadIntegrationDetails = ITypedReduxAction<
EIntegrationsActions.LoadIntegrationDetails,
TLoadIntegrationDetailsPayload
>;
export const loadIntegrationDetails: (payload: TLoadIntegrationDetailsPayload) => TLoadIntegrationDetails =
  actionGenerator<
  EIntegrationsActions.LoadIntegrationDetails,
  TLoadIntegrationDetailsPayload
  >(EIntegrationsActions.LoadIntegrationDetails);

export type TLoadIntegrationDetailsSuccess = ITypedReduxAction<
EIntegrationsActions.LoadIntegrationDetailsSuccess,
IIntegrationDetailed
>;
export const loadIntegrationDetailsSuccess: (payload: IIntegrationDetailed) => TLoadIntegrationDetailsSuccess =
  actionGenerator<EIntegrationsActions.LoadIntegrationDetailsSuccess, IIntegrationDetailed>
  (EIntegrationsActions.LoadIntegrationDetailsSuccess);

export type TLoadIntegrationDetailsFailed = ITypedReduxAction<EIntegrationsActions.LoadIntegrationDetailsFailed, void>;
export const loadIntegrationDetailsFailed: (payload?: void) => TLoadIntegrationDetailsFailed =
  actionGenerator<EIntegrationsActions.LoadIntegrationDetailsFailed, void>
  (EIntegrationsActions.LoadIntegrationDetailsFailed);

export type TIntegrationsActions = TLoadApiKeys
| TLoadApiKeysSuccess
| TLoadApiKeysFailed
| TCreateApiKey
| TCreateApiKeySuccess
| TCreateApiKeyFailed
| TDeleteApiKey
| TDeleteApiKeySuccess
| TDeleteApiKeyFailed
| TClearNewlyCreatedKey
| TLoadIntegrationsList
| TLoadIntegrationsListSuccess
| TLoadIntegrationsListFailed
| TLoadIntegrationDetails
| TLoadIntegrationDetailsSuccess
| TLoadIntegrationDetailsFailed;
