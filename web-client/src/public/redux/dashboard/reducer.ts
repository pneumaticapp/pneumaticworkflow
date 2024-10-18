/* eslint-disable */
/* prettier-ignore */
import produce from 'immer';

import { EDashboardActions, TDashboardActions } from './actions';
import { EDashboardTimeRange } from '../../types/dashboard';
import { IDashboardStore, EDashboardModes } from '../../types/redux';

import { REHYDRATE } from 'redux-persist/es/constants';

const INIT_STATE: IDashboardStore = {
  timeRange: EDashboardTimeRange.Today,
  counters: {
    completed: 0,
    inProgress: 0,
    overdue: 0,
    started: 0,
  },
  breakdownItems: [],
  mode: EDashboardModes.Workflows,
  isLoading: false,
  settingsChanged: false,
  checklist: {
    isLoading: false,
    isCompleted: false,
    checks: {
      templateCreated: false,
      inviteTeam: false,
      workflowStarted: false,
      templateOwnerChanged: false,
      conditionCreated: false,
      templatePublicated: false,
    },
  },
};

export const reducer = (state = INIT_STATE, action: TDashboardActions) => {
  switch (action.type) {
  case REHYDRATE:
    return { ...state, mode: action.payload?.dashboard?.mode || EDashboardModes.Workflows };
  case EDashboardActions.SetDashboardCounters:
    return { ...state, counters: action.payload };
  case EDashboardActions.SetDashboardTimeRange:
    return { ...state, timeRange: action.payload };
  case EDashboardActions.ResetDashboardData:
    return {
      ...INIT_STATE,
      timeRange: state.timeRange,
      mode: state.mode,
    };
  case EDashboardActions.SetBreakdownItems:
    return produce(state, draftState => {
      draftState.breakdownItems = action.payload;
    });
  case EDashboardActions.SetDashboardMode:
    return produce(state, draftState => {
      draftState.mode = action.payload;
      draftState.settingsChanged = false;
    });
  case EDashboardActions.SetIsLoaderVisible:
    return produce(state, draftState => {
      draftState.isLoading = action.payload;
    });
  case EDashboardActions.PatchBreakdownItem: {
    const { templateId, changedFields } = action.payload;
    const breakdownIndex = state.breakdownItems.findIndex(item => item.templateId === templateId);
    if (breakdownIndex === -1) {
      return state;
    }

    return produce(state, draftState => {
      const initialBreakdownFields = draftState.breakdownItems[breakdownIndex];
      draftState.breakdownItems[breakdownIndex] = { ...initialBreakdownFields, ...changedFields };
    });
  }
  case EDashboardActions.SetSettingsManuallyChanged: {
    return produce(state, draftState => {
      draftState.settingsChanged = true;
    });
  }
  case EDashboardActions.LoadChecklist: {
    return produce(state, draftState => {
      draftState.checklist.isLoading = true;
    });
  }
  case EDashboardActions.LoadChecklistSuccess: {
    return produce(state, draftState => {
      draftState.checklist.isLoading = false;
      draftState.checklist.checks = action.payload;
      draftState.checklist.isCompleted = Object.values(action.payload).every(value => value);
    });
  }
  case EDashboardActions.LoadChecklistFailed: {
    return produce(state, draftState => {
      draftState.checklist.isLoading = false;
    });
  }

  default: return { ...state };
  }
};
