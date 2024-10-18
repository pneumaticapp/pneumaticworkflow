/* eslint-disable */
/* prettier-ignore */
import produce from 'immer';
import { IGeneralStore } from '../../types/redux';
import { EGeneralActions, TGeneralActions } from './actions';

const INIT_STATE: IGeneralStore = {
  isLoaderVisible: false,
  fullscreenImage: {
    isOpen: false,
    url: '',
  },
};

export const reducer = (state = INIT_STATE, action: TGeneralActions): IGeneralStore => {
  switch (action.type) {
  case EGeneralActions.SetGeneralLoaderVisibility:
    return { ...state, isLoaderVisible: action.payload };
  case EGeneralActions.OpenFullscreenImage:
    return produce(state, draftState => {
      draftState.fullscreenImage.isOpen = true;
      draftState.fullscreenImage.url = action.payload.url;
    });
  case EGeneralActions.CloseFullscreenImage:
    return produce(state, draftState => {
      draftState.fullscreenImage.isOpen = false;
    });
  default: return { ...state };
  }
};
