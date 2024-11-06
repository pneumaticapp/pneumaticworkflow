/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-line-length

import {
  ITypedReduxAction,
  IDashboardCounters,
  TDashboardBreakdownItem,
  EDashboardModes,
  IDashboardStore,
} from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { EDashboardTimeRange, IGettingStartedChecklist } from '../../types/dashboard';

export const enum EDashboardActions {
  SetIsLoaderVisible = 'SET_IS_DASHBOARD_LOADER_VISIBLE',
  LoadDashboardData = 'LOAD_DASBOARD_DATA',
  SetDashboardCounters = 'SET_DASHBOARD_COUNTERS',
  SetDashboardTimeRange = 'SET_DASHBOARD_TIME_RANGE',
  ResetDashboardData = 'RESET_DASHBOARD_DATA',
  LoadBreakdownItems = 'LOAD_BREAKDOWN_ITEMS',
  SetBreakdownItems = 'SET_BREAKDOWN_ITEMS',
  LoadBreakdownTasks = 'LOAD_BREAKDOWN_TASKS',
  SetBreakdownTask = 'SET_BREAKDOWN_TASK',
  SetDashboardMode = 'SET_DASHBOARD_MODE',
  PatchBreakdownItem = 'PATCH_DASHBOARD_BREAKDOWN_ITEM',
  SetSettingsManuallyChanged = 'SET_DASHBOARD_SETTINGS_MANUALLY_CHANGED',
  OpenRunWorkflowModal = 'OPEN_RUN_WORKFLOW_MODAL_DASHBOARD',
  OpenRunWorkflowModalSideMenu = 'OPEN_RUN_WORKFLOW_MODAL_SIDE_MENU',
  LoadChecklist = 'LOAD_GETTING_STARTED_CHECKLIST',
  LoadChecklistSuccess = 'LOAD_GETTING_STARTED_CHECKLIST_SUCCESS',
  LoadChecklistFailed = 'LOAD_GETTING_STARTED_CHECKLIST_FAILED',
}

export type TSetIsLoaderVisible = ITypedReduxAction<EDashboardActions.SetIsLoaderVisible, boolean>;
export const setIsDasboardLoaderVisible: (payload: boolean) => TSetIsLoaderVisible =
  actionGenerator<EDashboardActions.SetIsLoaderVisible, boolean>(EDashboardActions.SetIsLoaderVisible);

export type TSetDashboardMode = ITypedReduxAction<EDashboardActions.SetDashboardMode, EDashboardModes>;
export const setDashboardMode: (payload: EDashboardModes) => TSetDashboardMode =
  actionGenerator<EDashboardActions.SetDashboardMode, EDashboardModes>(EDashboardActions.SetDashboardMode);

export type TLoadDashboardData = ITypedReduxAction<EDashboardActions.LoadDashboardData, void>;
export const loadDashboardData: (payload?: void) => TLoadDashboardData =
  actionGenerator<EDashboardActions.LoadDashboardData, void>(EDashboardActions.LoadDashboardData);

export type TSetDashboardCounters = ITypedReduxAction<EDashboardActions.SetDashboardCounters, IDashboardCounters>;
export const setDashboardCounters: (payload: IDashboardCounters) => TSetDashboardCounters =
  actionGenerator<EDashboardActions.SetDashboardCounters, IDashboardCounters>(EDashboardActions.SetDashboardCounters);

export type TSetDashboardTimeRange = ITypedReduxAction<EDashboardActions.SetDashboardTimeRange, EDashboardTimeRange>;
export const setDashboardTimeRange: (payload: EDashboardTimeRange) => TSetDashboardTimeRange =
  actionGenerator<EDashboardActions.SetDashboardTimeRange, EDashboardTimeRange>
  (EDashboardActions.SetDashboardTimeRange);

export type TLoadBreakdownItems = ITypedReduxAction<
EDashboardActions.LoadBreakdownItems,
EDashboardModes
>;
export const loadBreakdownItems: (payload: EDashboardModes) => TLoadBreakdownItems =
  actionGenerator<EDashboardActions.LoadBreakdownItems, EDashboardModes>
  (EDashboardActions.LoadBreakdownItems);

export interface ILoadBreakdownTasksPayload {
  templateId: number;
}
export type TLoadBreakdownTasks = ITypedReduxAction<
EDashboardActions.LoadBreakdownTasks,
ILoadBreakdownTasksPayload
>;
export const loadBreakdownTasks: (payload: ILoadBreakdownTasksPayload) => TLoadBreakdownTasks =
  actionGenerator<EDashboardActions.LoadBreakdownTasks, ILoadBreakdownTasksPayload>
  (EDashboardActions.LoadBreakdownTasks);

