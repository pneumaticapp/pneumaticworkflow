/* eslint-disable max-len */
// tslint:disable: max-line-length
import {
  ITemplatesList,
  ITemplatesSystemCategories,
  ITemplatesSystemList,
  ITemplatesSystemSelection,
  ITypedReduxAction,
} from '../../types/redux';
import { actionGenerator } from '../../utils/redux';
import { TTemplateIntegrationStatsApi } from '../../types/template';
import { ETemplatesSorting } from '../../types/workflow';
import { TTaskVariable } from '../../components/TemplateEdit/types';

export const enum ETemplatesActions {
  SetCurrentTemplatesSystemStatus = 'SET_CURRENT_TEMPLATES_SYSTEM_STATUS',
  LoadTemplatesSystem = 'LOAD_TEMPLATES_SYSTEM',
  ChangeTemplatesSystem = 'CHANGE_TEMPLATES_SYSTEM',
  ChangeTemplatesSystemSelectionSearch = 'CHANGE_TEMPLATES_SYSTEM_SELECTION_SEARCH',
  ChangeTemplatesSystemSelectionCategory = 'CHANGE_TEMPLATES_SYSTEM_SELECTION_CATEGORY',
  ChangeTemplatesSystemPaginationNext = 'CHANGE_TEMPLATES_SYSTEM_PAGINATION_NEXT',
  LoadTemplatesSystemFailed = 'LOAD_TEMPLATES_SYSTEM_FAILED',
  LoadTemplatesSystemCategories = 'LOAD_TEMPLATES_SYSTEM_CATEGORIES',
  ChangeTemplatesSystemCategories = 'CHANGE_TEMPLATES_SYSTEM_CATEGORIES',
  SetInvitedUsers = 'SET_INVITED_USERS',
  ResetTemplates = 'RESET_TEMPLATES',
  ChangeTemplatesList = 'CHANGE_WORKFLOW_TEMPLATES_LIST',
  ChangeTemplatesListSorting = 'CHANGE_WORKFLOW_TEMPLATES_LIST_SORTING',
  LoadTemplates = 'LOAD_TEMPLATES',
  LoadTemplatesFailed = 'LOAD_TEMPLATES_FAILED',
  LoadTemplateVariables = 'LOAD_TEMPLATE_VARIABLES',
  LoadTemplateVariablesSuccess = 'LOAD_TEMPLATE_VARIABLES_SUCCESS',
  LoadTemplateIntegrationsStats = 'LOAD_TEMPLATE_INTEGRATIONS_STATS',
  SetTemplateIntegrationsStats = 'SET_TEMPLATE_INTEGRATIONS_STATS',
}

export enum ETemplatesSystemStatus {
  WaitingForAction = 'waiting-for-action',
  Loading = 'loading',
  Searching = 'searching',
  NoTemplates = 'no-templates',
}

export type TSetCurrentTemplatesSystemStatus = ITypedReduxAction<
  ETemplatesActions.SetCurrentTemplatesSystemStatus,
  ETemplatesSystemStatus
>;
export const setCurrentTemplatesSystemStatus: (payload: ETemplatesSystemStatus) => TSetCurrentTemplatesSystemStatus =
  actionGenerator<ETemplatesActions.SetCurrentTemplatesSystemStatus, ETemplatesSystemStatus>(
    ETemplatesActions.SetCurrentTemplatesSystemStatus,
  );

export type TLoadTemplatesSystem = ITypedReduxAction<ETemplatesActions.LoadTemplatesSystem, void>;
export const loadTemplatesSystem: (payload: void) => TLoadTemplatesSystem = actionGenerator<
  ETemplatesActions.LoadTemplatesSystem,
  void
>(ETemplatesActions.LoadTemplatesSystem);

type TChangeTemplatesSystemPayload = Pick<ITemplatesSystemList, 'items'> & Pick<ITemplatesSystemSelection, 'count'>;
export type TChangeTemplatesSystem = ITypedReduxAction<
  ETemplatesActions.ChangeTemplatesSystem,
  TChangeTemplatesSystemPayload
