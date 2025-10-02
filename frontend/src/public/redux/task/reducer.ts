import produce from 'immer';
import { IStoreTask } from '../../types/redux';
import { getTaskChecklist, getTaskChecklistItem } from '../../utils/tasks';
import { ETaskActions, ETaskStatus, TTaskActions } from './actions';
import { EWorkflowsLogSorting, IWorkflowLogItem } from '../../types/workflow';

export const INIT_STATE: IStoreTask = {
  data: null,
  status: ETaskStatus.WaitingForAction,
  isWorkflowLoading: false,
  workflow: null,
  workflowLog: {
    items: [] as IWorkflowLogItem[],
    isCommentsShown: true,
    isOnlyAttachmentsShown: false,
    sorting: EWorkflowsLogSorting.New,
    isOpen: false,
    isLoading: false,
    workflowId: null,
  },
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
    case ETaskActions.ChangeTaskWorkflowLog:
      return produce(state, (draftState) => {
        draftState.workflowLog = { ...state.workflowLog, ...action.payload };
      });

    case ETaskActions.ChangeTaskWorkflow:
      return produce(state, (draftState) => {
        draftState.workflow = action.payload;
      });

    case ETaskActions.SetTaskWorkflowIsLoading:
      return produce(state, (draftState) => {
        draftState.isWorkflowLoading = action.payload;
      });

    case ETaskActions.ChangeTaskWorkflowLogViewSettings:
      return produce(state, (draftState) => {
        draftState.workflowLog.isCommentsShown = action.payload.comments;
        draftState.workflowLog.isOnlyAttachmentsShown = action.payload.isOnlyAttachmentsShown;
        draftState.workflowLog.sorting = action.payload.sorting;
      });

    case ETaskActions.UpdateTaskWorkflowLogItem:
      return produce(state, (draftState) => {
        const index = draftState.workflowLog.items.findIndex((item) => item.id === action.payload.id);

        if (index !== -1) {
          draftState.workflowLog.items[index] = action.payload;
        } else {
          draftState.workflowLog.items = [action.payload, ...draftState.workflowLog.items];
        }
      });

    default:
      return { ...state };
  }
};
