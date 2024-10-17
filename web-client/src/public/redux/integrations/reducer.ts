/* eslint-disable */
/* prettier-ignore */
import produce from 'immer';

import { EIntegrationsActions, TIntegrationsActions } from './actions';
import { IIntegrationsStore } from '../../types/redux';

const INIT_STATE: IIntegrationsStore = {
  apiKey: {
    isLoading: false,
    data: '',
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
  case EIntegrationsActions.LoadApiKey:
    return produce(state, draftState => {
      draftState.apiKey.isLoading = true;
    });
  case EIntegrationsActions.LoadApiKeySuccess:
    return produce(state, draftState => {
      draftState.apiKey.data = action.payload;
      draftState.apiKey.isLoading = false;
    });
  case EIntegrationsActions.LoadApiKeyFailed:
    return produce(state, draftState => {
      draftState.apiKey.isLoading = false;
    });
  case EIntegrationsActions.LoadIntegrationsList:
    return produce(state, draftState => {
      draftState.list.isLoading = true;
    });
  case EIntegrationsActions.LoadIntegrationsListSuccess:
    return produce(state, draftState => {
      draftState.list.data = action.payload;
      draftState.list.isLoading = false;
    });
  case EIntegrationsActions.LoadIntegrationsListFailed:
    return produce(state, draftState => {
      draftState.list.isLoading = false;
    });
  case EIntegrationsActions.LoadIntegrationDetails:
    return produce(state, draftState => {
      draftState.detailed.isLoading = true;
    });
  case EIntegrationsActions.LoadIntegrationDetailsSuccess:
    return produce(state, draftState => {
      draftState.detailed.data = action.payload;
      draftState.detailed.isLoading = false;
    });
  case EIntegrationsActions.LoadIntegrationDetailsFailed:
    return produce(state, draftState => {
      draftState.detailed.isLoading = false;
    });

  default: return state;
  }
};