>;
export const changeTemplatesSystem: (payload: TChangeTemplatesSystemPayload) => TChangeTemplatesSystem =
  actionGenerator<ETemplatesActions.ChangeTemplatesSystem, TChangeTemplatesSystemPayload>(
    ETemplatesActions.ChangeTemplatesSystem,
  );

export type TChangeTemplatesSystemSelectionSearch = ITypedReduxAction<
  ETemplatesActions.ChangeTemplatesSystemSelectionSearch,
  string
>;
export const changeTemplatesSystemSelectionSearch: (payload: string) => TChangeTemplatesSystemSelectionSearch =
  actionGenerator<ETemplatesActions.ChangeTemplatesSystemSelectionSearch, string>(
    ETemplatesActions.ChangeTemplatesSystemSelectionSearch,
  );

export type TChangeTemplatesSystemSelectionCategory = ITypedReduxAction<
  ETemplatesActions.ChangeTemplatesSystemSelectionCategory,
  number | null
>;
export const changeTemplatesSystemSelectionCategory: (
  payload: number | null,
) => TChangeTemplatesSystemSelectionCategory = actionGenerator<
  ETemplatesActions.ChangeTemplatesSystemSelectionCategory,
  number | null
>(ETemplatesActions.ChangeTemplatesSystemSelectionCategory);

export type TChangeTemplatesSystemPaginationNext = ITypedReduxAction<
  ETemplatesActions.ChangeTemplatesSystemPaginationNext,
  void
>;
export const changeTemplatesSystemPaginationNext: (payload: void) => TChangeTemplatesSystemPaginationNext =
  actionGenerator<ETemplatesActions.ChangeTemplatesSystemPaginationNext, void>(
    ETemplatesActions.ChangeTemplatesSystemPaginationNext,
  );

export type TLoadTemplatesSystemFailed = ITypedReduxAction<ETemplatesActions.LoadTemplatesSystemFailed, void>;
export const loadTemplatesSystemFailed: (payload: void) => TLoadTemplatesSystemFailed = actionGenerator<
  ETemplatesActions.LoadTemplatesSystemFailed,
  void
>(ETemplatesActions.LoadTemplatesSystemFailed);

export type TLoadTemplatesSystemCategories = ITypedReduxAction<ETemplatesActions.LoadTemplatesSystemCategories, void>;
export const loadTemplatesSystemCategories: (payload: void) => TLoadTemplatesSystemCategories = actionGenerator<
  ETemplatesActions.LoadTemplatesSystemCategories,
  void
>(ETemplatesActions.LoadTemplatesSystemCategories);

export type TChangeTemplatesSystemCategories = ITypedReduxAction<
  ETemplatesActions.ChangeTemplatesSystemCategories,
  ITemplatesSystemCategories[]
>;
export const changeTemplatesSystemCategories: (
  payload: ITemplatesSystemCategories[],
) => TChangeTemplatesSystemCategories = actionGenerator<
  ETemplatesActions.ChangeTemplatesSystemCategories,
  ITemplatesSystemCategories[]
>(ETemplatesActions.ChangeTemplatesSystemCategories);

export type TResetTemplates = ITypedReduxAction<ETemplatesActions.ResetTemplates, void>;
export const resetTemplates: (payload?: void) => TResetTemplates = actionGenerator<
  ETemplatesActions.ResetTemplates,
  void
>(ETemplatesActions.ResetTemplates);

export type TChangeTemplatesList = ITypedReduxAction<ETemplatesActions.ChangeTemplatesList, ITemplatesList>;
export const changeTemplatesList: (payload: ITemplatesList) => TChangeTemplatesList = actionGenerator<
  ETemplatesActions.ChangeTemplatesList,
  ITemplatesList
>(ETemplatesActions.ChangeTemplatesList);

export type TChangeTemplatesListSorting = ITypedReduxAction<
  ETemplatesActions.ChangeTemplatesListSorting,
  ETemplatesSorting
