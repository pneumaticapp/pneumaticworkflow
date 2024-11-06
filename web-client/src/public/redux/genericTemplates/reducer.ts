/* eslint-disable */
/* prettier-ignore */
import { EGenericTemplatesActions, TGenericTemplatesActions } from './actions';
import { IGenericTemplatesStore } from '../../types/redux';
import { toggleValueInArray } from '../../utils/helpers';

const INIT_STATE: IGenericTemplatesStore = {
  genericTemplates: [],
  selected: [],
  loading: false,
};

export const reducer = (state = INIT_STATE, action: TGenericTemplatesActions): IGenericTemplatesStore => {
  const { selected } = state;
  switch (action.type) {
  case EGenericTemplatesActions.Change:
    return {
      ...state,
      selected: toggleValueInArray(action.payload, selected),
    };
  case EGenericTemplatesActions.Set:
    return {
      ...state,
      loading: false,
      genericTemplates: action.payload,
    };
  case EGenericTemplatesActions.SetSelected:
    return {
      ...state,
      loading: false,
      selected: action.payload,
    };
  case EGenericTemplatesActions.Fetch:
    return {...state, loading: true};

  default: return { ...state };
  }
};
