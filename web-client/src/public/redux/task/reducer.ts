/* eslint-disable */
/* prettier-ignore */
import produce from 'immer';
import { IStoreTask } from '../../types/redux';
import { getTaskChecklist, getTaskChecklistItem } from '../../utils/tasks';
import { ETaskActions, ETaskStatus, TTaskActions } from './actions';

export const INIT_STATE: IStoreTask = {
  data: null,
  status: ETaskStatus.WaitingForAction,
};

export const reducer = (state = INIT_STATE, action: TTaskActions): IStoreTask => {
  switch (action.type) {
    case ETaskActions.SetCurrentTask:
      return { ...state, data: action.payload };
    case ETaskActions.PatchCurrentTask: {
      if (!state.data) return state;
      return { ...state, data: { ...state.data, ...action.payload } };
    }
    case ETaskActions.SetCurrentTaskStatus:
      return { ...state, status: action.payload };
    case ETaskActions.ChangeTaskPerformers:
      return produce(state, (draftState) => {
        if (!draftState.data) {
          return;
        }
        draftState.data.performers = action.payload;
      });
    case ETaskActions.ChangeChecklistItem: {
      const { listApiName, itemApiName, isChecked } = action.payload;

      return produce(state, (draftState) => {
        if (!draftState.data) {
          return;
        }

        const targetChecklist = getTaskChecklist(draftState.data, listApiName);
        const targetChecklistItem = getTaskChecklistItem(draftState.data, listApiName, itemApiName);
        if (!targetChecklist || !targetChecklistItem) {
          return;
        }

        targetChecklistItem.isSelected = isChecked;
        targetChecklist.checkedItems += isChecked ? 1 : -1;
      });
    }
    case ETaskActions.SetChecklistsHandling: {
      return produce(state, (draftState) => {
        if (!draftState.data) {
          return;
        }

        draftState.data.areChecklistsHandling = action.payload;
      });
    }

    default:
      return { ...state };
  }
};