>;
export const changeTemplatesSorting: (payload: ETemplatesSorting) => TChangeTemplatesListSorting = actionGenerator<
  ETemplatesActions.ChangeTemplatesListSorting,
  ETemplatesSorting
>(ETemplatesActions.ChangeTemplatesListSorting);

export type TLoadTemplates = ITypedReduxAction<ETemplatesActions.LoadTemplates, number>;
export const loadTemplates: (payload: number) => TLoadTemplates = actionGenerator<
  ETemplatesActions.LoadTemplates,
  number
>(ETemplatesActions.LoadTemplates);

export type TLoadTemplatesFailed = ITypedReduxAction<ETemplatesActions.LoadTemplatesFailed, void>;
export const loadTemplatesFailed: (payload?: void) => TLoadTemplatesFailed = actionGenerator<
  ETemplatesActions.LoadTemplatesFailed,
  void
>(ETemplatesActions.LoadTemplatesFailed);

export type TLoadTemplateVariablesPayload = { templateId: number };
export type TLoadTemplateVariables = ITypedReduxAction<
  ETemplatesActions.LoadTemplateVariables,
  TLoadTemplateVariablesPayload
>;
export const loadTemplateVariables: (payload: TLoadTemplateVariablesPayload) => TLoadTemplateVariables =
  actionGenerator<ETemplatesActions.LoadTemplateVariables, TLoadTemplateVariablesPayload>(
    ETemplatesActions.LoadTemplateVariables,
  );

export type TLoadTemplateVariablesSuccessPayload = { templateId: number; variables: TTaskVariable[] };
export type TLoadTemplateVariablesSuccess = ITypedReduxAction<
  ETemplatesActions.LoadTemplateVariablesSuccess,
  TLoadTemplateVariablesSuccessPayload
>;
export const loadTemplateVariablesSuccess: (
  payload: TLoadTemplateVariablesSuccessPayload,
) => TLoadTemplateVariablesSuccess = actionGenerator<
  ETemplatesActions.LoadTemplateVariablesSuccess,
  TLoadTemplateVariablesSuccessPayload
>(ETemplatesActions.LoadTemplateVariablesSuccess);

export type TLoadStatsPayload = {
  templates: number[];
};
export type TLoadTemplateIntegrationsStats = ITypedReduxAction<
  ETemplatesActions.LoadTemplateIntegrationsStats,
  TLoadStatsPayload
>;
export const loadTemplateIntegrationsStats: (payload: TLoadStatsPayload) => TLoadTemplateIntegrationsStats =
  actionGenerator<ETemplatesActions.LoadTemplateIntegrationsStats, TLoadStatsPayload>(
    ETemplatesActions.LoadTemplateIntegrationsStats,
  );

export type TSetTemplateIntegrationsStats = ITypedReduxAction<
  ETemplatesActions.SetTemplateIntegrationsStats,
  TTemplateIntegrationStatsApi[]
>;
export const setTemplateIntegrationsStats: (payload: TTemplateIntegrationStatsApi[]) => TSetTemplateIntegrationsStats =
  actionGenerator<ETemplatesActions.SetTemplateIntegrationsStats, TTemplateIntegrationStatsApi[]>(
    ETemplatesActions.SetTemplateIntegrationsStats,
  );

export type TTemplatesActions =
  | TSetCurrentTemplatesSystemStatus
  | TChangeTemplatesList
  | TLoadTemplatesSystemCategories
  | TChangeTemplatesSystemCategories
  | TChangeTemplatesSystemSelectionSearch
  | TChangeTemplatesSystemSelectionCategory
  | TChangeTemplatesSystemPaginationNext
  | TChangeTemplatesSystem
  | TLoadTemplatesSystemFailed
  | TLoadTemplatesSystem
  | TResetTemplates
  | TChangeTemplatesListSorting
  | TLoadTemplates
  | TLoadTemplatesFailed
  | TLoadTemplateVariables
  | TLoadTemplateVariablesSuccess
  | TLoadTemplateIntegrationsStats
  | TSetTemplateIntegrationsStats;