export type TSetBreakdownItems = ITypedReduxAction<
EDashboardActions.SetBreakdownItems,
TDashboardBreakdownItem[]
>;
export const setBreakdownItems: (payload: TDashboardBreakdownItem[]) => TSetBreakdownItems =
  actionGenerator<EDashboardActions.SetBreakdownItems, TDashboardBreakdownItem[]>
  (EDashboardActions.SetBreakdownItems);

export type TResetDashboardData = ITypedReduxAction<EDashboardActions.ResetDashboardData, void>;
export const resetDashboardData: (payload?: void) => TResetDashboardData =
  actionGenerator<EDashboardActions.ResetDashboardData, void>(EDashboardActions.ResetDashboardData);

type TPatchBreakdownItemPayload = {
  templateId: number;
  changedFields: Partial<TDashboardBreakdownItem>;
};
export type TPatchBreakdownItem = ITypedReduxAction<EDashboardActions.PatchBreakdownItem, TPatchBreakdownItemPayload>;
export const patchBreakdownItem: (payload: TPatchBreakdownItemPayload) => TPatchBreakdownItem =
  actionGenerator<EDashboardActions.PatchBreakdownItem, TPatchBreakdownItemPayload>(EDashboardActions.PatchBreakdownItem);

export type TSetSettingsManuallyChanged = ITypedReduxAction<EDashboardActions.SetSettingsManuallyChanged, void>;
export const setDashboardSettingsManuallyChanged: (payload?: void) => TSetSettingsManuallyChanged =
  actionGenerator<EDashboardActions.SetSettingsManuallyChanged, void>(EDashboardActions.SetSettingsManuallyChanged);

export interface IOpenRunWorkflowSideMenuPayload {
  templateData: any;
  ancestorTaskId?: number;
}

export type TOpenRunWorkflowModalSideMenu = ITypedReduxAction<EDashboardActions.OpenRunWorkflowModalSideMenu, IOpenRunWorkflowSideMenuPayload>;

export const openRunWorkflowModalSideMenu: (payload: IOpenRunWorkflowSideMenuPayload) => TOpenRunWorkflowModalSideMenu =
  actionGenerator<EDashboardActions.OpenRunWorkflowModalSideMenu, IOpenRunWorkflowSideMenuPayload>(EDashboardActions.OpenRunWorkflowModalSideMenu);

export interface IOpenRunWorkflowPayload {
  templateId: number;
  ancestorTaskId?: number;
}

export type TOpenRunWorkflowModalByTemplateId = ITypedReduxAction<EDashboardActions.OpenRunWorkflowModal, IOpenRunWorkflowPayload>;

export const openRunWorkflowModalByTemplateId: (payload: IOpenRunWorkflowPayload) => TOpenRunWorkflowModalByTemplateId =
  actionGenerator<EDashboardActions.OpenRunWorkflowModal, IOpenRunWorkflowPayload>(EDashboardActions.OpenRunWorkflowModal);

export type TLoadGettingStartedChecklist = ITypedReduxAction<EDashboardActions.LoadChecklist, void>;
export const loadGettingStartedChecklist: (payload?: void) => TLoadGettingStartedChecklist =
actionGenerator<EDashboardActions.LoadChecklist, void>(EDashboardActions.LoadChecklist);

export type TLoadGettingStartedChecklistSuccess = ITypedReduxAction<EDashboardActions.LoadChecklistSuccess, IGettingStartedChecklist>;
export const loadGettingStartedChecklistSuccess: (payload: IGettingStartedChecklist) => TLoadGettingStartedChecklistSuccess =
actionGenerator<EDashboardActions.LoadChecklistSuccess, IGettingStartedChecklist>(EDashboardActions.LoadChecklistSuccess);

export type TLoadGettingStartedChecklistFailed = ITypedReduxAction<EDashboardActions.LoadChecklistFailed, void>;
export const loadGettingStartedChecklistFailed: (payload?: void) => TLoadGettingStartedChecklistFailed =
actionGenerator<EDashboardActions.LoadChecklistFailed, void>(EDashboardActions.LoadChecklistFailed);

interface IPersistPayload {
  dashboard: IDashboardStore;
}

export type TRehydrateDashboardMode = ITypedReduxAction<'persist/REHYDRATE', IPersistPayload>;

export type TDashboardActions =
  | TSetIsLoaderVisible
  | TLoadDashboardData
  | TSetDashboardCounters
  | TSetDashboardTimeRange
  | TResetDashboardData
  | TLoadBreakdownItems
  | TSetBreakdownItems
  | TSetDashboardMode
  | TPatchBreakdownItem
  | TSetSettingsManuallyChanged
  | TOpenRunWorkflowModalByTemplateId
  | TOpenRunWorkflowModalSideMenu
  | TRehydrateDashboardMode
  | TLoadGettingStartedChecklist
  | TLoadGettingStartedChecklistSuccess
  | TLoadGettingStartedChecklistFailed;
