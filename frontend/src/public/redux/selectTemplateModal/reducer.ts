import produce from 'immer';
import { ISelectTemplateModalStore } from '../../types/redux';
import { ITemplateListItem } from '../../types/template';

import { ESelectTemplateModalActions, TSelectTemplateModalActions } from './actions';

const INIT_STATE: ISelectTemplateModalStore = {
  isOpen: false,
  ancestorTaskId: null,
  isLoading: false,
  items: [] as ITemplateListItem[],
  templatesIdsFilter: [],
};

export const reducer = (state = INIT_STATE, action: TSelectTemplateModalActions): ISelectTemplateModalStore => {
  switch (action.type) {
    case ESelectTemplateModalActions.OpenModal: {
      return produce(state, (draftState) => {
        draftState.isOpen = true;
        draftState.ancestorTaskId = action.payload?.ancestorTaskId || null;
        draftState.templatesIdsFilter = action.payload?.templatesIdsFilter || [];
      });
    }
    case ESelectTemplateModalActions.CloseModal: {
      return produce(state, (draftState) => {
        draftState.isOpen = false;
        draftState.ancestorTaskId = null;
        draftState.templatesIdsFilter =  [];
      });
    }
    case ESelectTemplateModalActions.LoadSelectTemplateModalTemplates:
      return { ...state, isLoading: true };
    case ESelectTemplateModalActions.SetSelectTemplateModalTemplates:
      return { ...state, isLoading: false, items: action.payload };
    default: return { ...state };
  }
};
