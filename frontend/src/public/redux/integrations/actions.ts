/* eslint-disable */
/* prettier-ignore */
import { actionGenerator } from '../../utils/redux';
import { ITypedReduxAction } from '../../types/redux';
import { IIntegrationDetailed, IIntegrationListItem } from '../../types/integrations';

export const enum EIntegrationsActions {
  LoadApiKey = 'LOAD_API_KEY',
  LoadApiKeySuccess = 'LOAD_API_KEY_SUCCESS',
  LoadApiKeyFailed = 'LOAD_API_KEY_FAILED',
  LoadIntegrationsList = 'LOAD_INTEGRATIONS_LIST',
  LoadIntegrationsListSuccess = 'LOAD_INTEGRATIONS_LIST_SUCCESS',
  LoadIntegrationsListFailed = 'LOAD_INTEGRATIONS_LIST_FAILED',
  LoadIntegrationDetails = 'LOAD_INTEGRATIONS_DETAILS',
  LoadIntegrationDetailsSuccess = 'LOAD_INTEGRATIONS_DETAILS_SUCCESS',
  LoadIntegrationDetailsFailed = 'LOAD_INTEGRATIONS_DETAILS_FAILED',
}

export type TLoadApiKey = ITypedReduxAction<EIntegrationsActions.LoadApiKey, void>;
export const loadApiKey: (payload?: void) => TLoadApiKey =
  actionGenerator<EIntegrationsActions.LoadApiKey, void>(EIntegrationsActions.LoadApiKey);

export type TLoadApiKeySuccess = ITypedReduxAction<EIntegrationsActions.LoadApiKeySuccess, string>;
export const loadApiKeySuccess: (payload: string) => TLoadApiKeySuccess =
  actionGenerator<EIntegrationsActions.LoadApiKeySuccess, string>(EIntegrationsActions.LoadApiKeySuccess);

export type TLoadApiKeyFailed = ITypedReduxAction<EIntegrationsActions.LoadApiKeyFailed, void>;
export const loadApiKeyFailed: (payload?: void) => TLoadApiKeyFailed =
  actionGenerator<EIntegrationsActions.LoadApiKeyFailed, void>(EIntegrationsActions.LoadApiKeyFailed);

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

export type TIntegrationsActions = TLoadApiKey
| TLoadApiKeySuccess
| TLoadApiKeyFailed
| TLoadIntegrationsList
| TLoadIntegrationsListSuccess
| TLoadIntegrationsListFailed
| TLoadIntegrationDetails
| TLoadIntegrationDetailsSuccess
| TLoadIntegrationDetailsFailed;
