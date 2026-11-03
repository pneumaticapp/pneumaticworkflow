import produce from 'immer';

import { EIntegrationsActions, TIntegrationsActions } from './actions';
import { IIntegrationsStore } from '../../types/redux';

const INIT_STATE: IIntegrationsStore = {
  apiKeys: {
    isLoading: false,
    data: [],
    newlyCreatedKey: null,
  },
  list: {
    isLoading: false,
    data: [],
  },
  detailed: {
    isLoading: false,
    data: null,
  },
};

export const reducer = (state = INIT_STATE, action: TIntegrationsActions): IIntegrationsStore => {
  switch (action.type) {
    case EIntegrationsActions.LoadApiKeys:
      return produce(state, (draftState) => {
        draftState.apiKeys.isLoading = true;
      });
    case EIntegrationsActions.LoadApiKeysSuccess:
      return produce(state, (draftState) => {
        draftState.apiKeys.data = action.payload;
        draftState.apiKeys.isLoading = false;
      });
    case EIntegrationsActions.LoadApiKeysFailed:
      return produce(state, (draftState) => {
        draftState.apiKeys.isLoading = false;
      });
    case EIntegrationsActions.CreateApiKeySuccess:
      return produce(state, (draftState) => {
        draftState.apiKeys.data.unshift(action.payload.apiKey);
        draftState.apiKeys.newlyCreatedKey = action.payload.rawKey;
      });
    case EIntegrationsActions.DeleteApiKeySuccess:
      return produce(state, (draftState) => {
        draftState.apiKeys.data = draftState.apiKeys.data.filter((key) => key.id !== action.payload.id);
      });
    case EIntegrationsActions.ClearNewlyCreatedKey:
      return produce(state, (draftState) => {
        draftState.apiKeys.newlyCreatedKey = null;
      });
    case EIntegrationsActions.LoadIntegrationsList:
      return produce(state, (draftState) => {
        draftState.list.isLoading = true;
      });
    case EIntegrationsActions.LoadIntegrationsListSuccess:
      return produce(state, (draftState) => {
        draftState.list.data = action.payload;
        draftState.list.isLoading = false;
      });
    case EIntegrationsActions.LoadIntegrationsListFailed:
      return produce(state, (draftState) => {
        draftState.list.isLoading = false;
      });
    case EIntegrationsActions.LoadIntegrationDetails:
      return produce(state, (draftState) => {
        draftState.detailed.isLoading = true;
      });
    case EIntegrationsActions.LoadIntegrationDetailsSuccess:
      return produce(state, (draftState) => {
        draftState.detailed.data = action.payload;
        draftState.detailed.isLoading = false;
      });
    case EIntegrationsActions.LoadIntegrationDetailsFailed:
      return produce(state, (draftState) => {
        draftState.detailed.isLoading = false;
      });

    default:
      return state;
  }
};
